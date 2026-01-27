from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.core.database import connect_to_mongo, close_mongo_connection
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.repositories.trace_repo import TraceRepo

logger = logging.getLogger("backend.main")


def create_app() -> FastAPI:
    """
    FastAPI application factory.

    Responsibilities:
    - Initialize FastAPI instance
    - Configure middleware (CORS + Rate Limiting)
    - Register routers safely
    - Handle startup/shutdown lifecycle
    """

    settings = get_settings()

    app = FastAPI(
        title="LLM Flight Recorder",
        version="0.1.0",
        description="Observability + replay system for LLM interactions",
    )

    # ---------------------------------
    # Middleware: CORS
    # ---------------------------------
    allowed_origins = [
        "http://localhost",
        "http://localhost:8501",
        "http://127.0.0.1",
        "http://127.0.0.1:8501",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("CORS middleware enabled", extra={"origins": allowed_origins})

    # ---------------------------------
    # Middleware: Rate Limiting
    # ---------------------------------
    app.add_middleware(RateLimitMiddleware)
    logger.info(
        "RateLimitMiddleware enabled",
        extra={"MAX_RPM": settings.max_rpm, "MAX_RPD": settings.max_rpd},
    )

    trace_repo = TraceRepo()

    # ---------------------------------
    # Lifecycle Events
    # ---------------------------------
    @app.on_event("startup")
    async def _startup() -> None:
        """
        Startup responsibilities:
        - Connect MongoDB
        - Ensure trace indexes exist
        """

        try:
            logger.info(
                "Backend startup initiated",
                extra={
                    "API_ENV": settings.api_env,
                    "USE_MOCK_LLM": settings.use_mock_llm,
                    "MONGODB_ENABLED": bool(settings.mongodb_uri),
                },
            )

            # Connect to MongoDB
            await connect_to_mongo()

            # Ensure indexes once at startup
            if settings.mongodb_uri:
                await trace_repo.ensure_indexes()
                logger.info("Mongo trace indexes ensured")

            logger.info("Backend startup completed successfully ✅")

        except Exception:
            logger.exception("Backend startup failed ❌")
            raise

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        """
        Shutdown responsibilities:
        - Close MongoDB connection cleanly
        """

        try:
            logger.info("Backend shutdown initiated")
            await close_mongo_connection()
            logger.info("Backend shutdown completed ✅")
        except Exception:
            logger.exception("Backend shutdown failed ❌")
            raise

    # ---------------------------------
    # Health Check
    # ---------------------------------
    @app.get("/health")
    async def health() -> dict:
        """
        Health endpoint for frontend + deploy verification.
        """

        return {
            "status": "ok",
            "env": settings.api_env,
            "mock": settings.use_mock_llm,
            "mongo_enabled": bool(settings.mongodb_uri),
        }

    # ---------------------------------
    # Routers Registration
    # ---------------------------------
    try:
        from backend.routes.chat import router as chat_router

        app.include_router(chat_router)
        logger.info("Router registered: /chat")

    except Exception:
        logger.exception("Chat router failed to load")

    try:
        from backend.routes.monitor import router as monitor_router

        app.include_router(monitor_router)
        logger.info("Router registered: /traces")

    except Exception:
        logger.exception("Monitor router failed to load")

    logger.info("All available routers registered successfully ✅")

    return app


# App entrypoint
app = create_app()
