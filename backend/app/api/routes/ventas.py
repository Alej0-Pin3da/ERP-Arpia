from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.clientes import Cliente
from app.models.ventas import DetalleVenta, Venta
from app.schemas.common import Paginated
from app.schemas.venta import VentaCreate, VentaRead, VentaUpdate
from app.services.inventory import registrar_venta
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/ventas", tags=["ventas"])

mutation_user = require_roles("admin", "operador")
audited_user = require_roles("admin", "operador", "consulta")

# Whitelisted server-side sort keys (frontend field -> SQLAlchemy column).
# cliente is the COALESCE'd joined name so NULL clientes sort predictably.
_SORTABLE_VENTAS = {
    "id": Venta.id,
    "fecha": Venta.fecha,
    "canal_venta": Venta.canal_venta,
    "estado": Venta.estado,
    "total_venta": Venta.total_venta,
    "cliente": func.coalesce(Cliente.nombre, ""),
}


@router.post("", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
def create_venta(
    payload: VentaCreate,
    db: Session = Depends(get_db),
    _: Venta = Depends(mutation_user),
):
    # registrar_venta takes a plain dict; HTTPException->HTTP mapping is
    # handled there (404 missing producto/cliente, 400 foreign variant,
    # 409 insufficient stock). Invalid payloads (canal/cantidad/descuento)
    # are rejected by pydantic -> 422 before this runs.
    venta: Venta = registrar_venta(db, payload.model_dump())
    return venta


@router.get("", response_model=Paginated[VentaRead])
def list_ventas(
    limit: int = 50,
    offset: int = 0,
    canal_venta: Literal["web", "whatsapp", "instagram", "feria"] | None = None,
    estado: Literal["completada", "anulada"] | None = None,
    producto_id: int | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Venta = Depends(audited_user),
):
    stmt = select(Venta).outerjoin(Venta.cliente).order_by(Venta.id)
    if canal_venta is not None:
        stmt = stmt.where(Venta.canal_venta == canal_venta)
    if estado is not None:
        stmt = stmt.where(Venta.estado == estado)
    if producto_id is not None:
        stmt = stmt.where(Venta.detalles.any(DetalleVenta.producto_id == producto_id))
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_VENTAS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[VentaRead](items=list(rows), total=total)


@router.patch("/{venta_id}", response_model=VentaRead)
def update_venta_es_regalo(
    venta_id: int,
    payload: VentaUpdate,
    db: Session = Depends(get_db),
    _: Venta = Depends(mutation_user),
):
    """Mark/unmark a venta as a gift (es_regalo).

    Only ``es_regalo`` is updatable for now. ``total_venta`` is NEVER changed
    here: the historical price is kept as a reference and money reports
    exclude gifts via the flag. 404 when the venta does not exist.
    """
    venta = db.get(Venta, venta_id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    venta.es_regalo = payload.es_regalo
    db.commit()
    db.refresh(venta)
    return venta
