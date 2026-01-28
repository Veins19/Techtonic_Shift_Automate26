from __future__ import annotations

import logging
import time
from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.config import get_settings
from backend.repositories.trace_repo import TraceRepo
from backend.services.llm_provider import GeminiLLMProvider, LLMProviderError
from backend.services.semantic_cache import SemanticCache

logger = logging.getLogger("backend.routes.chat")

router = APIRouter(tags=["chat"])

# Lightweight singletons
trace_repo = TraceRepo()
semantic_cache = SemanticCache()


class ChatRequest(BaseModel):
    """
    Incoming user chat request.
    """
    message: str = Field(..., min_length=1, description="User message")
    stream: bool = Field(default=False, description="Enable streaming response")
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier for grouping conversations",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional client metadata (ui version, user id, etc.)",
    )


class ChatResponse(BaseModel):
    """
    Outgoing response.
    """
    trace_id: str
    reply: str
    mock: bool
    latency_ms: int


def _mock_llm_reply(user_message: str) -> str:
    """
    Deterministic mock reply so demos are stable.
    """
    trimmed = user_message.strip()
    if not trimmed:
        return "Please send a message."
    
    return (
        "✅ [MOCK MODE]\n\n"
        f"You said: {trimmed}\n\n"
        "This is a placeholder response. Once the LLM provider is wired, "
        "this will contain the real model output."
    )


async def _stream_generator(prompt: str, trace_id: str):
    """
    Generator for streaming responses.
    Yields Server-Sent Events (SSE) format.
    """
    settings = get_settings()
    
    try:
        if settings.use_mock_llm:
            # Mock streaming - simulate word-by-word
            import asyncio
            words = _mock_llm_reply(prompt).split()
            for word in words:
                yield f"data: {word} \n\n"
                await asyncio.sleep(0.05)  # Simulate delay
            yield "data: [DONE]\n\n"
        else:
            # Real Gemini streaming
            llm = GeminiLLMProvider()
            async for chunk in llm.generate_stream(prompt):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
    except Exception as e:
        logger.exception("Streaming error", extra={"trace_id": trace_id})
        yield f"data: [ERROR: {str(e)}]\n\n"


@router.post("/chat")
async def chat(req: ChatRequest):
    """
    POST /chat
    Final behavior:
    - Mock or Gemini LLM
    - Streaming or non-streaming
    - Semantic cache (exact match)
    - Trace persistence (non-blocking)
    """
    settings = get_settings()
    trace_id = f"trace_{uuid4()}"
    start = time.perf_counter()

    try:
        logger.info(
            "Received /chat request",
            extra={
                "trace_id": trace_id,
                "session_id": req.session_id,
                "mock": settings.use_mock_llm,
                "stream": req.stream,
            },
        )

        if not req.message or not req.message.strip():
            raise HTTPException(status_code=400, detail="message is required")

        # ----------------------------
        # STREAMING MODE
        # ----------------------------
        if req.stream:
            return StreamingResponse(
                _stream_generator(req.message, trace_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Trace-ID": trace_id,
                },
            )

        # ----------------------------
        # NON-STREAMING MODE
        # ----------------------------
        
        # MOCK MODE
        if settings.use_mock_llm:
            reply_text = _mock_llm_reply(req.message)
            provider = "mock"

        # REAL LLM MODE (Gemini)
        else:
            provider = "gemini"
            
            # 1️⃣ Check semantic cache
            cached = await semantic_cache.get(req.message)
            if cached:
                reply_text = cached.get("response_text", "")
                logger.info(
                    "Reply served from semantic cache",
                    extra={"trace_id": trace_id},
                )
            else:
                # 2️⃣ Call Gemini
                llm = GeminiLLMProvider()
                result = await llm.generate(req.message)
                reply_text = result["text"]
                
                # 3️⃣ Store in cache (best-effort)
                await semantic_cache.set(
                    prompt=req.message,
                    response_text=reply_text,
                    metadata={"provider": provider},
                )

        latency_ms = int((time.perf_counter() - start) * 1000)

        # ----------------------------
        # Trace document
        # ----------------------------
        trace_doc: Dict[str, Any] = {
            "trace_id": trace_id,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "message_preview": req.message.strip()[:200],
            "latency_ms": latency_ms,
            "cost_usd": 0.0,
            "mock": settings.use_mock_llm,
            "provider": provider,
            "session_id": req.session_id,
            "metadata": req.metadata or {},
            "steps": [
                {
                    "name": provider,
                    "status": "success",
                    "latency_ms": latency_ms,
                }
            ],
        }

        # ----------------------------
        # Persist trace (non-blocking)
        # ----------------------------
        if settings.mongodb_uri:
            try:
                await trace_repo.ensure_indexes()
                await trace_repo.insert_trace(trace_doc)
            except Exception:
                logger.exception(
                    "Trace persistence failed (request not aborted)",
                    extra={"trace_id": trace_id},
                )

        logger.info(
            "Responding from /chat",
            extra={
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "provider": provider,
            },
        )

        return ChatResponse(
            trace_id=trace_id,
            reply=reply_text,
            mock=settings.use_mock_llm,
            latency_ms=latency_ms,
        )

    except LLMProviderError as e:
        logger.exception("LLM provider failure", extra={"trace_id": trace_id})
        raise HTTPException(status_code=502, detail=str(e)) from e
    except HTTPException:
        logger.exception("HTTP error in /chat", extra={"trace_id": trace_id})
        raise
    except Exception as e:
        logger.exception("Unhandled error in /chat", extra={"trace_id": trace_id})
        raise HTTPException(status_code=500, detail="Internal server error") from e
