"""
FinSight AI — LangGraph node functions.

Each function takes the current AgentState, performs work, and returns
a partial state update dict that gets merged back.

Node Flow
---------
check_cache → fetch_data → compute_metrics → retrieve_context →
assemble_context → generate_response / generate_memo → cache_result
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Node: check_cache
# ──────────────────────────────────────────────────────────────────────

async def check_cache(state: AgentState) -> dict[str, Any]:
    """Check Redis for a cached response for this exact query."""
    from app.services.cache import cache, RedisCache

    symbol = state["symbol"]
    query = state.get("query", "")
    step_log = list(state.get("step_log", []))
    step_log.append("check_cache")

    # For memo mode, cache by symbol+mode; for chat, by symbol+query hash
    if state.get("mode") == "memo":
        cache_key = RedisCache.make_key("memo", symbol)
    else:
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
        cache_key = RedisCache.make_key("chat", symbol, query_hash)

    cached = await cache.get(cache_key)
    if cached:
        logger.info("Cache HIT for %s", cache_key)
        return {"cached_data": cached, "step_log": step_log}

    logger.info("Cache MISS for %s", cache_key)
    return {"cached_data": None, "step_log": step_log}


# ──────────────────────────────────────────────────────────────────────
# Node: fetch_data
# ──────────────────────────────────────────────────────────────────────

async def fetch_data(state: AgentState) -> dict[str, Any]:
    """Fetch all financial data from yfinance (cached at the fetcher level)."""
    from app.services.fetcher import fetch_all_data

    symbol = state["symbol"]
    step_log = list(state.get("step_log", []))
    errors = list(state.get("errors", []))
    step_log.append("fetch_data")

    try:
        raw = await fetch_all_data(symbol)
        logger.info("Fetched raw financials for %s", symbol)
        return {"raw_financials": raw, "step_log": step_log, "errors": errors}
    except Exception as e:
        logger.exception("Failed to fetch data for %s", symbol)
        errors.append(f"fetch_data: {str(e)}")
        return {"raw_financials": None, "step_log": step_log, "errors": errors}


# ──────────────────────────────────────────────────────────────────────
# Node: compute_metrics
# ──────────────────────────────────────────────────────────────────────

async def compute_metrics(state: AgentState) -> dict[str, Any]:
    """Run the ratio engine on raw financials."""
    from app.services.ratios import compute_all_metrics

    step_log = list(state.get("step_log", []))
    errors = list(state.get("errors", []))
    step_log.append("compute_metrics")

    raw = state.get("raw_financials")
    if not raw:
        errors.append("compute_metrics: no raw financials available")
        return {"computed_metrics": None, "step_log": step_log, "errors": errors}

    try:
        metrics = compute_all_metrics(
            income_statements=raw.get("income_statement", []),
            balance_sheets=raw.get("balance_sheet", []),
            market_cap=raw.get("info", {}).get("market_cap"),
        )
        metrics_dicts = [m.to_dict() for m in metrics]
        logger.info("Computed %d periods of metrics", len(metrics_dicts))
        return {"computed_metrics": metrics_dicts, "step_log": step_log, "errors": errors}
    except Exception as e:
        logger.exception("Failed to compute metrics")
        errors.append(f"compute_metrics: {str(e)}")
        return {"computed_metrics": None, "step_log": step_log, "errors": errors}


# ──────────────────────────────────────────────────────────────────────
# Node: retrieve_context
# ──────────────────────────────────────────────────────────────────────

async def retrieve_context(state: AgentState) -> dict[str, Any]:
    """Search Qdrant for relevant document chunks (if any exist)."""
    from app.services.embedder import embedder

    symbol = state["symbol"]
    query = state.get("query", "")
    step_log = list(state.get("step_log", []))
    step_log.append("retrieve_context")

    try:
        collection_name = f"finsight_{symbol.lower()}"
        chunks = await embedder.semantic_search(query, collection_name, top_k=5)
        logger.info("Retrieved %d chunks from Qdrant for %s", len(chunks), symbol)
        return {"retrieved_chunks": chunks, "step_log": step_log}
    except Exception as e:
        logger.warning("Qdrant retrieval failed (non-fatal): %s", e)
        return {"retrieved_chunks": [], "step_log": step_log}


# ──────────────────────────────────────────────────────────────────────
# Node: assemble_context
# ──────────────────────────────────────────────────────────────────────

async def assemble_context(state: AgentState) -> dict[str, Any]:
    """Build the final context string from all gathered data."""
    step_log = list(state.get("step_log", []))
    step_log.append("assemble_context")

    parts: list[str] = []

    # Company info
    raw = state.get("raw_financials") or {}
    info = raw.get("info", {})
    if info:
        parts.append(f"=== Company: {info.get('name', state['symbol'])} ({state['symbol']}) ===")
        parts.append(f"Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}")
        parts.append(f"Market Cap: ${(info.get('market_cap') or 0):,.0f}")
        parts.append(f"Current Price: ${info.get('current_price') or 'N/A'}")
        parts.append("")

    # Computed metrics
    metrics = state.get("computed_metrics") or []
    if metrics:
        parts.append("=== Fundamental Metrics (by period) ===")
        for m in metrics:
            period = m.get("period", "?")
            lines = [f"  Period: {period}"]
            for key in ["pe_ratio", "roe", "roa", "gross_margin", "operating_margin",
                        "net_margin", "debt_to_equity", "current_ratio", "revenue_growth"]:
                val = m.get(key)
                if val is not None:
                    if "margin" in key or key in ("roe", "roa", "revenue_growth"):
                        lines.append(f"    {key}: {val*100:.2f}%")
                    else:
                        lines.append(f"    {key}: {val:.4f}")
            parts.append("\n".join(lines))
        parts.append("")

    # Raw income statement highlights
    income_stmts = raw.get("income_statement", [])
    if income_stmts and len(income_stmts) > 0:
        latest = income_stmts[0].get("data", {})
        parts.append(f"=== Latest Income Statement ({income_stmts[0].get('period', '?')}) ===")
        for key in ["Total Revenue", "Gross Profit", "Operating Income", "Net Income",
                     "Research And Development", "EBITDA"]:
            val = latest.get(key)
            if val is not None:
                parts.append(f"  {key}: ${val:,.0f}")
        parts.append("")

    # Balance sheet highlights
    balance_stmts = raw.get("balance_sheet", [])
    if balance_stmts and len(balance_stmts) > 0:
        latest = balance_stmts[0].get("data", {})
        parts.append(f"=== Latest Balance Sheet ({balance_stmts[0].get('period', '?')}) ===")
        for key in ["Total Assets", "Total Debt", "Stockholders Equity",
                     "Current Assets", "Current Liabilities", "Cash And Cash Equivalents"]:
            val = latest.get(key)
            if val is not None:
                parts.append(f"  {key}: ${val:,.0f}")
        parts.append("")

    # Retrieved document chunks (from Qdrant)
    chunks = state.get("retrieved_chunks") or []
    if chunks:
        parts.append("=== Relevant Document Excerpts ===")
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            source = chunk.get("source", "unknown")
            parts.append(f"[Excerpt {i} — source: {source}]")
            parts.append(text[:2000])
            parts.append("")

    context = "\n".join(parts)
    logger.info("Assembled context: %d characters", len(context))
    return {"context": context, "step_log": step_log}


# ──────────────────────────────────────────────────────────────────────
# Node: generate_response
# ──────────────────────────────────────────────────────────────────────

async def generate_response(state: AgentState) -> dict[str, Any]:
    """Call Gemini to generate a text answer to the user's query."""
    from app.services.llm import gemini_client

    step_log = list(state.get("step_log", []))
    errors = list(state.get("errors", []))
    step_log.append("generate_response")

    context = state.get("context", "")
    query = state.get("query", "Provide a financial overview.")

    try:
        response = await gemini_client.generate(query=query, context=context)
        logger.info("Generated LLM response: %d chars", len(response))
        return {"llm_response": response, "step_log": step_log, "errors": errors}
    except Exception as e:
        logger.exception("LLM generation failed")
        errors.append(f"generate_response: {str(e)}")
        return {
            "llm_response": f"I encountered an error generating the analysis: {str(e)}",
            "step_log": step_log,
            "errors": errors,
        }


# ──────────────────────────────────────────────────────────────────────
# Node: generate_memo
# ──────────────────────────────────────────────────────────────────────

async def generate_memo(state: AgentState) -> dict[str, Any]:
    """Call Gemini to produce a structured investment memo."""
    from app.services.llm import gemini_client

    step_log = list(state.get("step_log", []))
    errors = list(state.get("errors", []))
    step_log.append("generate_memo")

    context = state.get("context", "")
    symbol = state["symbol"]

    try:
        memo = await gemini_client.generate_memo(context=context, symbol=symbol)
        logger.info("Generated investment memo for %s", symbol)
        return {"memo": memo, "step_log": step_log, "errors": errors}
    except Exception as e:
        logger.exception("Memo generation failed")
        errors.append(f"generate_memo: {str(e)}")
        return {"memo": None, "step_log": step_log, "errors": errors}


# ──────────────────────────────────────────────────────────────────────
# Node: cache_result
# ──────────────────────────────────────────────────────────────────────

async def cache_result(state: AgentState) -> dict[str, Any]:
    """Write the final output to Redis for future cache hits."""
    from app.services.cache import cache, RedisCache

    symbol = state["symbol"]
    query = state.get("query", "")
    step_log = list(state.get("step_log", []))
    step_log.append("cache_result")

    try:
        if state.get("mode") == "memo" and state.get("memo"):
            cache_key = RedisCache.make_key("memo", symbol)
            await cache.set(cache_key, state["memo"], ttl=3600)  # 1h for memos
        elif state.get("llm_response"):
            import hashlib
            query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
            cache_key = RedisCache.make_key("chat", symbol, query_hash)
            await cache.set(cache_key, {"response": state["llm_response"]}, ttl=3600)

        logger.info("Cached result for %s", symbol)
    except Exception as e:
        logger.warning("Failed to cache result: %s", e)

    return {"step_log": step_log}
