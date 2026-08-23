import datetime as dt
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.limiter import limiter
from app.core.login_tracker import LoginAttemptTracker
from app.core.refresh import (
    generate_refresh_token,
    hash_refresh_token,
    refresh_expiry,
)
from app.core.security import create_access_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.usuarios import Usuario
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.schemas.usuario import UsuarioRead

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger("arpia.auth")


def _issue_token(db: Session, user: Usuario) -> Token:
    """Create an access token plus a new persisted refresh token."""
    access = create_access_token(subject=str(user.id), rol=user.rol)
    plain, token_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            usuario_id=user.id,
            token_hash=token_hash,
            expira_en=refresh_expiry(),
        )
    )
    db.commit()
    return Token(access_token=access, refresh_token=plain, rol=user.rol)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    client_ip = get_remote_address(request)

    # Check lockout before attempting login
    locked, remaining = LoginAttemptTracker.is_locked_out(payload.email, client_ip)
    if locked:
        logger.warning(
            "Login attempt on locked account",
            extra={
                "email": payload.email,
                "ip": client_ip,
                "remaining_seconds": remaining,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intente nuevamente en {remaining} segundos.",
        )

    stmt = select(Usuario).where(Usuario.email == payload.email)
    user = db.scalar(stmt)
    if user is None or not verify_password(payload.password, user.password_hash):
        # Record failed attempt
        attempt_count = LoginAttemptTracker.record_failure(payload.email, client_ip)
        logger.warning(
            "Failed login attempt",
            extra={
                "email": payload.email,
                "ip": client_ip,
                "attempt_count": attempt_count,
                "max_attempts": LoginAttemptTracker.max_attempts,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful login - clear failed attempts
    LoginAttemptTracker.record_success(payload.email, client_ip)
    return _issue_token(db, user)


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)
    )
    record = db.scalar(stmt)
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    now = dt.datetime.now(dt.UTC)
    if record.revocado_en is not None:
        # A revoked token being reused means the token (or its rotation chain)
        # was captured. Revoke every active token for this user to contain the
        # compromise, then reject the request.
        logger.warning(
            "Refresh token reuse detected - possible token theft",
            extra={
                "usuario_id": record.usuario_id,
                "token_id": record.id,
                "original_revoked_at": record.revocado_en.isoformat()
                if record.revocado_en
                else None,
                "reuse_attempt_at": now.isoformat(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        for other in db.scalars(
            select(RefreshToken).where(RefreshToken.usuario_id == record.usuario_id)
        ).all():
            other.revocado_en = now
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token already revoked")
    if record.expira_en <= now:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    user = db.get(Usuario, record.usuario_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    record.revocado_en = now
    db.commit()
    return _issue_token(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)
    )
    record = db.scalar(stmt)
    if record is not None and record.revocado_en is None:
        record.revocado_en = dt.datetime.now(dt.UTC)
        db.commit()


@router.get("/me", response_model=UsuarioRead)
def me(user: Usuario = Depends(get_current_user)) -> Usuario:
    return user
