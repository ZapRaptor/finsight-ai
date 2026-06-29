"""
FinSight AI — CRUD helpers for the database layer.

All functions accept an AsyncSession and return ORM objects or dicts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, Financial, Metric, Query


# ──────────────────────────────────────────────────────────────────────
# Companies
# ──────────────────────────────────────────────────────────────────────

async def upsert_company(
    session: AsyncSession,
    symbol: str,
    *,
    name: Optional[str] = None,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    market_cap: Optional[float] = None,
    description: Optional[str] = None,
) -> Company:
    """Insert or update a company by ticker symbol."""
    result = await session.execute(
        select(Company).where(Company.symbol == symbol.upper())
    )
    company = result.scalar_one_or_none()

    if company is None:
        company = Company(symbol=symbol.upper())
        session.add(company)

    if name is not None:
        company.name = name
    if sector is not None:
        company.sector = sector
    if industry is not None:
        company.industry = industry
    if market_cap is not None:
        company.market_cap = market_cap
    if description is not None:
        company.description = description

    company.last_fetched_at = datetime.now(timezone.utc)

    await session.flush()
    return company


async def get_company_by_symbol(
    session: AsyncSession, symbol: str
) -> Optional[Company]:
    """Look up a company by its ticker."""
    result = await session.execute(
        select(Company).where(Company.symbol == symbol.upper())
    )
    return result.scalar_one_or_none()


# ──────────────────────────────────────────────────────────────────────
# Financials
# ──────────────────────────────────────────────────────────────────────

async def upsert_financial(
    session: AsyncSession,
    company_id: UUID,
    period: str,
    statement_type: str,
    data: dict[str, Any],
) -> Financial:
    """Insert or update a financial statement record."""
    result = await session.execute(
        select(Financial).where(
            Financial.company_id == company_id,
            Financial.period == period,
            Financial.statement_type == statement_type,
        )
    )
    financial = result.scalar_one_or_none()

    if financial is None:
        financial = Financial(
            company_id=company_id,
            period=period,
            statement_type=statement_type,
            data=data,
        )
        session.add(financial)
    else:
        financial.data = data
        financial.fetched_at = datetime.now(timezone.utc)

    await session.flush()
    return financial


async def get_financials_by_symbol(
    session: AsyncSession,
    symbol: str,
    statement_type: Optional[str] = None,
) -> list[Financial]:
    """Retrieve all financial records for a ticker, optionally filtered by type."""
    company = await get_company_by_symbol(session, symbol)
    if company is None:
        return []

    stmt = select(Financial).where(Financial.company_id == company.id)
    if statement_type:
        stmt = stmt.where(Financial.statement_type == statement_type)
    stmt = stmt.order_by(Financial.period.desc())

    result = await session.execute(stmt)
    return list(result.scalars().all())


# ──────────────────────────────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────────────────────────────

async def upsert_metric(
    session: AsyncSession,
    company_id: UUID,
    period: str,
    **ratios: Optional[float],
) -> Metric:
    """Insert or update a metrics row for a given period."""
    result = await session.execute(
        select(Metric).where(
            Metric.company_id == company_id,
            Metric.period == period,
        )
    )
    metric = result.scalar_one_or_none()

    if metric is None:
        metric = Metric(company_id=company_id, period=period)
        session.add(metric)

    for key, value in ratios.items():
        if hasattr(metric, key):
            setattr(metric, key, value)

    metric.computed_at = datetime.now(timezone.utc)
    await session.flush()
    return metric


async def get_metrics_by_symbol(
    session: AsyncSession, symbol: str
) -> list[Metric]:
    """Retrieve all computed metrics for a ticker, most recent first."""
    company = await get_company_by_symbol(session, symbol)
    if company is None:
        return []

    result = await session.execute(
        select(Metric)
        .where(Metric.company_id == company.id)
        .order_by(Metric.period.desc())
    )
    return list(result.scalars().all())


# ──────────────────────────────────────────────────────────────────────
# Queries (audit log)
# ──────────────────────────────────────────────────────────────────────

async def save_query(
    session: AsyncSession,
    question: str,
    response: str,
    company_id: Optional[UUID] = None,
    sources: Optional[list[dict[str, Any]]] = None,
) -> Query:
    """Persist a user question and the AI response."""
    q = Query(
        company_id=company_id,
        question=question,
        response=response,
        sources=sources,
    )
    session.add(q)
    await session.flush()
    return q


async def get_recent_queries(
    session: AsyncSession, limit: int = 20
) -> list[Query]:
    """Return the N most recent queries."""
    result = await session.execute(
        select(Query).order_by(Query.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
