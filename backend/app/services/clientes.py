"""Service layer for Clientes CRM.

Separates business and persistence logic from the FastAPI route layer.
"""
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.clientes import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.services.paginacion import aplicar_orden, paginar

# Whitelisted server-side sort keys (plain columns on Cliente).
_SORTABLE_CLIENTES = {
    "id": Cliente.id,
    "nombre": Cliente.nombre,
}


def listar_clientes(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    tipo: str | None = None,
    ciudad: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
) -> tuple[list[Cliente], int]:
    """Return paginated and filtered clients list and total count."""
    stmt = select(Cliente).order_by(Cliente.id)
    if tipo is not None:
        stmt = stmt.where(Cliente.tipo == tipo)
    if ciudad is not None:
        stmt = stmt.where(Cliente.ciudad == ciudad)
    if q is not None:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Cliente.nombre.ilike(like),
                Cliente.ciudad.ilike(like),
                Cliente.direccion.ilike(like),
            )
        )
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_CLIENTES)
    rows, total = paginar(db, stmt, limit, offset)
    return list(rows), total


def obtener_cliente(db: Session, cliente_id: int) -> Cliente:
    """Fetch a single client by id or raise 404."""
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return cliente


def crear_cliente(db: Session, payload: ClienteCreate) -> Cliente:
    """Create a new client entity."""
    cliente = Cliente(**payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def actualizar_cliente(db: Session, cliente_id: int, payload: ClienteUpdate) -> Cliente:
    """Update existing client or raise 404."""
    cliente = obtener_cliente(db, cliente_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, field, value)
    db.commit()
    db.refresh(cliente)
    return cliente


def eliminar_cliente(db: Session, cliente_id: int) -> None:
    """Delete client or raise 404."""
    cliente = obtener_cliente(db, cliente_id)
    db.delete(cliente)
    db.commit()
