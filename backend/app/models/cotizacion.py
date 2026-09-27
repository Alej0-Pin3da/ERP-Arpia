"""Cotizacion model — persisted quick quotes from the Cotizador.

A quote snapshots the inputs the user priced with (dynamic BOM line items
in ``insumos_detalle``, avíos, empaque, labor time/rate, CIF) plus the
server-computed results (costo_total, margen_pct, precio_sugerido,
ganancia_neta), so the number no longer dies in WhatsApp: it has history
and can later feed the product's ``precio_venta_sugerido``. ``codigo`` is
derived (COT-0001), never stored, mirroring ``Venta.codigo``.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Cotizacion(Base):
    __tablename__ = "Cotizaciones"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('borrador', 'enviada', 'aprobada', 'descartada')",
            name="ck_cotizaciones_estado",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("Clientes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    producto_id: Mapped[int | None] = mapped_column(
        ForeignKey("Productos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    nombre_prenda: Mapped[str] = mapped_column(String(255), nullable=False)
    # Dynamic BOM snapshot (immutable per quote): list of
    # {nombre, cantidad, precio_unitario, unidad_medida, desperdicio_pct}.
    # Replaces the old static tela/forro columns (dropped in migration).
    insumos_detalle: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, server_default="[]"
    )
    # Pricing inputs (snapshot of what the user priced with).
    costo_avios: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    costo_empaque: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    tiempo_confeccion_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tarifa_hora: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    costo_cif: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0"))
    margen_pct: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    # Estimación de hilos (informativa: el costo de hilos entra vía
    # costo_avios si se aplica).
    costo_hilo_m: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    metros_hilo: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    # Server-computed results (single source of truth, mirrors the frontend).
    costo_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    precio_sugerido: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    ganancia_neta: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="borrador", index=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    @property
    def codigo(self) -> str | None:
        return f"COT-{self.id:04d}" if self.id is not None else None

    def __repr__(self) -> str:
        return f"<Cotizacion id={self.id} estado={self.estado!r} precio={self.precio_sugerido}>"
