"""
FinSight AI — Report / Investment Memo API route.

Generates a structured investment memo using the LangGraph memo pipeline.

Endpoints
---------
POST /api/report/{symbol}   → Structured JSON investment memo
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.report import InvestmentMemo, ReportResponse, SWOTAnalysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/report", tags=["report"])


@router.post("/{symbol}", response_model=ReportResponse)
async def generate_report(symbol: str):
    """Generate a structured investment memo for the given ticker.

    Runs the full LangGraph memo pipeline:
    check_cache → fetch_data → compute_metrics → retrieve_context →
    assemble_context → generate_memo → cache_result
    """
    from app.agents.graph import run_memo

    symbol = symbol.upper()

    try:
        result = await run_memo(symbol=symbol)

        memo_data = result.get("memo")
        step_log = result.get("step_log", [])
        errors = result.get("errors", [])

        if memo_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate investment memo. Check errors.",
            )

        # Parse the raw memo dict into the validated Pydantic model
        swot_raw = memo_data.get("swot", {})
        swot = SWOTAnalysis(
            strengths=swot_raw.get("strengths", []),
            weaknesses=swot_raw.get("weaknesses", []),
            opportunities=swot_raw.get("opportunities", []),
            threats=swot_raw.get("threats", []),
        )

        memo = InvestmentMemo(
            summary=memo_data.get("summary", ""),
            bull_case=memo_data.get("bull_case", []),
            bear_case=memo_data.get("bear_case", []),
            swot=swot,
            guidance=memo_data.get("guidance", ""),
            recommendation=memo_data.get("recommendation", "HOLD"),
            confidence=min(max(float(memo_data.get("confidence", 0.0)), 0.0), 1.0),
        )

        return ReportResponse(
            symbol=symbol,
            memo=memo,
            step_log=step_log,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Report generation failed for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))
