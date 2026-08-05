from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SociosConfiguracion(Base):
    __tablename__ = "Socios_Configuracion"
    __table_args__ = (
        CheckConstraint(
            "porcentaje_participacion > 0",
            name="ck_socios_participacion_positiva",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    porcentaje_participacion: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False
    )
    # Multi-row invariant "sum of percentages == 100" cannot be enforced as a
    # single-row CHECK constraint in PostgreSQL; it is validated in the service layer,
    # not in SQL. The check above only guarantees each row is positive.

    def __repr__(self) -> str:
        return f"<SociosConfiguracion id={self.id} nombre={self.nombre!r}>"


class MovimientoFinanciero(Base):
    __tablename__ = "Movimientos_Financieros"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('Gasto', 'Inversion', 'Retiro')",
            name="ck_movimientos_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    socio_id: Mapped[int | None] = mapped_column(
        ForeignKey("Socios_Configuracion.id", ondelete="SET NULL"), nullable=True
    )

    socio: Mapped[SociosConfiguracion | None] = relationship()

    def __repr__(self) -> str:
        return f"<MovimientoFinanciero id={self.id} tipo={self.tipo!r} monto={self.monto}>"