"""Finanzas API routes — thin HTTP surface over the finanzas engine.

- POST/GET/DELETE /finanzas/movimientos: MovimientoFinanciero CRUD (soft
  delete via estado -> 'inactivo').
- POST /finanzas/liquidaciones: one-time proportional settlement across socios
  (per-socio Retiro rows; replay of the same liquidacion_id -> 409).
- GET/POST/PATCH/DELETE /finanzas/socios: SociosConfiguracion management with
  the global sum-to-100 invariant enforced in the service layer.

Mutations require admin|operador; lists are audited (admin|operador|consulta).
"""

from typing import Literal

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, require_roles
from app.core.limiter import user_limiter
from app.models.finanzas import MovimientoFinanciero, SociosConfiguracion
from app.models.usuarios import Usuario
from app.schemas.common import Paginated
from app.schemas.finanzas import (
    LiquidacionCreate,
    MovimientoCreate,
    MovimientoRead,
    MovimientoUpdate,
    SocioConfiguracionCreate,
    SocioConfiguracionRead,
    SocioConfiguracionUpdate,
)
from app.services.finanzas import (
    actualizar_movimiento,
    actualizar_socio_configuracion,
    crear_movimiento,
    crear_socio_configuracion,
    eliminar_movimiento,
    eliminar_socio_configuracion,
    settle_liquidacion,
)
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/finanzas", tags=["finanzas"])

# Rate limiter for critical write endpoints
_critical_limiter = user_limiter if settings.ENVIRONMENT != "test" else Limiter(key_func=lambda r: "test", enabled=False)

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
    _: Usuario = Depends(mutation_user),
):
    """Create a financial movement (tipo Gasto|Inversion|Retiro)."""
    return crear_movimiento(db, payload.model_dump())


@router.get("/movimientos", response_model=Paginated[MovimientoRead])
@user_limiter.limit("300/minute")
def list_movimientos_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    tipo: Literal["Gasto", "Inversion", "Retiro"] | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """List active movements (soft-deleted rows are excluded), paginated with
    {items, total} and an optional tipo filter (API-1/API-3)."""
    # Socio joined once up-front so the socio sort key works; outer join since
    # socio_id is nullable.
    stmt = (
        select(MovimientoFinanciero)
        .outerjoin(MovimientoFinanciero.socio)
        .where(MovimientoFinanciero.estado == "activo")
    )
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
    """Soft delete a movement (estado -> 'inactivo')."""
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


# ---------------------------------------------------------------------------
# One-time settlement (FIN-1)
# ---------------------------------------------------------------------------


@router.post(
    "/liquidaciones",
    response_model=list[MovimientoRead],
    status_code=status.HTTP_201_CREATED,
)
@_critical_limiter.limit("30/minute")
def crear_liquidacion(
    request: Request,
    payload: LiquidacionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Process a proportional settlement: one 'Retiro' per socio for
    monto * porcentaje / 100, one-time per liquidacion_id (replay -> 409)."""
    return settle_liquidacion(db, payload.monto, payload.notas, payload.liquidacion_id)


# ---------------------------------------------------------------------------
# SociosConfiguracion management (FIN-2)
# ---------------------------------------------------------------------------


@router.get("/socios", response_model=Paginated[SocioConfiguracionRead])
@user_limiter.limit("300/minute")
def list_socios(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """List partner participation rows ordered by id, paginated {items, total}
    with an optional q search on nombre (API-1/API-3)."""
    stmt = select(SociosConfiguracion)
    if q is not None:
        stmt = stmt.where(SociosConfiguracion.nombre.ilike(f"%{q}%"))
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
    """Create a partner row; the global sum of participations must land exactly
    on 100 (else 422)."""
    return crear_socio_configuracion(db, payload.nombre, payload.porcentaje_participacion)


@router.patch("/socios/{socio_id}", response_model=SocioConfiguracionRead)
@_critical_limiter.limit("30/minute")
def update_socio(
    request: Request,
    socio_id: int,
    payload: SocioConfiguracionUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Update a partner's share (interim rebalance below 100 allowed, never
    above 100 -> 422)."""
    return actualizar_socio_configuracion(db, socio_id, payload.porcentaje_participacion)


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