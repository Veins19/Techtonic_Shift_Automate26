from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo.errors import PyMongoError

from backend.core.database import get_db, get_traces_collection_name

logger = logging.getLogger("backend.repositories.trace_repo")


class TraceRepo:
    """
    Mongo-backed repository for LLM traces.

    Document shape (flexible):
      - trace_id: str (unique business id)
      - created_at: str (recommended "%Y-%m-%d %H:%M:%S")
      - message_preview: str
      - latency_ms: int
      - cost_usd: float
      - mock: bool
      - optional: prompt/response/steps/metrics/metadata/session_id/etc.
    """

    def _collection(self):
        db = get_db()
        return db[get_traces_collection_name()]

    async def ensure_indexes(self) -> None:
        """
        Ensure indexes used by our queries.
        Safe to call multiple times.
        """
        try:
            col = self._collection()
            await col.create_index("trace_id", unique=True)
            await col.create_index([("created_at", -1)])
            logger.info("TraceRepo indexes ensured")
        except PyMongoError:
            logger.exception("Failed to create Mongo indexes for traces")
            raise
        except Exception:
            logger.exception("Unexpected error while ensuring trace indexes")
            raise

    @staticmethod
    def _normalize_trace_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Minimal normalization to keep schema flexible but consistent.
        """
        trace_id = str(doc.get("trace_id", "")).strip()
        if not trace_id:
            raise ValueError("Trace document must include non-empty 'trace_id'")

        if not doc.get("created_at"):
            doc["created_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if "message_preview" in doc and doc["message_preview"] is not None:
            doc["message_preview"] = str(doc["message_preview"])[:200]

        return doc

    async def upsert_trace(self, doc: Dict[str, Any]) -> None:
        """
        Upsert a trace by trace_id.
        This avoids duplicate-key failures in demo / retry scenarios.
        """
        try:
            col = self._collection()
            doc = self._normalize_trace_doc(doc)
            trace_id = doc["trace_id"]

            result = await col.update_one(
                {"trace_id": trace_id},
                {"$set": doc},
                upsert=True,
            )

            logger.info(
                "Upserted trace",
                extra={
                    "trace_id": trace_id,
                    "matched": result.matched_count,
                    "modified": result.modified_count,
                    "upserted_id": str(result.upserted_id) if result.upserted_id else None,
                },
            )
        except ValueError:
            logger.exception("Validation error in upsert_trace")
            raise
        except PyMongoError:
            logger.exception("Mongo error in upsert_trace")
            raise
        except Exception:
            logger.exception("Unexpected error in upsert_trace")
            raise

    async def insert_trace(self, doc: Dict[str, Any]) -> None:
        """
        Insert one trace document.

        NOTE:
        To keep the system resilient during demos/retries,
        this delegates to upsert_trace().
        """
        await self.upsert_trace(doc)

    async def list_latest_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List latest traces, sorted by created_at desc.
        Returns documents without Mongo _id.
        """
        try:
            col = self._collection()
            cursor = col.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            logger.info("Listed latest traces", extra={"count": len(docs), "limit": limit})
            return docs
        except PyMongoError:
            logger.exception("Mongo error in list_latest_traces")
            raise
        except Exception:
            logger.exception("Unexpected error in list_latest_traces")
            raise

    async def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single trace by trace_id (business id).
        Returns None if not found.
        """
        try:
            col = self._collection()
            doc = await col.find_one({"trace_id": trace_id}, {"_id": 0})
            logger.info("Fetched trace by id", extra={"trace_id": trace_id, "found": bool(doc)})
            return doc
        except PyMongoError:
            logger.exception("Mongo error in get_trace_by_id")
            raise
        except Exception:
            logger.exception("Unexpected error in get_trace_by_id")
            raise

    async def delete_all_traces_for_demo(self) -> int:
        """
        Danger: wipes the traces collection.
        Keep this repo-only; if we expose an endpoint later, we’ll protect it.

        Returns number of deleted docs.
        """
        try:
            col = self._collection()
            result = await col.delete_many({})
            logger.warning("Deleted all traces for demo reset", extra={"deleted": result.deleted_count})
            return int(result.deleted_count)
        except PyMongoError:
            logger.exception("Mongo error in delete_all_traces_for_demo")
            raise
        except Exception:
            logger.exception("Unexpected error in delete_all_traces_for_demo")
            raise
