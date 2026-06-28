"""
FinSight AI — Application configuration.

Loads settings from environment variables / .env file using Pydantic BaseSettings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database (PostgreSQL) ──────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://finsight:finsight_dev@localhost:5432/finsight_db"
    )

    # ── Vector Store (Qdrant) ──────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"

    # ── Cache (Redis) ──────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── LLM (Google Gemini) ────────────────────────────────────────────
    gemini_api_key: str = "your-gemini-api-key-here"

    # ── Embeddings ─────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Cache TTL (seconds — default 24 h) ─────────────────────────────
    cache_ttl: int = 86400

    # ── CORS ───────────────────────────────────────────────────────────
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── App ────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    # ── Derived helpers ────────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — parsed once per process."""
    return Settings()
