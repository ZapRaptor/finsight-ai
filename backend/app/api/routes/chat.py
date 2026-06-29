"""
FinSight AI — Chat API route.

Provides both streaming (SSE) and non-streaming chat endpoints.
The LangGraph agent orchestrates data fetching, metric computation,
context retrieval, and LLM generation.

Endpoints
---------
POST /api/chat          → Non-streaming JSON response
POST /api/chat/stream   → Server-Sent Events (SSE) streaming
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db import crud
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


# ──────────────────────────────────────────────────────────────────────
# POST /api/chat  —  Non-streaming
# ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run the full LangGraph chat pipeline and return the result."""
    from app.agents.graph import run_chat

    try:
        result = await run_chat(symbol=request.symbol, query=request.question)

        response_text = result.get("llm_response", "")
        sources = result.get("retrieved_chunks") or []
        step_log = result.get("step_log", [])
        errors = result.get("errors", [])

        # Persist the query to the audit log
        company = await crud.get_company_by_symbol(db, request.symbol)
        await crud.save_query(
            db,
            question=request.question,
            response=response_text,
            company_id=company.id if company else None,
            sources=sources,
        )

        return ChatResponse(
            symbol=request.symbol.upper(),
            question=request.question,
            response=response_text,
            sources=sources,
            step_log=step_log,
            errors=errors,
        )

    except Exception as e:
        logger.exception("Chat endpoint failed for %s", request.symbol)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────
# POST /api/chat/stream  —  SSE Streaming
# ──────────────────────────────────────────────────────────────────────

async def _stream_chat(symbol: str, question: str) -> AsyncIterator[str]:
    """Generator that yields SSE events during the chat pipeline.

    Event types:
    - step:     Agent pipeline progress updates
    - token:    Streamed LLM tokens
    - sources:  Retrieved context chunks
    - error:    Error messages
    - done:     Final signal
    """
    from app.services.cache import cache, RedisCache
    from app.services.fetcher import fetch_all_data
    from app.services.ratios import compute_all_metrics
    from app.services.embedder import embedder
    from app.services.llm import gemini_client
    from app.agents.nodes import assemble_context

    import hashlib

    symbol = symbol.upper()

    # Helper to format SSE
    def sse(event: str, data: str) -> str:
        return f"event: {event}\ndata: {data}\n\n"

    try:
        # Step 1: Check cache
        yield sse("step", "Checking cache...")
        query_hash = hashlib.md5(question.encode()).hexdigest()[:12]
        cache_key = RedisCache.make_key("chat", symbol, query_hash)
        cached = await cache.get(cache_key)

        if cached:
            yield sse("step", "Cache hit! Returning cached response.")
            response = cached.get("response", str(cached))
            # Stream the cached response token by token for UX consistency
            words = response.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i : i + 3])
                yield sse("token", chunk + " ")
            yield sse("done", json.dumps({"cached": True}))
            return

        # Step 2: Fetch data
        yield sse("step", f"Fetching financial data for {symbol}...")
        raw = await fetch_all_data(symbol)

        # Step 3: Compute metrics
        yield sse("step", "Computing financial ratios...")
        metrics_list = compute_all_metrics(
            income_statements=raw.get("income_statement", []),
            balance_sheets=raw.get("balance_sheet", []),
            market_cap=raw.get("info", {}).get("market_cap"),
        )
        metrics_dicts = [m.to_dict() for m in metrics_list]

        # Step 4: Retrieve context from Qdrant
        yield sse("step", "Searching document store...")
        collection_name = f"finsight_{symbol.lower()}"
        try:
            chunks = await embedder.semantic_search(question, collection_name, top_k=5)
        except Exception:
            chunks = []

        if chunks:
            yield sse("sources", json.dumps(chunks[:3], default=str))

        # Step 5: Assemble context
        yield sse("step", "Assembling analysis context...")
        state = {
            "symbol": symbol,
            "raw_financials": raw,
            "computed_metrics": metrics_dicts,
            "retrieved_chunks": chunks,
            "step_log": [],
        }
        ctx_result = await assemble_context(state)
        context = ctx_result.get("context", "")

        # Step 6: Stream LLM response
        yield sse("step", "Generating AI analysis...")
        full_response = []
        async for token in gemini_client.generate_stream(query=question, context=context):
            full_response.append(token)
            yield sse("token", token)

        # Step 7: Cache the result
        final_text = "".join(full_response)
        try:
            await cache.set(cache_key, {"response": final_text}, ttl=3600)
        except Exception:
            pass

        yield sse("done", json.dumps({"cached": False, "response_length": len(final_text)}))

    except Exception as e:
        logger.exception("Streaming chat failed for %s", symbol)
        yield sse("error", str(e))
        yield sse("done", json.dumps({"error": True}))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream the chat response as Server-Sent Events."""
    return StreamingResponse(
        _stream_chat(request.symbol, request.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
