from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.core.database import connect_to_mongo, close_mongo_connection
from backend.repositories.trace_repo import TraceRepo

logger = logging.getLogger("backend.main")


def create_app() -> FastAPI:
    """
    FastAPI application factory.

    Why:
    - Clean testability (create app in tests without side effects)
    - Explicit lifecycle management
    - Centralized router registration
    """
    settings = get_settings()

    app = FastAPI(
        title="LLM Flight Recorder",
        version="0.1.0",
        description="Observability + replay system for LLM interactions",
    )

    # ---------------------------------
    # CORS (Streamlit frontend -> API)
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

    trace_repo = TraceRepo()

    # ---------------------------------
    # Lifecycle events
    # ---------------------------------
    @app.on_event("startup")
    async def _startup() -> None:
        """
        Application startup:
        - Connect to MongoDB
        - Ensure indexes once
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

            await connect_to_mongo()

            if settings.mongodb_uri:
                await trace_repo.ensure_indexes()
                logger.info("Mongo indexes ensured at startup")

            logger.info("Backend startup completed successfully")

        except Exception:
            logger.exception("Backend startup failed")
            raise

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        """
        Graceful shutdown:
        - Close Mongo connection
        """
        try:
            logger.info("Backend shutdown initiated")
            await close_mongo_connection()
            logger.info("Backend shutdown completed")
        except Exception:
            logger.exception("Backend shutdown failed")
            raise

    # ---------------------------------
    # Health check
    # ---------------------------------
    @app.get("/health")
    async def health() -> dict:
        """
        Lightweight health endpoint for:
        - frontend checks
        - deploy verification
        """
        return {
            "status": "ok",
            "env": settings.api_env,
            "mock": settings.use_mock_llm,
            "mongo_enabled": bool(settings.mongodb_uri),
        }

    # ---------------------------------
    # Routers (safe include)
    # ---------------------------------
    try:
        from backend.routes.chat import router as chat_router  # type: ignore

        app.include_router(chat_router)
        logger.info("Included router: chat")
    except Exception:
        logger.warning("Chat router not included (missing or invalid).")

    try:
        from backend.routes.monitor import router as monitor_router  # type: ignore

        app.include_router(monitor_router)
        logger.info("Included router: monitor")
    except Exception:
        logger.warning("Monitor router not included (missing or invalid).")

    logger.info("All available routers registered")

    return app


app = create_app()
