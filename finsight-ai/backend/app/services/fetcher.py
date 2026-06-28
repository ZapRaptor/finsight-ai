"""
FinSight AI — Yahoo Finance data fetcher.

Wraps the `yfinance` library with Redis caching and async execution.
All heavy yfinance calls are offloaded to a thread pool since yfinance
is synchronous under the hood.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Optional

import yfinance as yf

from app.services.cache import cache, RedisCache

logger = logging.getLogger(__name__)

# Thread pool for blocking yfinance calls
_executor = ThreadPoolExecutor(max_workers=4)


def _run_sync(fn, *args, **kwargs):
    """Helper: call a blocking function."""
    return fn(*args, **kwargs)


async def _run_in_thread(fn, *args, **kwargs):
    """Run a synchronous function in the thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: fn(*args, **kwargs))


# ──────────────────────────────────────────────────────────────────────
# Raw yfinance helpers (synchronous — run via _run_in_thread)
# ──────────────────────────────────────────────────────────────────────

def _get_ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol.upper())


def _fetch_info(symbol: str) -> dict[str, Any]:
    """Fetch company metadata."""
    ticker = _get_ticker(symbol)
    info = ticker.info or {}
    return {
        "symbol": symbol.upper(),
        "name": info.get("longName") or info.get("shortName", ""),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "market_cap": info.get("marketCap"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "pe_trailing": info.get("trailingPE"),
        "pe_forward": info.get("forwardPE"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "description": info.get("longBusinessSummary", ""),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", ""),
    }


def _fetch_financials(symbol: str, statement: str) -> list[dict[str, Any]]:
    """Fetch a financial statement as a list of period dicts.

    Parameters
    ----------
    statement : str
        One of 'income', 'balance', 'cashflow'.
    """
    ticker = _get_ticker(symbol)

    df = None
    if statement == "income":
        df = ticker.income_stmt
    elif statement == "balance":
        df = ticker.balance_sheet
    elif statement == "cashflow":
        df = ticker.cashflow
    else:
        raise ValueError(f"Unknown statement type: {statement}")

    if df is None or df.empty:
        return []

    records: list[dict[str, Any]] = []
    for col in df.columns:
        period_label = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        period_data = df[col].dropna().to_dict()
        # Convert keys to strings for JSON serialization
        clean_data = {str(k): _safe_value(v) for k, v in period_data.items()}
        records.append({
            "period": period_label,
            "data": clean_data,
        })

    return records


def _fetch_prices(symbol: str, period: str = "5y") -> list[dict[str, Any]]:
    """Fetch historical OHLCV data."""
    ticker = _get_ticker(symbol)
    df = ticker.history(period=period)

    if df is None or df.empty:
        return []

    records: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        records.append({
            "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
            "open": round(float(row.get("Open", 0)), 2),
            "high": round(float(row.get("High", 0)), 2),
            "low": round(float(row.get("Low", 0)), 2),
            "close": round(float(row.get("Close", 0)), 2),
            "volume": int(row.get("Volume", 0)),
        })

    return records


def _safe_value(v: Any) -> Any:
    """Convert numpy/pandas types to JSON-safe Python types."""
    import numpy as np

    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v) if not np.isnan(v) else None
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


# ──────────────────────────────────────────────────────────────────────
# Public async API (cached)
# ──────────────────────────────────────────────────────────────────────

async def fetch_company_info(symbol: str) -> dict[str, Any]:
    """Fetch company metadata, cached in Redis."""
    cache_key = RedisCache.make_key("company", symbol)
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _run_in_thread(_fetch_info, symbol)
    await cache.set(cache_key, data)
    logger.info("Fetched company info for %s", symbol.upper())
    return data


async def fetch_financial_statements(
    symbol: str, statement_type: str
) -> list[dict[str, Any]]:
    """Fetch a financial statement (income/balance/cashflow), cached in Redis."""
    cache_key = RedisCache.make_key("financials", symbol, statement_type)
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _run_in_thread(_fetch_financials, symbol, statement_type)
    await cache.set(cache_key, data)
    logger.info("Fetched %s statement for %s", statement_type, symbol.upper())
    return data


async def fetch_income_statement(symbol: str) -> list[dict[str, Any]]:
    return await fetch_financial_statements(symbol, "income")


async def fetch_balance_sheet(symbol: str) -> list[dict[str, Any]]:
    return await fetch_financial_statements(symbol, "balance")


async def fetch_cash_flow(symbol: str) -> list[dict[str, Any]]:
    return await fetch_financial_statements(symbol, "cashflow")


async def fetch_historical_prices(
    symbol: str, period: str = "5y"
) -> list[dict[str, Any]]:
    """Fetch historical OHLCV prices, cached in Redis."""
    cache_key = RedisCache.make_key("prices", symbol, period)
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _run_in_thread(_fetch_prices, symbol, period)
    await cache.set(cache_key, data)
    logger.info("Fetched %s price history for %s", period, symbol.upper())
    return data


async def fetch_all_data(symbol: str) -> dict[str, Any]:
    """Convenience: fetch all data for a ticker in parallel."""
    info, income, balance, cashflow, prices = await asyncio.gather(
        fetch_company_info(symbol),
        fetch_income_statement(symbol),
        fetch_balance_sheet(symbol),
        fetch_cash_flow(symbol),
        fetch_historical_prices(symbol),
    )
    return {
        "info": info,
        "income_statement": income,
        "balance_sheet": balance,
        "cash_flow": cashflow,
        "prices": prices,
    }
