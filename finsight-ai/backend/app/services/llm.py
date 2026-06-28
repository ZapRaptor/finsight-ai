"""
FinSight AI — Gemini LLM client.

Wraps Google's Gemini 1.5 Flash for both streaming text generation
and structured JSON output. Uses the google-genai SDK directly
for maximum compatibility with auth keys (AQ. prefix).
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Optional

from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Initialize the google-genai client ─────────────────────────────────
_client = genai.Client(api_key=settings.gemini_api_key)

# ── System prompts ─────────────────────────────────────────────────────

FINANCIAL_ANALYST_PROMPT = """You are FinSight AI, an elite financial research analyst. 
You provide institutional-grade analysis grounded strictly in the data provided to you.

Rules:
1. ONLY use the financial data, metrics, and document excerpts provided in the context.
2. Never fabricate numbers. If data is missing, say so explicitly.
3. When citing metrics (P/E, ROE, margins), reference the exact period they belong to.
4. Provide actionable insights, not generic platitudes.
5. Structure your responses with clear headers and bullet points.
6. When analyzing trends, compare across multiple periods and explain the trajectory.
7. Always consider both bullish and bearish perspectives."""

MEMO_GENERATOR_PROMPT = """You are FinSight AI's Investment Memo Generator.
Given financial data and computed metrics for a company, produce a structured 
investment memo in valid JSON format.

The JSON must follow this exact schema:
{
  "summary": "2-3 sentence executive summary of the investment thesis",
  "bull_case": ["point 1", "point 2", "point 3"],
  "bear_case": ["point 1", "point 2", "point 3"],
  "swot": {
    "strengths": ["s1", "s2"],
    "weaknesses": ["w1", "w2"],
    "opportunities": ["o1", "o2"],
    "threats": ["t1", "t2"]
  },
  "guidance": "Forward-looking analysis based on trends in the data",
  "recommendation": "BUY or HOLD or SELL",
  "confidence": 0.0 to 1.0
}

Rules:
1. Base every point STRICTLY on the provided financial data.
2. Reference specific metrics and periods.
3. Be balanced — even a BUY recommendation should have real bear cases.
4. Output ONLY the JSON object, no markdown fences or extra text."""

MODEL = "gemini-2.5-flash"


class GeminiClient:
    """High-level wrapper for Gemini interactions using google-genai SDK."""

    async def generate(
        self,
        query: str,
        context: str,
        system_prompt: str = FINANCIAL_ANALYST_PROMPT,
    ) -> str:
        """Generate a complete text response (non-streaming)."""
        response = await _client.aio.models.generate_content(
            model=MODEL,
            contents=f"Context:\n{context}\n\nQuestion: {query}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
            ),
        )
        return response.text or ""

    async def generate_stream(
        self,
        query: str,
        context: str,
        system_prompt: str = FINANCIAL_ANALYST_PROMPT,
    ) -> AsyncIterator[str]:
        """Stream text response token-by-token."""
        async for chunk in _client.aio.models.generate_content_stream(
            model=MODEL,
            contents=f"Context:\n{context}\n\nQuestion: {query}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
            ),
        ):
            if chunk.text:
                yield chunk.text

    async def generate_memo(
        self,
        context: str,
        symbol: str,
    ) -> dict[str, Any]:
        """Generate a structured investment memo as JSON."""
        response = await _client.aio.models.generate_content(
            model=MODEL,
            contents=(
                f"Generate an investment memo for {symbol}.\n\n"
                f"Financial Data:\n{context}"
            ),
            config=types.GenerateContentConfig(
                system_instruction=MEMO_GENERATOR_PROMPT,
                temperature=0.4,
                response_mime_type="application/json",
            ),
        )
        raw = (response.text or "").strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            memo = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse memo JSON: %s", raw[:500])
            memo = {
                "summary": raw[:500],
                "bull_case": [],
                "bear_case": [],
                "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
                "guidance": "Unable to parse structured output.",
                "recommendation": "HOLD",
                "confidence": 0.0,
            }

        return memo


# Singleton
gemini_client = GeminiClient()
