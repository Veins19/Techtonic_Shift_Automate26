from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from backend.config import get_settings

logger = logging.getLogger("backend.middleware.rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.

    Limits:
    - Requests per minute (RPM)
    - Requests per day (RPD)

    Scope:
    - Per client IP (best-effort, suitable for hackathon / single-node deploys)

    Notes:
    - This is NOT distributed-safe (no Redis yet)
    - Designed to fail OPEN (never crash API)
    """

    def __init__(self, app) -> None:
        super().__init__(app)

        settings = get_settings()
        self.max_rpm = settings.max_rpm
        self.max_rpd = settings.max_rpd

        # Per-IP sliding windows
        self._minute_buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self._day_buckets: Dict[str, Deque[float]] = defaultdict(deque)

        logger.info(
            "RateLimitMiddleware initialized",
            extra={
                "MAX_RPM": self.max_rpm,
                "MAX_RPD": self.max_rpd,
            },
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Intercepts every HTTP request and enforces rate limits.
        """
        try:
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()

            minute_window = 60
            day_window = 24 * 60 * 60

            minute_bucket = self._minute_buckets[client_ip]
            day_bucket = self._day_buckets[client_ip]

            # Clean old timestamps
            while minute_bucket and minute_bucket[0] <= now - minute_window:
                minute_bucket.popleft()

            while day_bucket and day_bucket[0] <= now - day_window:
                day_bucket.popleft()

            # Check limits
            if len(minute_bucket) >= self.max_rpm:
                logger.warning(
                    "Rate limit exceeded (RPM)",
                    extra={"ip": client_ip, "count": len(minute_bucket)},
                )
                return Response(
                    content="Rate limit exceeded: too many requests per minute",
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                )

            if len(day_bucket) >= self.max_rpd:
                logger.warning(
                    "Rate limit exceeded (RPD)",
                    extra={"ip": client_ip, "count": len(day_bucket)},
                )
                return Response(
                    content="Rate limit exceeded: too many requests per day",
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                )

            # Record request
            minute_bucket.append(now)
            day_bucket.append(now)

            return await call_next(request)

        except Exception:
            # NEVER block traffic due to limiter bugs
            logger.exception("Rate limiting failed unexpectedly; allowing request")
            return await call_next(request)
