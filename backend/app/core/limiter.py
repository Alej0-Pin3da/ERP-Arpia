"""Rate limiting configuration with per-user/IP/endpoint policies."""

from functools import lru_cache

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _get_user_id_or_ip(request) -> str:
    """Key function: use user ID if authenticated, otherwise IP."""
    # Try to get user from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


# Global limiter (IP-based, disabled in test)
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.ENVIRONMENT != "test",
)

# Per-user/IP limiter for authenticated endpoints
user_limiter = Limiter(
    key_func=_get_user_id_or_ip,
    enabled=settings.ENVIRONMENT != "test",
)


@lru_cache
def get_rate_limit_config() -> dict:
    """Get rate limit configuration per environment."""
    if settings.ENVIRONMENT in ("production", "staging"):
        return {
            "auth_login": "10/minute",
            "auth_refresh": "20/minute",
            "api_write": "100/minute",  # POST/PUT/PATCH/DELETE
            "api_read": "300/minute",  # GET
            # ventas, devoluciones, compras, finanzas, stock adjustments
            "critical_write": "30/minute",
        }
    elif settings.ENVIRONMENT == "development":
        return {
            "auth_login": "30/minute",
            "auth_refresh": "60/minute",
            "api_write": "300/minute",
            "api_read": "1000/minute",
            "critical_write": "100/minute",
        }
    else:  # test
        return {
            "auth_login": "1000/minute",
            "auth_refresh": "1000/minute",
            "api_write": "10000/minute",
            "api_read": "10000/minute",
            "critical_write": "10000/minute",
        }
