"""Idempotency key middleware for critical POST endpoints.

Ensures that retries with the same Idempotency-Key return the same response
without executing the operation twice. Uses Redis for distributed storage
with automatic TTL expiration.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Callable, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger("arpia.idempotency")

# Critical endpoints that require idempotency keys
IDEMPOTENT_ENDPOINTS = {
    "/api/v1/ventas",
    "/api/v1/devoluciones",
    "/api/v1/compras",
    "/api/v1/finanzas/movimientos",
    "/api/v1/inventario/ajustes",
}

# Methods that should be idempotent
IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}

# Redis key prefix
IDEMPOTENCY_PREFIX = "idempotency:"

# Default TTL: 24 hours
IDEMPOTENCY_TTL = 86400


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware to handle Idempotency-Key header for critical endpoints."""

    def __init__(
        self,
        app: ASGIApp,
        redis_client: Optional[object] = None,
        ttl: int = IDEMPOTENCY_TTL,
    ):
        super().__init__(app)
        self.redis = redis_client
        self.ttl = ttl
        self._memory_store: dict[str, tuple[bytes, int]] = {}  # Fallback for tests

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this endpoint requires idempotency
        if not self._requires_idempotency(request):
            return await call_next(request)

        # Get idempotency key from header
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Idempotency-Key header is required for this endpoint",
                    "error_code": "IDEMPOTENCY_KEY_MISSING",
                },
            )

        # Validate key format (UUID or similar)
        if not self._is_valid_key(idempotency_key):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Invalid Idempotency-Key format",
                    "error_code": "IDEMPOTENCY_KEY_INVALID",
                },
            )

        # Build storage key
        storage_key = f"{IDEMPOTENCY_PREFIX}{idempotency_key}"

        # Check if we have a cached response
        cached = await self._get_cached_response(storage_key)
        if cached:
            response_body, response_status, response_headers = cached
            logger.info(
                "Idempotent response returned",
                extra={
                    "idempotency_key": idempotency_key,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            response = Response(
                content=response_body,
                status_code=response_status,
                headers=response_headers,
                media_type="application/json",
            )
            response.headers["Idempotency-Key"] = idempotency_key
            return response

        # Execute the request
        response = await call_next(request)

        # Only cache successful responses (2xx)
        if 200 <= response.status_code < 300:
            await self._cache_response(storage_key, response)

        # Add idempotency key to response headers
        response.headers["Idempotency-Key"] = idempotency_key

        return response

    def _requires_idempotency(self, request: Request) -> bool:
        """Check if this request requires idempotency handling."""
        path = request.url.path
        method = request.method

        # Check if path matches any critical endpoint
        for endpoint in IDEMPOTENT_ENDPOINTS:
            if path.startswith(endpoint) and method in IDEMPOTENT_METHODS:
                return True
        return False

    def _is_valid_key(self, key: str) -> bool:
        """Validate idempotency key format."""
        # Accept UUID-like keys (at least 16 chars, alphanumeric + dash/underscore)
        if len(key) < 16 or len(key) > 128:
            return False
        # Basic validation - alphanumeric, dash, underscore
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", key))

    async def _get_cached_response(self, key: str) -> Optional[tuple[bytes, int, dict]]:
        """Get cached response from Redis or memory fallback."""
        try:
            if self.redis:
                data = await self.redis.get(key)
                if data:
                    cached = json.loads(data)
                    return (
                        cached["body"].encode("utf-8"),
                        cached["status"],
                        cached["headers"],
                    )
            else:
                # Memory fallback
                if key in self._memory_store:
                    body, status_code = self._memory_store[key]
                    return (body, status_code, {"content-type": "application/json"})
        except Exception as e:
            logger.warning(f"Failed to get cached idempotency response: {e}")
        return None

    async def _cache_response(self, key: str, response: Response) -> None:
        """Cache response in Redis or memory fallback."""
        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Re-create response body iterator for actual response
            response.body_iterator = self._make_async_iterator(body)

            if self.redis:
                cached = {
                    "body": body.decode("utf-8"),
                    "status": response.status_code,
                    "headers": dict(response.headers),
                }
                await self.redis.setex(key, self.ttl, json.dumps(cached))
            else:
                # Memory fallback
                self._memory_store[key] = (body, response.status_code)
        except Exception as e:
            logger.warning(f"Failed to cache idempotency response: {e}")

    async def _make_async_iterator(self, body: bytes):
        """Create async iterator from bytes."""
        yield body


def create_idempotency_middleware() -> type[IdempotencyMiddleware]:
    """Create IdempotencyMiddleware class with Redis client configured.
    
    This factory creates a middleware class that can be used with
    app.add_middleware(). The Redis client is initialized at class creation time.
    """
    redis_client = None
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(
            getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
            encoding="utf-8",
            decode_responses=True,
        )
    except Exception:
        logger.info("Redis not available for idempotency, using in-memory fallback")

    class ConfiguredIdempotencyMiddleware(IdempotencyMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(app, redis_client=redis_client)

    return ConfiguredIdempotencyMiddleware