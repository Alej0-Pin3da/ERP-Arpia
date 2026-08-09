from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.productos import TipoProducto
from app.schemas.common import Paginated
from app.schemas.producto import TipoProductoCreate, TipoProductoRead, TipoProductoUpdate
from app.services.paginacion import paginar

router = APIRouter(prefix="/tipos-producto", tags=["tipos-producto"])

audited_user = require_roles("admin", "operador", "consulta")


@router.get("", response_model=Paginated[TipoProductoRead])
def list_tipos_producto(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(audited_user),
):
    stmt = select(TipoProducto).order_by(TipoProducto.id)
    if q is not None:
        stmt = stmt.where(TipoProducto.nombre.ilike(f"%{q}%"))
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[TipoProductoRead](items=list(rows), total=total)


@router.get("/{tipo_producto_id}", response_model=TipoProductoRead)
def get_tipo_producto(
    tipo_producto_id: int,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(audited_user),
):
    tipo = db.get(TipoProducto, tipo_producto_id)
    if tipo is None:
        raise HTTPException(status_code=404, detail="TipoProducto not found")
    return tipo


@router.post("", response_model=TipoProductoRead, status_code=status.HTTP_201_CREATED)
def create_tipo_producto(
    payload: TipoProductoCreate,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(require_admin),
):
    tipo = TipoProducto(**payload.model_dump())
    db.add(tipo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="TipoProducto name already exists"
        )
    db.refresh(tipo)
    return tipo


@router.put("/{tipo_producto_id}", response_model=TipoProductoRead)
def update_tipo_producto(
    tipo_producto_id: int,
    payload: TipoProductoUpdate,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(require_admin),
):
    tipo = db.get(TipoProducto, tipo_producto_id)
    if tipo is None:
        raise HTTPException(status_code=404, detail="TipoProducto not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tipo, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="TipoProducto name already exists"
        )
    db.refresh(tipo)
    return tipo


@router.delete("/{tipo_producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_producto(
    tipo_producto_id: int,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(require_admin),
):
    tipo = db.get(TipoProducto, tipo_producto_id)
    if tipo is None:
        raise HTTPException(status_code=404, detail="TipoProducto not found")
    db.delete(tipo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="TipoProducto is in use and cannot be deleted"
        )
