from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from pymongo.errors import PyMongoError

from backend.config import get_settings
from backend.core.database import get_db, get_cache_collection_name

logger = logging.getLogger("backend.services.semantic_cache")


class SemanticCache:
    """
    Mongo-backed semantic cache for LLM responses.

    Design goals:
    - Optional & safe (never break chat flow)
    - Deterministic (exact-match for now)
    - Extendable to embeddings later
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def _collection(self):
        db = get_db()
        return db[get_cache_collection_name()]

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        """
        Create a stable hash for a prompt.
        This avoids storing huge prompt strings as primary keys.
        """
        return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()

    async def ensure_indexes(self) -> None:
        """
        Ensure indexes used by the cache.

        Safe to call multiple times.
        """
        try:
            col = self._collection()
            await col.create_index("prompt_hash", unique=True)
            await col.create_index("created_at")
            logger.info("Semantic cache indexes ensured")
        except PyMongoError:
            logger.exception("Failed to create semantic cache indexes")
            raise
        except Exception:
            logger.exception("Unexpected error while creating cache indexes")
            raise

    async def get(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cached response for a prompt.
        Returns None if not found or cache unavailable.
        """
        if not self._settings.mongodb_uri:
            return None

        try:
            prompt_hash = self._hash_prompt(prompt)
            doc = await self._collection().find_one(
                {"prompt_hash": prompt_hash},
                {"_id": 0},
            )

            if doc:
                logger.info(
                    "Semantic cache hit",
                    extra={"prompt_hash": prompt_hash},
                )
            else:
                logger.info(
                    "Semantic cache miss",
                    extra={"prompt_hash": prompt_hash},
                )

            return doc

        except RuntimeError:
            # DB not initialized
            logger.warning("Semantic cache skipped (Mongo not initialized)")
            return None
        except Exception:
            logger.exception("Semantic cache lookup failed")
            return None

    async def set(
        self,
        *,
        prompt: str,
        response_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a response in the cache.
        Failures are logged but never raised.
        """
        if not self._settings.mongodb_uri:
            return

        try:
            doc = {
                "prompt_hash": self._hash_prompt(prompt),
                "prompt": prompt,
                "response_text": response_text,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            }

            await self._collection().update_one(
                {"prompt_hash": doc["prompt_hash"]},
                {"$set": doc},
                upsert=True,
            )

            logger.info(
                "Semantic cache stored",
                extra={"prompt_hash": doc["prompt_hash"]},
            )

        except RuntimeError:
            logger.warning("Semantic cache write skipped (Mongo not initialized)")
        except Exception:
            logger.exception("Failed to write semantic cache")
