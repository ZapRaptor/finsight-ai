"""
FinSight AI — FastAPI application entrypoint.

Initializes the app, middleware, lifespan events, and route registrations.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.engine import dispose_engine, init_db
from app.services.cache import cache

settings = get_settings()

# ── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("finsight")


# ── Lifespan (startup / shutdown) ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of shared resources."""
    # ── Startup ──
    logger.info("Starting FinSight AI (%s)", settings.app_env)

    # Initialize database tables
    await init_db()
    logger.info("Database initialized")

    # Connect Redis cache
    try:
        await cache.connect()
        logger.info("Redis cache connected")
    except Exception as e:
        logger.warning("Redis unavailable — running without cache: %s", e)

    yield

    # ── Shutdown ──
    logger.info("Shutting down FinSight AI")
    await cache.disconnect()
    await dispose_engine()
    logger.info("Cleanup complete")


# ── App factory ────────────────────────────────────────────────────────
app = FastAPI(
    title="FinSight AI",
    description=(
        "AI-powered financial research platform. "
        "Automates extraction, calculation, and synthesis of financial data."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS middleware ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ───────────────────────────────────────────────────────
@app.get("/api/health", tags=["system"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.app_env,
    }


# ── Register routers ──────────────────────────────────────────────────
from app.api.routes.ticker import router as ticker_router  # noqa: E402
from app.api.routes.chat import router as chat_router  # noqa: E402
from app.api.routes.report import router as report_router  # noqa: E402

app.include_router(ticker_router)
app.include_router(chat_router)
app.include_router(report_router)


# ── Dev: run with `python -m app.main` ─────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
