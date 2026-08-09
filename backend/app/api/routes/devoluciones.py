"""Devoluciones API routes — thin HTTP surface over the engine service.

POST /devoluciones (admin|operador) -> registrar_devolucion (full cancel or
partial return, atomic with FOR-UPDATE inventory restore).
GET  /devoluciones (audited) -> listar_devoluciones with items + sale
reference, optional venta_id / fecha range filters, limit/offset.

Business rules stay in app.services.devoluciones; this router only maps
payloads/roles and passes the authenticated user id for audit.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.usuarios import Usuario
from app.schemas.common import Paginated
from app.schemas.devoluciones import DevolucionCreate, DevolucionRead
from app.services.devoluciones import listar_devoluciones, registrar_devolucion

router = APIRouter(prefix="/devoluciones", tags=["devoluciones"])

mutation_user = require_roles("admin", "operador")
audited_user = require_roles("admin", "operador", "consulta")


@router.post("", response_model=DevolucionRead, status_code=status.HTTP_201_CREATED)
def create_devolucion(
    payload: DevolucionCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(mutation_user),
):
    """Register a return: tipo 'total' cancels the whole sale and restores ALL
    BOM stock; tipo 'parcial' restores only the returned lines (snapshot
    pricing). 400/409/422 mapping is owned by the service."""
    return registrar_devolucion(db, user.id, payload.model_dump())


@router.get("", response_model=Paginated[DevolucionRead])
def list_devoluciones(
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
    venta_id: int | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List returns ordered by id with items + Venta reference, optionally
    filtered by venta_id, a fecha range and a global q on motivo, paginated
    into ``{items, total}`` (total counts the filtered set)."""
    rows, total = listar_devoluciones(
        db,
        venta_id=venta_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        q=q,
        limit=limit,
        offset=offset,
    )
    return Paginated[DevolucionRead](items=list(rows), total=total)
