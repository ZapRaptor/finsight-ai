"""
FinSight AI — Redis caching layer.

Provides an async Redis wrapper with JSON serialization
and namespace-based key management.

Key convention:  finsight:{category}:{symbol}:{qualifier}
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisCache:
    """Async Redis cache with JSON ser/de and configurable TTL."""

    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        self._client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
        # Verify connectivity
        await self._client.ping()
        logger.info("Redis connected at %s", settings.redis_url)

    async def disconnect(self) -> None:
        """Gracefully close the Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("RedisCache is not connected. Call .connect() first.")
        return self._client

    # ── Key helpers ────────────────────────────────────────────────────

    @staticmethod
    def make_key(category: str, symbol: str, qualifier: str = "") -> str:
        """Build a namespaced cache key.

        Examples
        -------
        >>> RedisCache.make_key("company", "AAPL")
        'finsight:company:AAPL'
        >>> RedisCache.make_key("financials", "AAPL", "income")
        'finsight:financials:AAPL:income'
        """
        parts = ["finsight", category, symbol.upper()]
        if qualifier:
            parts.append(qualifier)
        return ":".join(parts)

    # ── Core operations ────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a JSON-deserialized value, or None on miss."""
        raw = await self.client.get(key)
        if raw is None:
            logger.debug("Cache MISS: %s", key)
            return None
        logger.debug("Cache HIT: %s", key)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        """Store a JSON-serialized value with optional TTL (seconds)."""
        ttl = ttl or settings.cache_ttl
        serialized = json.dumps(value, default=str)
        await self.client.set(key, serialized, ex=ttl)
        logger.debug("Cache SET: %s (ttl=%ds)", key, ttl)

    async def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        await self.client.delete(key)
        logger.debug("Cache DEL: %s", key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern. Returns count deleted."""
        count = 0
        async for key in self.client.scan_iter(match=pattern):
            await self.client.delete(key)
            count += 1
        logger.debug("Cache DEL pattern '%s': %d keys", pattern, count)
        return count

    async def exists(self, key: str) -> bool:
        """Check whether a key exists."""
        return bool(await self.client.exists(key))


# Module-level singleton
cache = RedisCache()
