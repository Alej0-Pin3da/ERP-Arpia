import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings


def generate_refresh_token() -> tuple[str, str]:
    """Return (plain_token, token_hash).

    The plain token is returned to the client exactly once. Only the SHA-256
    hash is ever persisted, so a database leak does not expose usable tokens.
    """
    token = secrets.token_urlsafe(48)
    return token, hash_refresh_token(token)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
