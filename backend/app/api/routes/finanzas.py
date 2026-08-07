"""Finanzas API routes — thin HTTP surface over the finanzas engine.

- POST/GET/DELETE /finanzas/movimientos: MovimientoFinanciero CRUD (soft
  delete via estado -> 'inactivo').
- POST /finanzas/liquidaciones: one-time proportional settlement across socios
  (per-socio Retiro rows; replay of the same liquidacion_id -> 409).
- GET/POST/PATCH/DELETE /finanzas/socios: SociosConfiguracion management with
  the global sum-to-100 invariant enforced in the service layer.

Mutations require admin|operador; lists are audited (admin|operador|consulta).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.finanzas import SociosConfiguracion
from app.models.usuarios import Usuario
from app.schemas.finanzas import (
    LiquidacionCreate,
    MovimientoCreate,
    MovimientoRead,
    SocioConfiguracionCreate,
    SocioConfiguracionRead,
    SocioConfiguracionUpdate,
)
from app.services.finanzas import (
    actualizar_socio_configuracion,
    crear_movimiento,
    crear_socio_configuracion,
    eliminar_movimiento,
    eliminar_socio_configuracion,
    listar_movimientos,
    settle_liquidacion,
)

router = APIRouter(prefix="/finanzas", tags=["finanzas"])

mutation_user = require_roles("admin", "operador")
audited_user = require_roles("admin", "operador", "consulta")


# ---------------------------------------------------------------------------
# MovimientoFinanciero CRUD (FIN-1)
# ---------------------------------------------------------------------------


@router.post(
    "/movimientos",
    response_model=MovimientoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_movimiento(
    payload: MovimientoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Create a financial movement (tipo Gasto|Inversion|Retiro)."""
    return crear_movimiento(db, payload.model_dump())


@router.get("/movimientos", response_model=list[MovimientoRead])
def list_movimientos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """List active movements (soft-deleted rows are excluded)."""
    return listar_movimientos(db)


@router.delete("/movimientos/{movimiento_id}", response_model=MovimientoRead)
def delete_movimiento(
    movimiento_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Soft delete a movement (estado -> 'inactivo')."""
    return eliminar_movimiento(db, movimiento_id)


# ---------------------------------------------------------------------------
# One-time settlement (FIN-1)
# ---------------------------------------------------------------------------


@router.post(
    "/liquidaciones",
    response_model=list[MovimientoRead],
    status_code=status.HTTP_201_CREATED,
)
def crear_liquidacion(
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


@router.get("/socios", response_model=list[SocioConfiguracionRead])
def list_socios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """List partner participation rows ordered by id."""
    return list(db.scalars(select(SociosConfiguracion).order_by(SociosConfiguracion.id)))


@router.post(
    "/socios",
    response_model=SocioConfiguracionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_socio(
    payload: SocioConfiguracionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Create a partner row; the global sum of participations must land exactly
    on 100 (else 422)."""
    return crear_socio_configuracion(db, payload.nombre, payload.porcentaje_participacion)


@router.patch("/socios/{socio_id}", response_model=SocioConfiguracionRead)
def update_socio(
    socio_id: int,
    payload: SocioConfiguracionUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Update a partner's share (interim rebalance below 100 allowed, never
    above 100 -> 422)."""
    return actualizar_socio_configuracion(db, socio_id, payload.porcentaje_participacion)


@router.delete("/socios/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_socio(
    socio_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    """Delete a partner row; blocked with 409 when the socio has payouts."""
    eliminar_socio_configuracion(db, socio_id)
