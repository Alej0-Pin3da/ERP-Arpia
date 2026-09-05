"""Devoluciones API routes — thin HTTP surface over the engine service.

POST /devoluciones (admin|operador) -> registrar_devolucion (full cancel or
partial return, atomic with FOR-UPDATE inventory restore).
GET  /devoluciones (audited) -> listar_devoluciones with items + sale
reference, optional venta_id / fecha range filters, limit/offset.
PATCH /devoluciones/{id}/state (admin|operador) -> state transition with validation

Business rules stay in app.services.devoluciones; this router only maps
payloads/roles and passes the authenticated user id for audit.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db, require_roles
from app.core.limiter import user_limiter
from app.models.usuarios import Usuario
from app.models.ventas import Devolucion, DocumentState
from app.schemas.common import Paginated
from app.schemas.devoluciones import (
    DevolucionCreate,
    DevolucionRead,
    DevolucionStateTransition,
    DevolucionUpdate,
)
from app.services.audit import audit_devolucion_create
from app.services.devoluciones import (
    actualizar_devolucion,
    eliminar_devolucion,
    listar_devoluciones,
    registrar_devolucion,
)

router = APIRouter(prefix="/devoluciones", tags=["devoluciones"])

# Rate limiter for critical write endpoints
_critical_limiter = (
    user_limiter
    if settings.ENVIRONMENT != "test"
    else Limiter(key_func=lambda r: "test", enabled=False)
)

mutation_user = require_roles("admin", "operador")
audited_user = require_roles("admin", "operador", "consulta")


def _devolucion_to_read(d: Devolucion) -> DevolucionRead:
    res = DevolucionRead.model_validate(d)
    venta = d.venta
    if venta is not None:
        res.cliente_nombre = venta.cliente_nombre
        detalles = venta.detalles or []
        if detalles:
            res.prenda_nombre = detalles[0].nombre_prenda
    return res


@router.post("", response_model=DevolucionRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_devolucion(
    request: Request,
    payload: DevolucionCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(mutation_user),
):
    """Register a return: tipo 'total' cancels the whole sale and restores ALL
    BOM stock; tipo 'parcial' restores only the returned lines (snapshot
    pricing). 400/409/422 mapping is owned by the service."""
    devolucion = registrar_devolucion(db, user.id, payload.model_dump())
    devolucion_id = devolucion.id
    try:
        audit_devolucion_create(db, request, user.id, user.rol, devolucion)
        db.commit()
    except Exception:
        pass
    devolucion = db.get(Devolucion, devolucion_id)
    assert devolucion is not None
    return _devolucion_to_read(devolucion)


@router.get("", response_model=Paginated[DevolucionRead])
@user_limiter.limit("300/minute")
def list_devoluciones(
    request: Request,
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
    return Paginated[DevolucionRead](
        items=[_devolucion_to_read(d) for d in rows], total=total
    )


@router.get("/{devolucion_id}", response_model=DevolucionRead)
@user_limiter.limit("300/minute")
def get_devolucion(
    request: Request,
    devolucion_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Get a single devolucion with its items + Venta reference."""
    devolucion = db.get(Devolucion, devolucion_id)
    if devolucion is None:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    return _devolucion_to_read(devolucion)


@router.put("/{devolucion_id}", response_model=DevolucionRead)
@_critical_limiter.limit("30/minute")
def update_devolucion(
    request: Request,
    devolucion_id: int,
    payload: DevolucionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Edit motivo and/or transition estado.

    motivo is correctable on draft/confirmed/cancelled; estado must follow
    the DocumentState FSM (400 otherwise); reversed is immutable (422).
    """
    if current_user.rol not in ("admin", "operador"):
        raise HTTPException(status_code=403, detail="No autorizado")
    return actualizar_devolucion(
        db,
        devolucion_id,
        motivo=payload.motivo,
        estado=payload.estado,
        reversed_by=current_user.id,
    )


@router.delete("/{devolucion_id}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_devolucion(
    request: Request,
    devolucion_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Hard-delete a devolucion ONLY in draft state (204). Non-draft ->
    400: use the state transition (cancelled/reversed) instead, since the
    return already restored stock."""
    if current_user.rol not in ("admin", "operador"):
        raise HTTPException(status_code=403, detail="No autorizado")
    eliminar_devolucion(db, devolucion_id)
    return None


@router.patch("/{devolucion_id}/state", response_model=DevolucionRead)
@_critical_limiter.limit("30/minute")
def transition_devolucion_state(
    request: Request,
    devolucion_id: int,
    payload: DevolucionStateTransition,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Transition devolucion to a new state with validation.

    Valid transitions:
    - draft -> confirmed, cancelled
    - confirmed -> cancelled, reversed
    - cancelled -> reversed
    - reversed -> (terminal, no transitions allowed)

    Reversal (cancelled -> reversed) requires a motivo (reason).
    """
    devolucion = db.get(Devolucion, devolucion_id)
    if devolucion is None:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")

    try:
        new_state = DocumentState(payload.estado)
        devolucion.transition_to(
            new_state,
            motivo=payload.motivo,
            reversed_by=current_user.id if new_state == DocumentState.REVERSED else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    db.commit()
    db.refresh(devolucion)
    return devolucion
