"""
FinSight AI — Ticker API routes.

Endpoints
---------
GET /api/ticker/{symbol}            → Full overview (company + metrics + price)
GET /api/ticker/{symbol}/financials → Raw financial statements
GET /api/ticker/{symbol}/metrics    → Computed ratio time-series
GET /api/ticker/{symbol}/prices     → Historical OHLCV
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db import crud
from app.schemas.ticker import (
    CompanyInfo,
    FinancialPeriod,
    FinancialStatementResponse,
    MetricPeriod,
    MetricsResponse,
    PriceChange,
    PriceHistoryResponse,
    PricePoint,
    TickerOverview,
)
from app.services import fetcher
from app.services.ratios import compute_all_metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ticker", tags=["ticker"])


# ──────────────────────────────────────────────────────────────────────
# GET /api/ticker/{symbol}  —  Full overview
# ──────────────────────────────────────────────────────────────────────


@router.get("/{symbol}", response_model=TickerOverview)
async def get_ticker_overview(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Fetch complete ticker overview: company info, latest metrics, and price change."""
    symbol = symbol.upper()

    try:
        # 1) Fetch company info
        info = await fetcher.fetch_company_info(symbol)
        if not info or not info.get("name"):
            raise HTTPException(status_code=404, detail=f"Ticker '{symbol}' not found")

        company_info = CompanyInfo(**info)

        # 2) Persist company to DB
        company = await crud.upsert_company(
            db,
            symbol=symbol,
            name=info.get("name"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("market_cap"),
            description=info.get("description"),
        )

        # 3) Fetch financial statements & compute metrics
        income = await fetcher.fetch_income_statement(symbol)
        balance = await fetcher.fetch_balance_sheet(symbol)

        metrics_list = compute_all_metrics(
            income_statements=income,
            balance_sheets=balance,
            market_cap=info.get("market_cap"),
        )

        # 4) Persist metrics
        for m in metrics_list:
            await crud.upsert_metric(
                db,
                company_id=company.id,
                period=m.period,
                pe_ratio=m.pe_ratio,
                roe=m.roe,
                roa=m.roa,
                gross_margin=m.gross_margin,
                operating_margin=m.operating_margin,
                net_margin=m.net_margin,
                debt_to_equity=m.debt_to_equity,
                current_ratio=m.current_ratio,
                revenue_growth=m.revenue_growth,
            )

        # 5) Persist financial statements
        for stmt in income:
            await crud.upsert_financial(
                db,
                company_id=company.id,
                period=stmt["period"],
                statement_type="income",
                data=stmt["data"],
            )
        for stmt in balance:
            await crud.upsert_financial(
                db,
                company_id=company.id,
                period=stmt["period"],
                statement_type="balance",
                data=stmt["data"],
            )

        # 6) Compute price change
        price_change = PriceChange()
        current_price = info.get("current_price")
        prev_close = info.get("previous_close")
        if current_price and prev_close:
            diff = current_price - prev_close
            pct = (diff / prev_close) * 100
            price_change = PriceChange(
                absolute=round(diff, 2),
                percentage=round(pct, 2),
                direction="up" if diff > 0 else "down" if diff < 0 else "flat",
            )

        # 7) Build response
        metric_periods = [
            MetricPeriod(**m.to_dict()) for m in metrics_list
        ]

        return TickerOverview(
            company=company_info,
            price_change=price_change,
            latest_metrics=metric_periods[0] if metric_periods else None,
            metrics_history=metric_periods,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching overview for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────
# GET /api/ticker/{symbol}/financials
# ──────────────────────────────────────────────────────────────────────


@router.get("/{symbol}/financials", response_model=FinancialStatementResponse)
async def get_financials(
    symbol: str,
    statement_type: str = Query(
        default="income",
        description="Statement type: income | balance | cashflow",
    ),
):
    """Fetch raw financial statements for a ticker."""
    symbol = symbol.upper()

    if statement_type not in ("income", "balance", "cashflow"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid statement_type: '{statement_type}'. Use income|balance|cashflow.",
        )

    try:
        data = await fetcher.fetch_financial_statements(symbol, statement_type)
        periods = [FinancialPeriod(**item) for item in data]

        return FinancialStatementResponse(
            symbol=symbol,
            statement_type=statement_type,
            periods=periods,
        )
    except Exception as e:
        logger.exception("Error fetching financials for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────
# GET /api/ticker/{symbol}/metrics
# ──────────────────────────────────────────────────────────────────────


@router.get("/{symbol}/metrics", response_model=MetricsResponse)
async def get_metrics(symbol: str):
    """Fetch computed financial ratios (time series)."""
    symbol = symbol.upper()

    try:
        info = await fetcher.fetch_company_info(symbol)
        income = await fetcher.fetch_income_statement(symbol)
        balance = await fetcher.fetch_balance_sheet(symbol)

        metrics_list = compute_all_metrics(
            income_statements=income,
            balance_sheets=balance,
            market_cap=info.get("market_cap"),
        )

        return MetricsResponse(
            symbol=symbol,
            metrics=[MetricPeriod(**m.to_dict()) for m in metrics_list],
        )
    except Exception as e:
        logger.exception("Error computing metrics for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────
# GET /api/ticker/{symbol}/prices
# ──────────────────────────────────────────────────────────────────────


@router.get("/{symbol}/prices", response_model=PriceHistoryResponse)
async def get_prices(
    symbol: str,
    period: str = Query(default="5y", description="Price history period (e.g. 1y, 5y, max)"),
):
    """Fetch historical OHLCV price data."""
    symbol = symbol.upper()

    try:
        prices = await fetcher.fetch_historical_prices(symbol, period=period)
        return PriceHistoryResponse(
            symbol=symbol,
            period=period,
            prices=[PricePoint(**p) for p in prices],
        )
    except Exception as e:
        logger.exception("Error fetching prices for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))
