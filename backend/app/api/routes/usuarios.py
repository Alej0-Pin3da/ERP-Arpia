from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.core.password_policy import validate_password_strength
from app.core.security import hash_password, verify_password
from app.models.usuarios import Usuario
from app.schemas.common import Paginated
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.services.paginacion import paginar

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=Paginated[UsuarioRead])
def list_usuarios(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    rol: Literal["admin", "operador", "consulta"] | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    stmt = select(Usuario).order_by(Usuario.id)
    if q is not None:
        stmt = stmt.where(
            or_(
                Usuario.nombre.ilike(f"%{q}%"),
                Usuario.email.ilike(f"%{q}%"),
            )
        )
    if rol is not None:
        stmt = stmt.where(Usuario.rol == rol)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[UsuarioRead](items=list(rows), total=total)


@router.get("/{usuario_id}", response_model=UsuarioRead)
def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return usuario


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def create_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    existing = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    data = payload.model_dump(exclude={"password"})
    usuario = Usuario(**data, password_hash=hash_password(payload.password))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioRead)
def update_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    if usuario.id == current_admin.id and payload.rol not in (None, "admin"):
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role away from admin",
        )
    changes = payload.model_dump(exclude_unset=True)
    password = changes.pop("password", None)
    for field, value in changes.items():
        setattr(usuario, field, value)
    if password is not None:
        usuario.password_hash = hash_password(password)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(require_admin),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    if usuario.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own user")
    db.delete(usuario)
    db.commit()


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


@router.patch("/{usuario_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    usuario_id: int,
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    """Change user password with strength validation.

    Admins can change any user's password. Users can only change their own
    password (via /auth/me/password endpoint in future).
    """
    # Admin can change any password, but for security we verify current password
    # only when changing own password. For admin changing others, skip verification.
    target_user = db.get(Usuario, usuario_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="Usuario not found")

    # If admin is changing someone else's password, don't require current password
    # If changing own password, verify current password
    if target_user.id == current_user.id:
        if not verify_password(payload.current_password, target_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta",
            )

    # Validate new password strength
    try:
        validate_password_strength(payload.new_password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    target_user.password_hash = hash_password(payload.new_password)
    db.commit()
