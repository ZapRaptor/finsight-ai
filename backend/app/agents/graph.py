"""
FinSight AI — LangGraph state machine definition.

Defines two execution graphs:
1. chat_graph  — For conversational Q&A (streaming-compatible).
2. memo_graph  — For structured investment memo generation.

Both share the same node functions but differ in their terminal node
(generate_response vs generate_memo).

Flow
----
START → check_cache →  [cache hit?]
                          ├─ YES → return cached (short-circuit)
                          └─ NO  → fetch_data → compute_metrics →
                                   retrieve_context → assemble_context →
                                   generate_response / generate_memo →
                                   cache_result → END
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    assemble_context,
    cache_result,
    check_cache,
    compute_metrics,
    fetch_data,
    generate_memo,
    generate_response,
    retrieve_context,
)
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Conditional edge: cache hit or miss?
# ──────────────────────────────────────────────────────────────────────

def route_after_cache(state: AgentState) -> Literal["use_cache", "fetch_data"]:
    """Decide whether to short-circuit with cached data or proceed to fetch."""
    if state.get("cached_data") is not None:
        return "use_cache"
    return "fetch_data"


# ──────────────────────────────────────────────────────────────────────
# Node: use_cache (extracts cached data into the right state fields)
# ──────────────────────────────────────────────────────────────────────

async def use_cache(state: AgentState) -> dict[str, Any]:
    """Unpack cached data into state fields."""
    cached = state.get("cached_data", {})
    step_log = list(state.get("step_log", []))
    step_log.append("use_cache")

    if state.get("mode") == "memo":
        return {"memo": cached, "step_log": step_log}
    else:
        response = cached.get("response", str(cached))
        return {"llm_response": response, "step_log": step_log}


# ──────────────────────────────────────────────────────────────────────
# Build the Chat Graph
# ──────────────────────────────────────────────────────────────────────

def build_chat_graph() -> StateGraph:
    """Construct the LangGraph for conversational financial Q&A."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("check_cache", check_cache)
    graph.add_node("use_cache", use_cache)
    graph.add_node("fetch_data", fetch_data)
    graph.add_node("compute_metrics", compute_metrics)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("generate_response", generate_response)
    graph.add_node("cache_result", cache_result)

    # Edges
    graph.add_edge(START, "check_cache")
    graph.add_conditional_edges(
        "check_cache",
        route_after_cache,
        {"use_cache": "use_cache", "fetch_data": "fetch_data"},
    )
    graph.add_edge("use_cache", END)
    graph.add_edge("fetch_data", "compute_metrics")
    graph.add_edge("compute_metrics", "retrieve_context")
    graph.add_edge("retrieve_context", "assemble_context")
    graph.add_edge("assemble_context", "generate_response")
    graph.add_edge("generate_response", "cache_result")
    graph.add_edge("cache_result", END)

    return graph


def build_memo_graph() -> StateGraph:
    """Construct the LangGraph for investment memo generation."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("check_cache", check_cache)
    graph.add_node("use_cache", use_cache)
    graph.add_node("fetch_data", fetch_data)
    graph.add_node("compute_metrics", compute_metrics)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("generate_memo", generate_memo)
    graph.add_node("cache_result", cache_result)

    # Edges
    graph.add_edge(START, "check_cache")
    graph.add_conditional_edges(
        "check_cache",
        route_after_cache,
        {"use_cache": "use_cache", "fetch_data": "fetch_data"},
    )
    graph.add_edge("use_cache", END)
    graph.add_edge("fetch_data", "compute_metrics")
    graph.add_edge("compute_metrics", "retrieve_context")
    graph.add_edge("retrieve_context", "assemble_context")
    graph.add_edge("assemble_context", "generate_memo")
    graph.add_edge("generate_memo", "cache_result")
    graph.add_edge("cache_result", END)

    return graph


# ──────────────────────────────────────────────────────────────────────
# Compiled graphs (ready to invoke)
# ──────────────────────────────────────────────────────────────────────

chat_graph = build_chat_graph().compile()
memo_graph = build_memo_graph().compile()


async def run_chat(symbol: str, query: str) -> AgentState:
    """Execute the chat graph and return the final state."""
    initial_state: AgentState = {
        "symbol": symbol.upper(),
        "query": query,
        "mode": "chat",
        "cached_data": None,
        "raw_financials": None,
        "computed_metrics": None,
        "retrieved_chunks": None,
        "context": "",
        "llm_response": "",
        "memo": None,
        "errors": [],
        "step_log": [],
    }
    result = await chat_graph.ainvoke(initial_state)
    logger.info("Chat graph finished. Steps: %s", result.get("step_log", []))
    return result


async def run_memo(symbol: str) -> AgentState:
    """Execute the memo graph and return the final state."""
    initial_state: AgentState = {
        "symbol": symbol.upper(),
        "query": f"Generate an investment memo for {symbol.upper()}",
        "mode": "memo",
        "cached_data": None,
        "raw_financials": None,
        "computed_metrics": None,
        "retrieved_chunks": None,
        "context": "",
        "llm_response": "",
        "memo": None,
        "errors": [],
        "step_log": [],
    }
    result = await memo_graph.ainvoke(initial_state)
    logger.info("Memo graph finished. Steps: %s", result.get("step_log", []))
    return result
