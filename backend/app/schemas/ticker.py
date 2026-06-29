"""
FinSight AI — Pydantic response schemas for ticker endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────
# Company / Overview
# ──────────────────────────────────────────────────────────────────────

class CompanyInfo(BaseModel):
    """Core company metadata."""

    symbol: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    pe_trailing: Optional[float] = None
    pe_forward: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    description: str = ""
    currency: str = "USD"
    exchange: str = ""


class PriceChange(BaseModel):
    """Computed price change from the raw data."""

    absolute: Optional[float] = None
    percentage: Optional[float] = None
    direction: str = "flat"  # "up" | "down" | "flat"


# ──────────────────────────────────────────────────────────────────────
# Financial Statements
# ──────────────────────────────────────────────────────────────────────

class FinancialPeriod(BaseModel):
    """A single period of a financial statement."""

    period: str
    data: dict[str, Any]


class FinancialStatementResponse(BaseModel):
    """Response for a financial statement endpoint."""

    symbol: str
    statement_type: str
    periods: list[FinancialPeriod]


# ──────────────────────────────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────────────────────────────

class MetricPeriod(BaseModel):
    """Computed ratios for a single fiscal period."""

    period: str
    pe_ratio: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None


class MetricsResponse(BaseModel):
    """Full metrics response for a ticker."""

    symbol: str
    metrics: list[MetricPeriod]


# ──────────────────────────────────────────────────────────────────────
# Prices
# ──────────────────────────────────────────────────────────────────────

class PricePoint(BaseModel):
    """Single OHLCV data point."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceHistoryResponse(BaseModel):
    """Historical price data response."""

    symbol: str
    period: str = "5y"
    prices: list[PricePoint]


# ──────────────────────────────────────────────────────────────────────
# Ticker Overview (combined)
# ──────────────────────────────────────────────────────────────────────

class TickerOverview(BaseModel):
    """Full overview response combining company info, latest metrics, and price change."""

    company: CompanyInfo
    price_change: PriceChange
    latest_metrics: Optional[MetricPeriod] = None
    metrics_history: list[MetricPeriod] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Health / generic
# ──────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    environment: str = "development"


class ErrorResponse(BaseModel):
    detail: str
    status_code: int = 500
