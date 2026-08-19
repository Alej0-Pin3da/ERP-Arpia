import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.limiter import limiter
from app.core.logging_config import setup_logging
from app.core.logging_middleware import RequestContextMiddleware
from app.db.session import engine
from app.models import Base  # noqa: F401  # ensure all models are registered

setup_logging()

logger = logging.getLogger("arpia.api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(DomainError)
def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception processing request %s %s",
        request.method,
        request.url,
        exc_info=exc,
        extra={"request_id": getattr(request.state, "request_id", None)},
    )
    if settings.ENVIRONMENT in ("production", "staging"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor. Intente nuevamente más tarde."},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


def _database_is_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


@app.get("/health/live", tags=["health"])
def health_live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def health_ready() -> dict:
    if not _database_is_ready():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "error"},
        )
    return {"status": "ok", "database": "ok"}


@app.get("/health", tags=["health"])
def health() -> dict:
    """Backward-compatible alias for the readiness check."""
    if not _database_is_ready():
        return {"status": "ok", "database": "error"}
    return {"status": "ok", "database": "ok"}
