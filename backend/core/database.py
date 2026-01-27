from __future__ import annotations

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from backend.config import get_settings

logger = logging.getLogger("backend.core.database")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """
    Initialize a global MongoDB (Motor) client + database handle.

    Why:
    - We want exactly one client per process.
    - Motor client is designed to be reused across requests.
    """
    global _client, _db

    settings = get_settings()

    try:
        if not settings.mongodb_uri:
            logger.warning(
                "MongoDB connection skipped: MONGODB_URI is not set (mock/dev mode)."
            )
            return

        if _client is not None and _db is not None:
            logger.info("MongoDB already connected; skipping re-initialization.")
            return

        logger.info("Connecting to MongoDB...")

        # serverSelectionTimeoutMS keeps startup failures fast + debuggable
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=8000,
        )
        _db = _client[settings.mongodb_db_name]

        # Smoke test to fail fast if URI/network/creds wrong
        await _client.admin.command("ping")

        logger.info(
            "MongoDB connected successfully",
            extra={
                "db": settings.mongodb_db_name,
                "traces_collection": settings.mongodb_traces_collection,
                "cache_collection": settings.mongodb_cache_collection,
            },
        )

    except PyMongoError:
        logger.exception("MongoDB connection failed (PyMongoError)")
        _client = None
        _db = None
        raise
    except Exception:
        logger.exception("MongoDB connection failed (unexpected)")
        _client = None
        _db = None
        raise


async def close_mongo_connection() -> None:
    """
    Close MongoDB client cleanly.

    Why:
    - Prevent resource leaks on shutdown.
    - Good hygiene for production readiness.
    """
    global _client, _db
    try:
        if _client is None:
            logger.info("MongoDB client already closed / not initialized.")
            return

        logger.info("Closing MongoDB connection...")
        _client.close()

        _client = None
        _db = None

        logger.info("MongoDB connection closed.")
    except Exception:
        logger.exception("Error while closing MongoDB connection")
        raise


def get_db() -> AsyncIOMotorDatabase:
    """
    Returns the active database handle.

    Important:
    - Must call connect_to_mongo() during app startup before using this.
    """
    if _db is None:
        raise RuntimeError(
            "MongoDB database is not initialized. "
            "Did you forget to call connect_to_mongo() at startup?"
        )
    return _db


def get_traces_collection_name() -> str:
    """Central source of truth for the traces collection name."""
    return get_settings().mongodb_traces_collection


def get_cache_collection_name() -> str:
    """Central source of truth for the semantic cache collection name."""
    return get_settings().mongodb_cache_collection
