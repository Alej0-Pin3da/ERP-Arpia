"""Automatic profit split (V6 M2) — real-time balances without Excel.

Every confirmed sale distributes its ``ganancia_neta`` across the active
``Reglas_Liquidacion`` rows inside the SAME atomic transaction that creates
(or reverses) it. ``Saldos_Socias`` is the running balance per account;
``Reparto_Ventas`` is the per-sale audit ledger that makes reversals exact.

Design notes:
- Gifts and zero/negative-gain sales distribute nothing (nothing to split).
- No rules configured -> sales register normally, no split (documented).
- These are LIVE informational balances. The official monthly settlement
  stays ``crear_liquidacion`` — no money moves here, so nothing double-pays.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ventas import Venta


class ReglaLiquidacion(Base):
    __tablename__ = "Reglas_Liquidacion"
    __table_args__ = (
        UniqueConstraint("cuenta_destino", name="uq_reglas_liquidacion_cuenta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cuenta_destino: Mapped[str] = mapped_column(String(100), nullable=False)
    porcentaje: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<ReglaLiquidacion id={self.id} cuenta={self.cuenta_destino!r} pct={self.porcentaje}>"


class SaldoSocia(Base):
    __tablename__ = "Saldos_Socias"
    __table_args__ = (
        UniqueConstraint("cuenta", name="uq_saldos_socias_cuenta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cuenta: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    saldo: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SaldoSocia cuenta={self.cuenta!r} saldo={self.saldo}>"


class RepartoVenta(Base):
    __tablename__ = "Reparto_Ventas"
    __table_args__ = (
        UniqueConstraint("venta_id", "cuenta", name="uq_reparto_ventas_venta_cuenta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("Ventas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cuenta: Mapped[str] = mapped_column(String(100), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    venta: Mapped[Venta] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<RepartoVenta venta_id={self.venta_id} cuenta={self.cuenta!r} monto={self.monto}>"
