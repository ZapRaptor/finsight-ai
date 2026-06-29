"""
FinSight AI — FastAPI dependency injection.

Provides shared resources (DB sessions, cache, etc.) to route handlers.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.services.cache import cache


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session."""
    async for session in get_session():
        yield session


def get_cache():
    """Return the Redis cache singleton."""
    return cache
