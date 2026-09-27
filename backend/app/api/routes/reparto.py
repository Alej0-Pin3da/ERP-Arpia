"""Automatic profit-split routes (V6 M2).

Live informational balances (no money moves here — the official settlement
stays ``crear_liquidacion``):
- GET /reparto/saldos: running balance per account.
- GET/POST /reparto/reglas, PATCH /reparto/reglas/{id}: split rules.
- GET /reparto/ventas/{venta_id}: per-sale applied ledger.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.reparto import ReglaLiquidacion, RepartoVenta, SaldoSocia
from app.models.usuarios import Usuario
from app.schemas.reparto import (
    ReglaCreate,
    ReglaRead,
    ReglaUpdate,
    RepartoVentaRead,
    SaldoRead,
)

router = APIRouter(prefix="/reparto", tags=["reparto"])

audited_user = require_roles("admin", "operador", "consulta")
editor_user = require_roles("admin", "operador")


@router.get("/saldos", response_model=list[SaldoRead])
def list_saldos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Running balance per account (live, informational)."""
    return list(
        db.scalars(select(SaldoSocia).order_by(SaldoSocia.cuenta))
    )


@router.get("/reglas", response_model=list[ReglaRead])
def list_reglas(
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Active and inactive split rules."""
    return list(
        db.scalars(select(ReglaLiquidacion).order_by(ReglaLiquidacion.id))
    )


@router.post("/reglas", response_model=ReglaRead, status_code=status.HTTP_201_CREATED)
def create_regla(
    payload: ReglaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Create a split rule (409 on duplicate account)."""
    regla = ReglaLiquidacion(
        cuenta_destino=payload.cuenta_destino.strip(),
        porcentaje=payload.porcentaje,
    )
    db.add(regla)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="La cuenta ya tiene regla") from None
    db.refresh(regla)
    return regla


@router.patch("/reglas/{regla_id}", response_model=ReglaRead)
def update_regla(
    regla_id: int,
    payload: ReglaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Update porcentaje/activo/cuenta (409 on duplicate account)."""
    regla = db.get(ReglaLiquidacion, regla_id)
    if regla is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "cuenta_destino" and isinstance(value, str):
            value = value.strip()
        setattr(regla, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="La cuenta ya tiene regla") from None
    db.refresh(regla)
    return regla


@router.get("/ventas/{venta_id}", response_model=list[RepartoVentaRead])
def get_reparto_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Per-sale applied split ledger (empty when nothing was split)."""
    return list(
        db.scalars(
            select(RepartoVenta)
            .where(RepartoVenta.venta_id == venta_id)
            .order_by(RepartoVenta.id)
        )
    )
