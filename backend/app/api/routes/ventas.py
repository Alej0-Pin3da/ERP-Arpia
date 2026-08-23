from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db, require_roles
from app.core.limiter import get_rate_limit_config, user_limiter
from app.models.clientes import Cliente
from app.models.usuarios import Usuario
from app.models.ventas import DetalleVenta, DocumentState, Venta
from app.schemas.common import Paginated
from app.schemas.venta import VentaCreate, VentaRead, VentaUpdate, VentaStateTransition
from app.services.audit import audit_venta_create, audit_venta_delete, audit_venta_update
from app.services.inventory import (
    actualizar_venta,
    registrar_venta,
)
from app.services.inventory import (
    anular_venta as anular_venta_service,
)
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/ventas", tags=["ventas"])

# Rate limiter for critical write endpoints
_critical_limiter = user_limiter if settings.ENVIRONMENT != "test" else Limiter(key_func=lambda r: "test", enabled=False)

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
@_critical_limiter.limit("30/minute")
def create_venta(
    request: Request,
    payload: VentaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(mutation_user),
):
    # registrar_venta takes a plain dict; HTTPException->HTTP mapping is
    # handled there (404 missing producto/cliente, 400 foreign variant,
    # 409 insufficient stock). Invalid payloads (canal/cantidad/descuento)
    # are rejected by pydantic -> 422 before this runs.
    venta: Venta = registrar_venta(db, payload.model_dump())
    venta_id = venta.id
    try:
        audit_venta_create(db, request, current_user.id, current_user.rol, venta)
        db.commit()
    except Exception:
        db.rollback()
    # Re-query to avoid DetachedInstanceError after commit/expire
    venta = db.get(Venta, venta_id)
    return venta


@router.get("", response_model=Paginated[VentaRead])
@user_limiter.limit("300/minute")
def list_ventas(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    canal_venta: Literal["web", "whatsapp", "instagram", "feria"] | None = None,
    estado: Literal["draft", "confirmed", "cancelled", "reversed"] | None = None,
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
@_critical_limiter.limit("30/minute")
def update_venta_es_regalo(
    request: Request,
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


@router.put("/{venta_id}", response_model=VentaRead)
@_critical_limiter.limit("30/minute")
def update_venta(
    request: Request,
    venta_id: int,
    payload: VentaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(mutation_user),
):
    """Full update of a venta (PUT /ventas/{id}).

    Accepts the SAME body as POST /ventas (VentaCreate): cliente_id,
    canal_venta, descuento_porcentaje, es_regalo and detalles[]. The service
    recalculates total_venta and rebalances stock atomically — the old detail
    explosion is restored and the new one deducted in a single commit (409 if
    the new quantities exceed available stock). 404 when the venta does not
    exist, 400 when it is already anulada.
    """
    old_venta = db.get(Venta, venta_id)
    old_values = {"estado": old_venta.estado, "total_venta": str(old_venta.total_venta)} if old_venta else {}
    venta: Venta = actualizar_venta(db, venta_id, payload.model_dump())
    try:
        audit_venta_update(
            db, request, current_user.id, current_user.rol, venta_id,
            old_values, {"estado": venta.estado, "total_venta": str(venta.total_venta)},
        )
        db.commit()
    except Exception:
        pass
    venta = db.get(Venta, venta_id)
    return venta


@router.delete("/{venta_id}", response_model=VentaRead)
@_critical_limiter.limit("30/minute")
def anular_venta(
    request: Request,
    venta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(mutation_user),
):
    """Anular (soft-cancel) a venta — NOT a physical delete.

    Marks ``estado='anulada'`` and restores the sold BOM stock (reponer) in a
    single atomic commit, keeping the historical record (consistent with the
    es_regalo flag philosophy). Returns the anulada venta so the UI can
    refresh. 404 when the venta does not exist, 400 when already anulada.
    """
    venta_before = db.get(Venta, venta_id)
    old_values = {"estado": venta_before.estado} if venta_before else {}
    venta: Venta = anular_venta_service(db, venta_id)
    try:
        audit_venta_delete(db, request, current_user.id, current_user.rol, venta_id, old_values)
        db.commit()
    except Exception:
        pass
    venta = db.get(Venta, venta_id)
    return venta


@router.patch("/{venta_id}/state", response_model=VentaRead)
@_critical_limiter.limit("30/minute")
def transition_venta_state(
    request: Request,
    venta_id: int,
    payload: VentaStateTransition,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Transition venta to a new state with validation.

    Valid transitions:
    - draft -> confirmed, cancelled
    - confirmed -> cancelled, reversed
    - cancelled -> reversed
    - reversed -> (terminal, no transitions allowed)

    Reversal (cancelled -> reversed) requires a motivo (reason).
    """
    venta = db.get(Venta, venta_id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    try:
        new_state = DocumentState(payload.estado)
        venta.transition_to(
            new_state,
            motivo=payload.motivo,
            reversed_by=current_user.id if new_state == DocumentState.REVERSED else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    db.refresh(venta)
    return venta
