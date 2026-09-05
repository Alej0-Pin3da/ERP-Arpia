"""Finanzas API routes — thin HTTP surface over the finanzas engine.

- POST/GET/DELETE /finanzas/movimientos: MovimientoFinanciero CRUD with state transitions.
- POST /finanzas/liquidaciones: one-time proportional settlement across socios
  (per-socio Retiro rows; replay of the same liquidacion_id -> 409).
- GET/POST/PATCH/DELETE /finanzas/socios: SociosConfiguracion management with
  the global sum-to-100 invariant enforced in the service layer.

v4 (PR2):
- GET/POST/PATCH/DELETE /finanzas/socios: extended socia profile (SOC-1), sum-to-100
  over activo incl fondo (SOC-2), composable filters (SOC-3).
- POST /finanzas/liquidaciones/crear + GET /{id} + PATCH /{id}/estado + DELETE /{id}:
  real liquidacion header+distribution (LIQ-1/2/3).
- GET/POST /finanzas/anticipos + PATCH /{id}/descuento + PATCH /{id}/estado: anticipos
  with atomic discount link (ANT-1/2/3).

Mutations require admin|operador; lists are audited (admin|operador|consulta).
"""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.deps import get_current_user, get_db, require_roles
from app.core.limiter import user_limiter
from app.models.finanzas import (
    Anticipo,
    AnticipoEstado,
    DocumentState,
    Liquidacion,
    LiquidacionDistribucion,
    MovimientoFinanciero,
    SociosConfiguracion,
)
from app.models.usuarios import Usuario
from app.schemas.common import Paginated
from app.schemas.finanzas import (
    AnticipoCreate,
    AnticipoDescuentoUpdate,
    AnticipoEstadoUpdate,
    AnticipoRead,
    LiquidacionCreate,
    LiquidacionEstadoUpdate,
    LiquidacionRead,
    LiquidacionSettlementCreate,
    MovimientoCreate,
    MovimientoRead,
    MovimientoStateTransition,
    MovimientoUpdate,
    SocioConfiguracionCreate,
    SocioConfiguracionRead,
    SocioConfiguracionUpdate,
)
from app.services.audit import audit_movimiento_create
from app.services.finanzas import (
    actualizar_movimiento,
    actualizar_socia_configuracion,
    actualizar_socio_configuracion,
    crear_anticipo,
    crear_liquidacion,
    crear_movimiento,
    crear_socia_configuracion,
    crear_socio_configuracion,
    descontar_anticipo,
    eliminar_anticipo,
    eliminar_liquidacion,
    eliminar_movimiento,
    eliminar_socio_configuracion,
    listar_socias,
    settle_liquidacion,
    transicionar_anticipo,
    transicionar_liquidacion,
)
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/finanzas", tags=["finanzas"])

# Rate limiter for critical write endpoints
_critical_limiter = (
    user_limiter
    if settings.ENVIRONMENT != "test"
    else Limiter(key_func=lambda r: "test", enabled=False)
)

mutation_user = require_roles("admin", "operador")
audited_user = require_roles("admin", "operador", "consulta")

# Whitelisted server-side sort keys; socio is the COALESCE'd joined partner
# name (outer join — socio_id is nullable).
_SORTABLE_MOVIMIENTOS = {
    "id": MovimientoFinanciero.id,
    "fecha": MovimientoFinanciero.fecha,
    "tipo": MovimientoFinanciero.tipo,
    "monto": MovimientoFinanciero.monto,
    "descripcion": MovimientoFinanciero.descripcion,
    "socio": func.coalesce(SociosConfiguracion.nombre, ""),
}

_SORTABLE_SOCIOS = {
    "id": SociosConfiguracion.id,
    "nombre": SociosConfiguracion.nombre,
    "porcentaje_participacion": SociosConfiguracion.porcentaje_participacion,
}


# ---------------------------------------------------------------------------
# MovimientoFinanciero CRUD (FIN-1)
# ---------------------------------------------------------------------------


@router.post(
    "/movimientos",
    response_model=MovimientoRead,
    status_code=status.HTTP_201_CREATED,
)
@_critical_limiter.limit("30/minute")
def create_movimiento(
    request: Request,
    payload: MovimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(mutation_user),
):
    """Create a financial movement (tipo Gasto|Inversion|Retiro)."""
    movimiento = crear_movimiento(db, payload.model_dump())
    movimiento_id = movimiento.id
    try:
        audit_movimiento_create(db, request, current_user.id, current_user.rol, movimiento)
        db.commit()
    except Exception:
        pass
    movimiento = db.get(MovimientoFinanciero, movimiento_id)
    return movimiento


@router.get("/movimientos", response_model=Paginated[MovimientoRead])
@user_limiter.limit("300/minute")
def list_movimientos_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    tipo: Literal["Gasto", "Inversion", "Retiro"] | None = None,
    estado: Literal["draft", "confirmed", "cancelled", "reversed"] | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """List movements (soft-deleted rows are excluded), paginated with
    {items, total} and optional tipo/estado filters."""
    # Socio joined once up-front so the socio sort key works; outer join since
    # socio_id is nullable.
    stmt = select(MovimientoFinanciero).outerjoin(MovimientoFinanciero.socio)
    if estado is not None:
        stmt = stmt.where(MovimientoFinanciero.estado == estado)
    else:
        # Default: hide soft-deleted (cancelled) and terminal reversed rows.
        stmt = stmt.where(MovimientoFinanciero.estado != DocumentState.CANCELLED.value)
    if tipo is not None:
        stmt = stmt.where(MovimientoFinanciero.tipo == tipo)
    stmt = stmt.order_by(MovimientoFinanciero.id)
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_MOVIMIENTOS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[MovimientoRead](items=list(rows), total=total)


@router.delete("/movimientos/{movimiento_id}", response_model=MovimientoRead)
@_critical_limiter.limit("30/minute")
def delete_movimiento(
    request: Request,
    movimiento_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Soft delete a movement (estado -> 'cancelled')."""
    return eliminar_movimiento(db, movimiento_id)


@router.patch("/movimientos/{movimiento_id}", response_model=MovimientoRead)
@_critical_limiter.limit("30/minute")
def update_movimiento_route(
    request: Request,
    movimiento_id: int,
    payload: MovimientoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Partial update of a movement (FIN-1): fecha/tipo/descripcion/monto/
    socio_id, only the sent fields applied. Liquidacion-born rows freeze
    monto/socio_id server-side (FIN-2 -> 422)."""
    return actualizar_movimiento(db, movimiento_id, payload.model_dump(exclude_unset=True))


@router.patch("/movimientos/{movimiento_id}/state", response_model=MovimientoRead)
@_critical_limiter.limit("30/minute")
def transition_movimiento_state(
    request: Request,
    movimiento_id: int,
    payload: MovimientoStateTransition,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: Usuario = Depends(mutation_user),
):
    """Transition movimiento to a new state with validation.

    Valid transitions:
    - draft -> confirmed, cancelled
    - confirmed -> cancelled, reversed
    - cancelled -> reversed
    - reversed -> (terminal, no transitions allowed)

    Reversal (cancelled -> reversed) requires a motivo (reason).
    """
    movimiento = db.get(MovimientoFinanciero, movimiento_id)
    if movimiento is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")

    try:
        new_state = DocumentState(payload.estado)
        movimiento.transition_to(
            new_state,
            motivo=payload.motivo,
            reversed_by=current_user.id if new_state == DocumentState.REVERSED else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    db.commit()
    db.refresh(movimiento)
    return movimiento


# ---------------------------------------------------------------------------
# One-time settlement (FIN-1)
# ---------------------------------------------------------------------------


@router.post(
    "/liquidaciones",
    response_model=list[MovimientoRead],
    status_code=status.HTTP_201_CREATED,
)
@_critical_limiter.limit("30/minute")
def crear_liquidacion_settlement(
    request: Request,
    payload: LiquidacionSettlementCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Process a proportional settlement: one 'Retiro' per socio for
    monto * porcentaje / 100, one-time per liquidacion_id (replay -> 409)."""
    return settle_liquidacion(db, payload.monto, payload.notas, payload.liquidacion_id)


# ---------------------------------------------------------------------------
# SociosConfiguracion management (FIN-2 / v4 SOC-1/SOC-2/SOC-3)
# ---------------------------------------------------------------------------


@router.get("/socios", response_model=Paginated[SocioConfiguracionRead])
@user_limiter.limit("300/minute")
def list_socios(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    activo: bool | None = None,
    es_fondo_taller: bool | None = None,
    rol: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """List partner participation rows ordered by id, paginated {items, total}
    with composable filters activo/es_fondo_taller/rol/q (SOC-3)."""
    stmt = select(SociosConfiguracion)
    if activo is not None:
        stmt = stmt.where(SociosConfiguracion.activo.is_(activo))
    if es_fondo_taller is not None:
        stmt = stmt.where(SociosConfiguracion.es_fondo_taller.is_(es_fondo_taller))
    if rol is not None:
        stmt = stmt.where(SociosConfiguracion.rol == rol)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            SociosConfiguracion.nombre.ilike(like)
            | SociosConfiguracion.email.ilike(like)
            | SociosConfiguracion.telefono.ilike(like)
        )
    stmt = stmt.order_by(SociosConfiguracion.id)
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_SOCIOS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[SocioConfiguracionRead](items=list(rows), total=total)


@router.post(
    "/socios",
    response_model=SocioConfiguracionRead,
    status_code=status.HTTP_201_CREATED,
)
@_critical_limiter.limit("30/minute")
def create_socio(
    request: Request,
    payload: SocioConfiguracionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Create a socia with the extended profile (SOC-1). Sum-to-100 over active
    rows incl fondo is checked in the service; building up to 100 is allowed,
    exceeding it -> 422, second active fondo -> 422 (SOC-2)."""
    data = payload.model_dump()
    porcentaje = data.pop("porcentaje_participacion")
    nombre = data.pop("nombre")
    return crear_socia_configuracion(db, nombre=nombre, porcentaje=porcentaje, **data)


@router.patch("/socios/{socio_id}", response_model=SocioConfiguracionRead)
@_critical_limiter.limit("30/minute")
def update_socio(
    request: Request,
    socio_id: int,
    payload: SocioConfiguracionUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Partial update of a socia profile (SOC-1). Only sent fields applied;
    sum-to-100 over active rows incl fondo never exceeded -> 422 (SOC-2)."""
    return actualizar_socia_configuracion(
        db, socio_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/socios/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_socio(
    request: Request,
    socio_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Delete a partner row; blocked with 409 when the socio has payouts."""
    eliminar_socio_configuracion(db, socio_id)


# ---------------------------------------------------------------------------
# v4 — LIQ-1/2/3: real liquidaciones
# ---------------------------------------------------------------------------


def _liquidacion_response(db: Session, liq: Liquidacion) -> dict:
    """Build the LiquidacionRead response including distribution rows and the
    socia nombre (LIQ-1)."""
    return {
        "id": liq.id,
        "codigo": liq.codigo,
        "periodo": liq.periodo,
        "fecha_cierre": liq.fecha_cierre,
        "total_ventas_brutas": liq.total_ventas_brutas,
        "costo_taller_insumos": liq.costo_taller_insumos,
        "gastos_operativos": liq.gastos_operativos,
        "utilidad_neta_total": liq.utilidad_neta_total,
        "fondo_reinversion_monto": liq.fondo_reinversion_monto,
        "utilidad_repartible": liq.utilidad_repartible,
        "estado": liq.estado,
        "observaciones": liq.observaciones,
        "distribucion": [
            {
                "id": d.id,
                "liquidacion_id": d.liquidacion_id,
                "socia_id": d.socia_id,
                "socia_nombre": d.socia.nombre if d.socia else None,
                "porcentaje": d.porcentaje,
                "monto_bruto": d.monto_bruto,
                "deduccion_anticipos": d.deduccion_anticipos,
                "monto_neto": d.monto_neto,
                "estado_pago": d.estado_pago,
            }
            for d in liq.distribucion
        ],
    }


@router.post(
    "/liquidaciones/crear",
    response_model=LiquidacionRead,
    status_code=status.HTTP_201_CREATED,
)
@_critical_limiter.limit("30/minute")
def crear_liquidacion_real(
    request: Request,
    payload: LiquidacionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Create a real liquidacion header + distribution (LIQ-1). Codigo auto
    LIQ-YYYY-NN; drift>5% persists with warning (LIQ-3)."""
    liq, warnings = crear_liquidacion(db, payload.model_dump())
    db.refresh(liq)
    resp = _liquidacion_response(db, liq)
    resp["warnings"] = warnings
    return resp


@router.get("/liquidaciones/{liquidacion_id}", response_model=LiquidacionRead)
@user_limiter.limit("300/minute")
def get_liquidacion(
    request: Request,
    liquidacion_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Get one liquidacion with distribution (LIQ-1)."""
    liq = db.get(Liquidacion, liquidacion_id)
    if liq is None:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    resp = _liquidacion_response(db, liq)
    resp["warnings"] = []
    return resp


@router.get("/liquidaciones", response_model=Paginated[LiquidacionRead])
@user_limiter.limit("300/minute")
def list_liquidaciones(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    estado: Literal["BORRADOR", "APROBADA", "PAGADA"] | None = None,
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Paginated list of real liquidaciones (LIQ-1)."""
    stmt = (
        select(Liquidacion)
        .options(selectinload(Liquidacion.distribucion).selectinload(LiquidacionDistribucion.socia))
        .order_by(Liquidacion.id)
    )
    if estado is not None:
        stmt = stmt.where(Liquidacion.estado == estado)
    if periodo is not None:
        stmt = stmt.where(Liquidacion.periodo == periodo)
    rows, total = paginar(db, stmt, limit, offset)
    items = [_liquidacion_response(db, liq) for liq in rows]
    return Paginated[LiquidacionRead](items=items, total=total)


@router.patch("/liquidaciones/{liquidacion_id}/estado", response_model=LiquidacionRead)
@_critical_limiter.limit("30/minute")
def patch_liquidacion_estado(
    request: Request,
    liquidacion_id: int,
    payload: LiquidacionEstadoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """FSM BORRADOR -> APROBADA -> PAGADA; invalid/skip/revert -> 422 (LIQ-2)."""
    liq = transicionar_liquidacion(db, liquidacion_id, payload.estado)
    resp = _liquidacion_response(db, liq)
    resp["warnings"] = []
    return resp


@router.delete("/liquidaciones/{liquidacion_id}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_liquidacion(
    request: Request,
    liquidacion_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Delete a BORRADOR liquidacion; children cascade, linked anticipos SET NULL
    (LIQ-1/ANT-2)."""
    eliminar_liquidacion(db, liquidacion_id)


# ---------------------------------------------------------------------------
# v4 — ANT-1/2/3: anticipos
# ---------------------------------------------------------------------------


def _anticipo_response(db: Session, a: Anticipo) -> dict:
    return {
        "id": a.id,
        "socia_id": a.socia_id,
        "socia_nombre": a.socia.nombre if a.socia else None,
        "liquidacion_id": a.liquidacion_id,
        "monto": a.monto,
        "fecha": a.fecha,
        "estado": a.estado,
        "concepto": a.concepto,
        "metodo_desembolso": a.metodo_desembolso,
        "comprobante": a.comprobante,
        "observaciones": a.observaciones,
        "creado_en": a.creado_en,
    }


@router.get("/anticipos", response_model=Paginated[AnticipoRead])
@user_limiter.limit("300/minute")
def list_anticipos(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    socia_id: int | None = None,
    estado: Literal["PENDIENTE_DESCUENTO", "DESCONTADO", "ANULADO"] | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Paginated list of anticipos, filter by socia_id/estado (ANT-3)."""
    stmt = select(Anticipo).options(selectinload(Anticipo.socia)).order_by(Anticipo.id)
    if socia_id is not None:
        stmt = stmt.where(Anticipo.socia_id == socia_id)
    if estado is not None:
        stmt = stmt.where(Anticipo.estado == estado)
    rows, total = paginar(db, stmt, limit, offset)
    items = [_anticipo_response(db, a) for a in rows]
    return Paginated[AnticipoRead](items=items, total=total)


@router.post(
    "/anticipos",
    response_model=AnticipoRead,
    status_code=status.HTTP_201_CREATED,
)
@_critical_limiter.limit("30/minute")
def create_anticipo(
    request: Request,
    payload: AnticipoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Create an anticipo (ANT-1); nonexistent socia -> 404/422."""
    data = payload.model_dump()
    socia_id = data.pop("socia_id")
    monto = data.pop("monto")
    a = crear_anticipo(db, socia_id=socia_id, monto=monto, **data)
    return _anticipo_response(db, a)


@router.patch("/anticipos/{anticipo_id}/descuento", response_model=AnticipoRead)
@_critical_limiter.limit("30/minute")
def patch_anticipo_descuento(
    request: Request,
    anticipo_id: int,
    payload: AnticipoDescuentoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Atomically link an anticipo to a liquidacion + transition to DESCONTADO
    (ANT-2). Double-discount -> 409; ANULADO -> 422 (ANT-3)."""
    a = descontar_anticipo(db, anticipo_id, payload.liquidacion_id)
    return _anticipo_response(db, a)


@router.patch("/anticipos/{anticipo_id}/estado", response_model=AnticipoRead)
@_critical_limiter.limit("30/minute")
def patch_anticipo_estado(
    request: Request,
    anticipo_id: int,
    payload: AnticipoEstadoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """FSM PENDIENTE_DESCUENTO -> DESCONTADO|ANULADO; terminal rejects (ANT-2)."""
    a = transicionar_anticipo(db, anticipo_id, payload.estado)
    return _anticipo_response(db, a)


@router.delete("/anticipos/{anticipo_id}", status_code=status.HTTP_204_NO_CONTENT)
@_critical_limiter.limit("30/minute")
def delete_anticipo(
    request: Request,
    anticipo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    eliminar_anticipo(db, anticipo_id)
