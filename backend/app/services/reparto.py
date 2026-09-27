"""Automatic profit split on confirmed sales (V6 M2).

``aplicar_reparto_venta`` runs INSIDE the sale's own transaction (called
after flush, before commit — no commits here, the caller owns them):
it reads the sale's ``ganancia_neta``, splits it across the active rules
(last line absorbs rounding so money is conserved to the cent), appends
one ``Reparto_Ventas`` ledger row per account and accumulates
``Saldos_Socias`` (pessimistically locked). ``revertir_reparto_venta``
negates the exact ledger rows on reversal.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reparto import ReglaLiquidacion, RepartoVenta, SaldoSocia
from app.models.ventas import Venta


def reglas_activas(db: Session) -> list[ReglaLiquidacion]:
    return list(
        db.scalars(
            select(ReglaLiquidacion)
            .where(ReglaLiquidacion.activo.is_(True))
            .order_by(ReglaLiquidacion.id)
        )
    )


def _saldo_bloqueado(db: Session, cuenta: str) -> SaldoSocia:
    saldo = db.scalar(
        select(SaldoSocia).where(SaldoSocia.cuenta == cuenta).with_for_update()
    )
    if saldo is None:
        saldo = SaldoSocia(cuenta=cuenta, saldo=Decimal("0"))
        db.add(saldo)
        db.flush()
    return saldo


def aplicar_reparto_venta(db: Session, venta: Venta) -> list[dict]:
    """Split a confirmed sale's gain across active rules (no commit)."""
    ganancia = Decimal(venta.ganancia_neta or Decimal("0"))
    if ganancia <= 0:
        return []
    reglas = reglas_activas(db)
    if not reglas:
        return []
    aplicados: list[dict] = []
    acumulado = Decimal("0")
    ahora = datetime.now(timezone.utc)
    for i, regla in enumerate(reglas):
        if i < len(reglas) - 1:
            monto = (ganancia * regla.porcentaje / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            acumulado += monto
        else:
            monto = (ganancia - acumulado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        saldo = _saldo_bloqueado(db, regla.cuenta_destino)
        saldo.saldo = (Decimal(saldo.saldo) + monto).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        saldo.actualizado_en = ahora
        db.add(
            RepartoVenta(venta_id=venta.id, cuenta=regla.cuenta_destino, monto=monto)
        )
        aplicados.append({"cuenta": regla.cuenta_destino, "monto": monto})
    db.flush()
    return aplicados


def revertir_reparto_venta(db: Session, venta_id: int) -> int:
    """Negate a sale's applied split (no commit). Returns rows reverted."""
    filas = list(
        db.scalars(select(RepartoVenta).where(RepartoVenta.venta_id == venta_id))
    )
    for fila in filas:
        saldo = _saldo_bloqueado(db, fila.cuenta)
        saldo.saldo = (Decimal(saldo.saldo) - Decimal(fila.monto)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        saldo.actualizado_en = datetime.now(timezone.utc)
        db.delete(fila)
    if filas:
        db.flush()
    return len(filas)
