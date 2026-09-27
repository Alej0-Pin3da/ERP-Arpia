"""Service layer for TipoProducto CRUD."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.productos import TipoProducto
from app.schemas.producto import TipoProductoCreate, TipoProductoUpdate
from app.services.paginacion import paginar


def listar_tipos_producto(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
) -> tuple[list[TipoProducto], int]:
    stmt = select(TipoProducto).order_by(TipoProducto.id)
    if q is not None:
        stmt = stmt.where(TipoProducto.nombre.ilike(f"%{q}%"))
    rows, total = paginar(db, stmt, limit, offset)
    return list(rows), total


def obtener_tipo_producto(db: Session, tipo_producto_id: int) -> TipoProducto:
    tipo = db.get(TipoProducto, tipo_producto_id)
    if tipo is None:
        raise HTTPException(status_code=404, detail="TipoProducto not found")
    return tipo


def crear_tipo_producto(db: Session, payload: TipoProductoCreate) -> TipoProducto:
    tipo = TipoProducto(**payload.model_dump())
    db.add(tipo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="TipoProducto name already exists") from None
    db.refresh(tipo)
    return tipo


def actualizar_tipo_producto(
    db: Session,
    tipo_producto_id: int,
    payload: TipoProductoUpdate,
) -> TipoProducto:
    tipo = obtener_tipo_producto(db, tipo_producto_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tipo, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="TipoProducto name already exists") from None
    db.refresh(tipo)
    return tipo


def eliminar_tipo_producto(db: Session, tipo_producto_id: int) -> None:
    tipo = obtener_tipo_producto(db, tipo_producto_id)
    db.delete(tipo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="TipoProducto is in use and cannot be deleted"
        ) from None
