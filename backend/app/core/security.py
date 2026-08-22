import datetime as dt

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_bcrypt(password: str) -> str:
    # bcrypt 72 bytes limit — passlib with bcrypt 4.1+ raises ValueError otherwise
    b = password.encode("utf-8")
    if len(b) > 72:
        b = b[:72]
        # avoid cutting mid-utf8 sequence
        while True:
            try:
                return b.decode("utf-8")
            except UnicodeDecodeError:
                b = b[:-1]
    return password


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_bcrypt(password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(_truncate_bcrypt(plain_password), password_hash)


def create_access_token(
    subject: str,
    rol: str | None = None,
    expires_delta: dt.timedelta | None = None,
) -> str:
    now = dt.datetime.now(dt.UTC)
    expire = now + (
        expires_delta
        if expires_delta
        else dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
    }
    if rol:
        payload["rol"] = rol
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
