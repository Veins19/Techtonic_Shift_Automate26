from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# -------------------------------
# Logging setup (backend-wide)
# -------------------------------
def _configure_logging(log_level: str) -> None:
    """
    Configure root logging once, with timestamps.

    Why:
    - Every module will import settings; logging should be ready early.
    - Timestamped logs are essential for debugging distributed/async flows.
    """
    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


logger = logging.getLogger("backend.config")

# -------------------------------
# Settings (Pydantic v2)
# -------------------------------
class Settings(BaseSettings):
    """
    Central typed config for the whole backend.

    Loaded from:
    - .env in project root
    - real environment variables

    Conditional validation is applied based on USE_MOCK_LLM.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -------------------------------
    # App
    # -------------------------------
    api_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="API_ENV"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # -------------------------------
    # Feature toggles
    # -------------------------------
    use_mock_llm: bool = Field(default=True, alias="USE_MOCK_LLM")

    # -------------------------------
    # Google Gemini (LLM Provider)
    # -------------------------------
    # Exposed with provider-friendly names
    gemini_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model_name: str = Field(
        default="models/gemini-1.5-flash",
        alias="GEMINI_MODEL_NAME",
    )

    # -------------------------------
    # MongoDB
    # -------------------------------
    mongodb_uri: Optional[str] = Field(default=None, alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="llm_flight_recorder", alias="MONGODB_DB_NAME")
    mongodb_traces_collection: str = Field(
        default="traces", alias="MONGODB_TRACES_COLLECTION"
    )
    mongodb_cache_collection: str = Field(
        default="semantic_cache", alias="MONGODB_CACHE_COLLECTION"
    )

    # -------------------------------
    # Rate limits
    # -------------------------------
    max_rpm: int = Field(default=25, alias="MAX_RPM")
    max_rpd: int = Field(default=14000, alias="MAX_RPD")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    Why:
    - Settings parsing/validation should happen once.
    - Shared across the entire backend.
    """
    try:
        settings = Settings()

        # Configure logging ASAP
        _configure_logging(settings.log_level)

        # -------------------------------
        # Conditional validation
        # -------------------------------
        if not settings.use_mock_llm:
            missing = []

            if not settings.gemini_api_key:
                missing.append("GOOGLE_API_KEY")

            if not settings.mongodb_uri:
                missing.append("MONGODB_URI")

            if missing:
                raise ValueError(
                    f"Missing required env vars for non-mock mode: {', '.join(missing)}"
                )

        if not settings.mongodb_uri:
            logger.warning(
                "MONGODB_URI is not set. Mongo-backed features will be disabled."
            )

        logger.info(
            "Settings loaded",
            extra={
                "API_ENV": settings.api_env,
                "USE_MOCK_LLM": settings.use_mock_llm,
                "GEMINI_MODEL": settings.gemini_model_name,
                "MONGODB_DB_NAME": settings.mongodb_db_name,
                "MAX_RPM": settings.max_rpm,
                "MAX_RPD": settings.max_rpd,
            },
        )

        return settings

    except ValidationError:
        _configure_logging(os.getenv("LOG_LEVEL", "INFO"))
        logger.exception("Settings validation error")
        raise

    except Exception:
        _configure_logging(os.getenv("LOG_LEVEL", "INFO"))
        logger.exception("Failed to load settings")
        raise
