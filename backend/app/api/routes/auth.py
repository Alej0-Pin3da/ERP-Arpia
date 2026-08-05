from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
from app.models.usuarios import Usuario
from app.schemas.auth import LoginRequest, Token
from app.schemas.usuario import UsuarioRead

router = APIRouter(prefix="/auth", tags=["auth"])


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
    token = create_access_token(subject=str(user.id), rol=user.rol)
    return Token(access_token=token, rol=user.rol)


@router.get("/me", response_model=UsuarioRead)
def me(user: Usuario = Depends(get_current_user)) -> Usuario:
    return user