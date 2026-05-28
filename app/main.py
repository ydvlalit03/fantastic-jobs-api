from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.middleware.security import SecurityHeadersMiddleware, TraceIdMiddleware

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    from app.db.base import Base
    from app.db.models import ClientConfig  # noqa: F401
    from app.db.session import engine

    logger = logging.getLogger("app.main")

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("[STARTUP] Database tables ready")

    # Shared HTTP client for salary estimator
    app.state.http_client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=20),
        timeout=httpx.Timeout(30),
    )
    logger.info("[STARTUP] HTTP client ready")

    yield

    # Cleanup
    await app.state.http_client.aclose()
    logger.info("[SHUTDOWN] HTTP client closed")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "version": settings.APP_VERSION,
            "services": ["fantastic-jobs", "job-title", "salary-estimator"],
        }

    return app


app = create_app()
