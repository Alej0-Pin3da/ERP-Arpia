import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
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
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    stmt = select(Usuario).where(Usuario.email == payload.email)
    user = db.scalar(stmt)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_token(db, user)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)
    )
    record = db.scalar(stmt)
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    now = dt.datetime.now(dt.timezone.utc)
    if record.revocado_en is not None:
        # A revoked token being reused means the token (or its rotation chain)
        # was captured. Revoke every active token for this user to contain the
        # compromise, then reject the request.
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
        record.revocado_en = dt.datetime.now(dt.timezone.utc)
        db.commit()


@router.get("/me", response_model=UsuarioRead)
def me(user: Usuario = Depends(get_current_user)) -> Usuario:
    return user
