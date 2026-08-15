from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models import CompraInsumo, Insumo, Usuario
from app.schemas.common import Paginated
from app.schemas.compra_insumo import CompraInsumoCreate, CompraInsumoRead
from app.services.paginacion import aplicar_orden, paginar
from app.services.wac import registrar_compra

router = APIRouter(prefix="/compras-insumos", tags=["compras-insumos"])

audited_user = require_roles("admin", "operador", "consulta")
mutation_user = require_roles("admin", "operador")

# Whitelisted server-side sort keys. insumo is a joined column.
_SORTABLE_COMPRAS = {
    "id": CompraInsumo.id,
    "fecha_compra": CompraInsumo.fecha_compra,
    "cantidad_comprada": CompraInsumo.cantidad_comprada,
    "precio_unitario_compra": CompraInsumo.precio_unitario_compra,
    "insumo": Insumo.nombre,
}


@router.post("", response_model=CompraInsumoRead, status_code=status.HTTP_201_CREATED)
def create_compra_insumo(
    payload: CompraInsumoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    compra = registrar_compra(
        db,
        insumo_id=payload.insumo_id,
        cantidad=payload.cantidad_comprada,
        precio_unitario=payload.precio_unitario_compra,
    )
    return compra


@router.get("", response_model=Paginated[CompraInsumoRead])
def list_compras_insumos(
    limit: int = 50,
    offset: int = 0,
    insumo_id: int | None = None,
    q: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    # Single join build for BOTH filtering and sorting: SQLAlchemy does not
    # dedupe repeated joins, so Insumo is joined exactly once.
    stmt = select(CompraInsumo).join(CompraInsumo.insumo)
    if insumo_id is not None:
        stmt = stmt.where(CompraInsumo.insumo_id == insumo_id)
    if q is not None:
        stmt = stmt.where(Insumo.nombre.ilike(f"%{q}%"))
    stmt = stmt.order_by(CompraInsumo.id)
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_COMPRAS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[CompraInsumoRead](items=list(rows), total=total)
