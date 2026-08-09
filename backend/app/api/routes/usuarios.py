from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.core.security import hash_password
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