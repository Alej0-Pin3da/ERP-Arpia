"""Omisiones API routes — MIG-3/MIG-4.

The Migracion_Omisiones table is populated by the migration CLI hook in
commit mode (migrate/omisiones.py); this module is the read / mark-resolved
surface:
- GET /omisiones: paginated {items, total} with AND-combined filters
  (fase, nivel, hoja, resuelta, fecha_desde/fecha_hasta on creado_en, q on
  mensaje). Audited roles admin|operador|consulta (design D8).
- PATCH /omisiones/{id}: set resuelta; require_admin (design D9, spec
  MIG-4); 404 when the row does not exist.
"""

from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.migracion import MigracionOmision
from app.models.usuarios import Usuario
from app.schemas.common import Paginated
from app.schemas.migracion import OmisionRead, OmisionUpdate
from app.services.paginacion import paginar

router = APIRouter(prefix="/omisiones", tags=["omisiones"])

audited_user = require_roles("admin", "operador", "consulta")


@router.get("", response_model=Paginated[OmisionRead])
def list_omisiones(
    limit: int = 50,
    offset: int = 0,
    fase: str | None = None,
    nivel: Literal["WARN", "ERROR"] | None = None,
    hoja: str | None = None,
    resuelta: bool | None = None,
    # date (not datetime): callers filter by calendar day ("2026-08-01");
    # pydantic v2 datetime rejects date-only strings with 422.
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Paginated list of migration omissions with AND-combined filters
    (MIG-3): every filter reduces both ``items`` and ``total``."""
    stmt = select(MigracionOmision)
    if fase is not None:
        stmt = stmt.where(MigracionOmision.fase == fase)
    if nivel is not None:
        stmt = stmt.where(MigracionOmision.nivel == nivel)
    if hoja is not None:
        stmt = stmt.where(MigracionOmision.hoja == hoja)
    if resuelta is not None:
        stmt = stmt.where(MigracionOmision.resuelta == resuelta)
    if fecha_desde is not None:
        stmt = stmt.where(MigracionOmision.creado_en >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(MigracionOmision.creado_en <= fecha_hasta)
    if q is not None:
        stmt = stmt.where(MigracionOmision.mensaje.ilike(f"%{q}%"))
    stmt = stmt.order_by(MigracionOmision.id)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[OmisionRead](items=list(rows), total=total)


@router.patch("/{omision_id}", response_model=OmisionRead)
def update_omision(
    omision_id: int,
    payload: OmisionUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
):
    """Mark/unmark an omission as resolved (MIG-4); 404 when missing."""
    omision = db.get(MigracionOmision, omision_id)
    if omision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Omisión no encontrada",
        )
    omision.resuelta = payload.resuelta
    db.commit()
    db.refresh(omision)
    return omision
