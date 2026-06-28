"""
FinSight AI — LangGraph agent state definition.

Defines the TypedDict that flows through every node in the graph.
Every node reads from and writes to this shared state object.
"""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed through the LangGraph execution graph.

    Attributes
    ----------
    symbol : str
        The ticker symbol being analyzed (e.g. "AAPL").
    query : str
        The user's question or request.
    mode : str
        Execution mode: "chat" for conversational Q&A, "memo" for report generation.

    cached_data : dict | None
        Data retrieved from the Redis cache (if cache hit).
    raw_financials : dict | None
        Raw financial data from yfinance (info, income, balance, cashflow).
    computed_metrics : list[dict] | None
        Computed fundamental ratios from the ratio engine.
    retrieved_chunks : list[dict] | None
        Relevant text chunks from Qdrant semantic search.

    context : str
        The assembled context string fed to the LLM.
    llm_response : str
        The LLM's generated text response.
    memo : dict | None
        Structured investment memo (JSON) from the memo generator.

    errors : list[str]
        Accumulated error messages from any node.
    step_log : list[str]
        Ordered log of which nodes executed (for traceability).
    """

    # ── Input ──────────────────────────────────────────────────────────
    symbol: str
    query: str
    mode: str  # "chat" | "memo"

    # ── Data pipeline ──────────────────────────────────────────────────
    cached_data: Optional[dict[str, Any]]
    raw_financials: Optional[dict[str, Any]]
    computed_metrics: Optional[list[dict[str, Any]]]
    retrieved_chunks: Optional[list[dict[str, Any]]]

    # ── LLM output ─────────────────────────────────────────────────────
    context: str
    llm_response: str
    memo: Optional[dict[str, Any]]

    # ── Observability ──────────────────────────────────────────────────
    errors: list[str]
    step_log: list[str]
