"""
FinSight AI — Financial ratio calculation engine.

Computes fundamental ratios from raw yfinance financial statements.
All math is done in pure Python — no LLM involvement — so every number
is traceable and reproducible.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class PeriodMetrics:
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "pe_ratio": self.pe_ratio,
            "roe": self.roe,
            "roa": self.roa,
            "gross_margin": self.gross_margin,
            "operating_margin": self.operating_margin,
            "net_margin": self.net_margin,
            "debt_to_equity": self.debt_to_equity,
            "current_ratio": self.current_ratio,
            "revenue_growth": self.revenue_growth,
        }


def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safe division — returns None if inputs are missing or denominator is zero."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _get(data: dict[str, Any], *keys: str) -> Optional[float]:
    """Try multiple field names and return the first non-None numeric value.

    yfinance uses varying key names across versions — this makes us resilient.
    """
    for key in keys:
        val = data.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                continue
    return None


def compute_metrics_for_period(
    period: str,
    income: dict[str, Any],
    balance: dict[str, Any],
    market_cap: Optional[float] = None,
    prev_revenue: Optional[float] = None,
) -> PeriodMetrics:
    """Compute all ratios for a single fiscal period.

    Parameters
    ----------
    period : str
        Period label (e.g. "2024-12-31").
    income : dict
        Income statement data for this period.
    balance : dict
        Balance sheet data for this period.
    market_cap : float, optional
        Latest market cap (for P/E — only meaningful for most recent period).
    prev_revenue : float, optional
        Revenue from the prior period (for YoY growth).
    """
    # ── Extract values ─────────────────────────────────────────────
    revenue = _get(income, "Total Revenue", "TotalRevenue", "Revenue")
    gross_profit = _get(income, "Gross Profit", "GrossProfit")
    operating_income = _get(
        income, "Operating Income", "OperatingIncome", "EBIT"
    )
    net_income = _get(income, "Net Income", "NetIncome", "Net Income Common Stockholders")

    total_assets = _get(balance, "Total Assets", "TotalAssets")
    total_equity = _get(
        balance,
        "Stockholders Equity",
        "StockholdersEquity",
        "Total Stockholder Equity",
        "Common Stock Equity",
        "Total Equity Gross Minority Interest",
    )
    total_debt = _get(
        balance, "Total Debt", "TotalDebt", "Long Term Debt", "LongTermDebt"
    )
    current_assets = _get(balance, "Current Assets", "CurrentAssets", "Total Current Assets")
    current_liabilities = _get(
        balance,
        "Current Liabilities",
        "CurrentLiabilities",
        "Total Current Liabilities",
    )

    # ── Compute ratios ─────────────────────────────────────────────
    metrics = PeriodMetrics(period=period)

    # P/E Ratio = Market Cap / Net Income
    metrics.pe_ratio = _safe_div(market_cap, net_income)

    # ROE = Net Income / Shareholders' Equity
    metrics.roe = _safe_div(net_income, total_equity)

    # ROA = Net Income / Total Assets
    metrics.roa = _safe_div(net_income, total_assets)

    # Gross Margin = Gross Profit / Revenue
    metrics.gross_margin = _safe_div(gross_profit, revenue)

    # Operating Margin = Operating Income / Revenue
    metrics.operating_margin = _safe_div(operating_income, revenue)

    # Net Margin = Net Income / Revenue
    metrics.net_margin = _safe_div(net_income, revenue)

    # Debt-to-Equity = Total Debt / Total Equity
    metrics.debt_to_equity = _safe_div(total_debt, total_equity)

    # Current Ratio = Current Assets / Current Liabilities
    metrics.current_ratio = _safe_div(current_assets, current_liabilities)

    # Revenue Growth = (Revenue_t - Revenue_{t-1}) / Revenue_{t-1}
    if prev_revenue is not None and revenue is not None:
        metrics.revenue_growth = _safe_div(revenue - prev_revenue, abs(prev_revenue))

    logger.debug("Computed metrics for %s: %s", period, metrics.to_dict())
    return metrics


def compute_all_metrics(
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
    market_cap: Optional[float] = None,
) -> list[PeriodMetrics]:
    """Compute ratios across all available fiscal periods.

    Parameters
    ----------
    income_statements : list[dict]
        List of ``{"period": str, "data": dict}`` from the fetcher.
    balance_sheets : list[dict]
        List of ``{"period": str, "data": dict}`` from the fetcher.
    market_cap : float, optional
        Latest market cap for P/E on the most recent period.

    Returns
    -------
    list[PeriodMetrics]
        Metrics sorted by period descending (most recent first).
    """
    # Build lookup by period
    income_by_period = {stmt["period"]: stmt["data"] for stmt in income_statements}
    balance_by_period = {stmt["period"]: stmt["data"] for stmt in balance_sheets}

    # Sorted periods (ascending for growth calculation)
    all_periods = sorted(
        set(income_by_period.keys()) & set(balance_by_period.keys())
    )

    results: list[PeriodMetrics] = []
    prev_revenue: Optional[float] = None

    for i, period in enumerate(all_periods):
        income_data = income_by_period[period]
        balance_data = balance_by_period[period]

        # Only apply market_cap to the most recent period
        mc = market_cap if i == len(all_periods) - 1 else None

        metrics = compute_metrics_for_period(
            period=period,
            income=income_data,
            balance=balance_data,
            market_cap=mc,
            prev_revenue=prev_revenue,
        )
        results.append(metrics)

        # Track previous revenue for growth calc
        revenue = _get(income_data, "Total Revenue", "TotalRevenue", "Revenue")
        if revenue is not None:
            prev_revenue = revenue

    # Return most recent first
    results.reverse()
    return results
