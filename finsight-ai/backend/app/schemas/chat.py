"""
FinSight AI — Pydantic schemas for the chat endpoint.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""

    symbol: str = Field(..., description="Ticker symbol (e.g. AAPL)")
    question: str = Field(..., description="User's question about the company")
    include_documents: bool = Field(
        default=True,
        description="Whether to include Qdrant document retrieval in context",
    )


class ChatResponse(BaseModel):
    """Non-streaming response for the /api/chat endpoint."""

    symbol: str
    question: str
    response: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    step_log: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
