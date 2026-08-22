"""Security headers middleware for FastAPI."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app, csp_policy: str | None = None):
        super().__init__(app)
        self.csp_policy = csp_policy or self._default_csp_policy()
        self._is_production = settings.ENVIRONMENT in ("production", "staging")

    def _default_csp_policy(self) -> str:
        """Default Content Security Policy."""
        return (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "  # unsafe-inline for PrimeVue inline styles
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (restrict dangerous features)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=()"
        )

        # HSTS - only in production/staging with HTTPS
        if self._is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # X-Frame-Options (additional clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection (legacy but harmless)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response