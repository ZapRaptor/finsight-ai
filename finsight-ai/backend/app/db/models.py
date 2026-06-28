"""
FinSight AI — SQLAlchemy ORM models.

Tables
------
- companies   : Ticker metadata (symbol, name, sector, market cap).
- financials  : Raw financial statements stored as JSONB.
- metrics     : Pre-computed fundamental ratios.
- queries     : Audit log of user questions and AI responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Shared base for all ORM models."""
    pass


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    sector = Column(String(128), nullable=True)
    industry = Column(String(255), nullable=True)
    market_cap = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    financials = relationship("Financial", back_populates="company", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="company", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company {self.symbol}>"


class Financial(Base):
    __tablename__ = "financials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period = Column(String(20), nullable=False)  # e.g. "2024-12-31" or "2024Q3"
    statement_type = Column(
        String(20), nullable=False
    )  # income | balance | cashflow
    data = Column(JSONB, nullable=False)  # Raw yfinance JSON dict
    fetched_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="financials")

    def __repr__(self) -> str:
        return f"<Financial {self.statement_type} {self.period}>"


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period = Column(String(20), nullable=False)

    # Fundamental ratios (all nullable — not every ratio is computable for every period)
    pe_ratio = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    roa = Column(Float, nullable=True)
    gross_margin = Column(Float, nullable=True)
    operating_margin = Column(Float, nullable=True)
    net_margin = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    current_ratio = Column(Float, nullable=True)
    revenue_growth = Column(Float, nullable=True)

    computed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<Metric {self.period}>"


class Query(Base):
    __tablename__ = "queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    sources = Column(JSONB, nullable=True)  # List of chunk references
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="queries")

    def __repr__(self) -> str:
        return f"<Query {self.id}>"
