from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
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


class SystemStatsResponse(BaseModel):
    """Aggregated system statistics."""
    total_requests: int
    total_cache_hits: int
    total_cache_misses: int
    cache_hit_rate: float
    avg_latency_ms: int
    total_time_saved_ms: int
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


def _mock_system_stats() -> SystemStatsResponse:
    """Mock aggregated statistics."""
    return SystemStatsResponse(
        total_requests=150,
        total_cache_hits=45,
        total_cache_misses=105,
        cache_hit_rate=30.0,
        avg_latency_ms=850,
        total_time_saved_ms=54000,  # 45 hits * 1200ms average
        source="mock",
    )


def _mock_export_data() -> List[Dict[str, Any]]:
    """Generate mock export data."""
    now = datetime.utcnow()
    data = []
    
    for i in range(10):
        data.append({
            "trace_id": f"trace_{uuid4()}",
            "created_at": (now - timedelta(minutes=i * 4)).strftime("%Y-%m-%d %H:%M:%S"),
            "message_preview": "Explain this concept simply...",
            "latency_ms": 650 + (i * 90),
            "cost_usd": round(0.0015 + (i * 0.0004), 4),
            "mock": True,
            "cache_hit": i % 3 == 0,  # Every 3rd is cache hit
            "cache_saved_ms": 1200 if i % 3 == 0 else 0,
            "provider": "mock",
        })
    
    return data


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


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats() -> SystemStatsResponse:
    """
    GET /stats
    
    Returns aggregated system statistics:
    - Total requests
    - Cache hit rate
    - Average latency
    - Time saved from caching
    """
    settings = get_settings()
    
    if not settings.mongodb_uri:
        logger.info("GET /stats -> mock (MONGODB_URI not set)")
        return _mock_system_stats()
    
    try:
        # Fetch all traces from MongoDB
        all_traces = await trace_repo.list_latest_traces(limit=1000)
        
        if not all_traces:
            logger.info("GET /stats -> no traces, returning zeros")
            return SystemStatsResponse(
                total_requests=0,
                total_cache_hits=0,
                total_cache_misses=0,
                cache_hit_rate=0.0,
                avg_latency_ms=0,
                total_time_saved_ms=0,
                source="mongo",
            )
        
        # Calculate stats
        total_requests = len(all_traces)
        cache_hits = sum(1 for t in all_traces if t.get("cache_hit", False))
        cache_misses = total_requests - cache_hits
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        # Average latency
        total_latency = sum(t.get("latency_ms", 0) for t in all_traces)
        avg_latency_ms = int(total_latency / total_requests) if total_requests > 0 else 0
        
        # Total time saved (sum of all cache_saved_ms)
        total_time_saved_ms = sum(t.get("cache_saved_ms", 0) for t in all_traces)
        
        logger.info(
            "GET /stats -> mongo",
            extra={
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "cache_hit_rate": cache_hit_rate,
            },
        )
        
        return SystemStatsResponse(
            total_requests=total_requests,
            total_cache_hits=cache_hits,
            total_cache_misses=cache_misses,
            cache_hit_rate=round(cache_hit_rate, 2),
            avg_latency_ms=avg_latency_ms,
            total_time_saved_ms=total_time_saved_ms,
            source="mongo",
        )
    
    except RuntimeError:
        logger.warning("GET /stats -> mock (Mongo not initialized)")
        return _mock_system_stats()
    except Exception as e:
        logger.exception("Unhandled error in GET /stats")
        raise HTTPException(status_code=500, detail="Failed to fetch stats") from e


@router.get("/export")
async def export_traces(
    format: str = Query(default="json", regex="^(json|csv)$", description="Export format: json or csv"),
):
    """
    GET /export?format=json|csv
    
    Export all traces as JSON or CSV file.
    Returns downloadable file with timestamp in filename.
    """
    settings = get_settings()
    
    # Fetch all traces
    if not settings.mongodb_uri:
        logger.info("GET /export -> using mock data")
        all_traces = _mock_export_data()
        source = "mock"
    else:
        try:
            all_traces = await trace_repo.list_latest_traces(limit=1000)
            source = "mongo"
            logger.info(f"GET /export -> fetched {len(all_traces)} traces from MongoDB")
        except Exception:
            logger.warning("GET /export -> MongoDB unavailable, using mock data")
            all_traces = _mock_export_data()
            source = "mock"
    
    if not all_traces:
        raise HTTPException(status_code=404, detail="No traces available to export")
    
    # Generate timestamp for filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # JSON Export
    if format == "json":
        json_data = json.dumps(all_traces, indent=2, default=str)
        
        return StreamingResponse(
            iter([json_data]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=llm_traces_{timestamp}.json",
                "X-Source": source,
            }
        )
    
    # CSV Export
    elif format == "csv":
        # Create CSV in memory
        output = io.StringIO()
        
        # Define CSV columns
        fieldnames = [
            "trace_id",
            "created_at",
            "message_preview",
            "latency_ms",
            "cost_usd",
            "cache_hit",
            "cache_saved_ms",
            "provider",
            "mock",
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        # Write rows
        for trace in all_traces:
            writer.writerow({
                "trace_id": trace.get("trace_id", ""),
                "created_at": trace.get("created_at", ""),
                "message_preview": trace.get("message_preview", "")[:100],  # Truncate for CSV
                "latency_ms": trace.get("latency_ms", 0),
                "cost_usd": trace.get("cost_usd", 0.0),
                "cache_hit": trace.get("cache_hit", False),
                "cache_saved_ms": trace.get("cache_saved_ms", 0),
                "provider": trace.get("provider", "unknown"),
                "mock": trace.get("mock", False),
            })
        
        csv_data = output.getvalue()
        output.close()
        
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=llm_traces_{timestamp}.csv",
                "X-Source": source,
            }
        )
