from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from backend.config import get_settings
from backend.repositories.trace_repo import TraceRepo

logger = logging.getLogger("backend.routes.monitor")

router = APIRouter(tags=["monitor"])
trace_repo = TraceRepo()

# ----------------------------------
# Response models
# ----------------------------------

class TraceSummary(BaseModel):
    trace_id: str
    created_at: str
    message_preview: str
    latency_ms: int
    cost_usd: float
    mock: bool

class TraceListResponse(BaseModel):
    items: List[TraceSummary]
    source: str = Field(..., description="mongo | mock")
    count: int
    page: int
    limit: int

class TraceDetailResponse(BaseModel):
    trace: Dict[str, Any]
    source: str = Field(..., description="mongo | mock")

# ----------------------------------
# Mock helpers
# ----------------------------------

def _mock_traces(limit: int, page: int) -> TraceListResponse:
    now = datetime.utcnow()
    items: List[TraceSummary] = []

    start = (page - 1) * limit
    end = start + limit

    for i in range(start, end):
        items.append(
            TraceSummary(
                trace_id=f"trace_{uuid4()}",
                created_at=(now - timedelta(minutes=i * 4)).strftime("%Y-%m-%d %H:%M:%S"),
                message_preview="Explain this concept simply...",
                latency_ms=650 + (i * 90),
                cost_usd=round(0.0015 + (i * 0.0004), 4),
                mock=True,
            )
        )

    return TraceListResponse(
        items=items,
        source="mock",
        count=len(items),
        page=page,
        limit=limit,
    )

def _mock_trace_detail(trace_id: str) -> TraceDetailResponse:
    trace = {
        "trace_id": trace_id,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "message_preview": "Explain this concept simply...",
        "latency_ms": 910,
        "cost_usd": 0.0021,
        "mock": True,
        "steps": [
            {"name": "retrieval", "status": "success", "latency_ms": 140},
            {"name": "prompt_build", "status": "success", "latency_ms": 90},
            {"name": "generation", "status": "success", "latency_ms": 620},
            {"name": "metrics", "status": "success", "latency_ms": 60},
        ],
    }
    return TraceDetailResponse(trace=trace, source="mock")

# ----------------------------------
# Routes
# ----------------------------------

@router.get("/traces", response_model=TraceListResponse)
async def list_traces(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    limit: int = Query(default=20, ge=1, le=200, description="Items per page"),
    mock: Optional[bool] = Query(default=None),
    provider: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
) -> TraceListResponse:
    """
    GET /traces

    Supports:
    - Pagination (page, limit)
    - Filtering (mock, provider, session_id)

    Behavior:
    - Mongo unavailable -> mock data
    - Mongo errors -> 500
    """
    settings = get_settings()

    if not settings.mongodb_uri:
        logger.info("GET /traces -> mock (MONGODB_URI not set)")
        return _mock_traces(limit=limit, page=page)

    try:
        skip = (page - 1) * limit
        docs = await trace_repo.list_latest_traces(limit=skip + limit)

        # Apply filtering at route layer (safe + explicit)
        filtered: List[Dict[str, Any]] = []
        for d in docs:
            if mock is not None and bool(d.get("mock")) != mock:
                continue
            if provider and d.get("provider") != provider:
                continue
            if session_id and d.get("session_id") != session_id:
                continue
            filtered.append(d)

        paged = filtered[skip : skip + limit]

        items = [
            TraceSummary(
                trace_id=str(d.get("trace_id", "")),
                created_at=str(d.get("created_at", "")),
                message_preview=str(d.get("message_preview", ""))[:200],
                latency_ms=int(d.get("latency_ms", 0)),
                cost_usd=float(d.get("cost_usd", 0.0)),
                mock=bool(d.get("mock", False)),
            )
            for d in paged
        ]

        logger.info(
            "GET /traces -> mongo",
            extra={
                "page": page,
                "limit": limit,
                "returned": len(items),
            },
        )

        return TraceListResponse(
            items=items,
            source="mongo",
            count=len(items),
            page=page,
            limit=limit,
        )

    except RuntimeError:
        logger.warning("GET /traces -> mock (Mongo not initialized)")
        return _mock_traces(limit=limit, page=page)

    except Exception as e:
        logger.exception("Unhandled error in GET /traces")
        raise HTTPException(status_code=500, detail="Failed to fetch traces") from e

@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(
    trace_id: str = Path(..., description="Trace ID returned by POST /chat"),
) -> TraceDetailResponse:
    """
    GET /traces/{trace_id}
    """
    settings = get_settings()

    if not settings.mongodb_uri:
        logger.info("GET /traces/{trace_id} -> mock", extra={"trace_id": trace_id})
        return _mock_trace_detail(trace_id)

    try:
        doc = await trace_repo.get_trace_by_id(trace_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Trace not found")

        logger.info("GET /traces/{trace_id} -> mongo", extra={"trace_id": trace_id})
        return TraceDetailResponse(trace=doc, source="mongo")

    except RuntimeError:
        logger.warning("GET /traces/{trace_id} -> mock (Mongo not initialized)")
        return _mock_trace_detail(trace_id)

    except HTTPException:
        logger.exception("HTTP error in GET /traces/{trace_id}")
        raise

    except Exception as e:
        logger.exception("Unhandled error in GET /traces/{trace_id}")
        raise HTTPException(status_code=500, detail="Failed to fetch trace") from e
