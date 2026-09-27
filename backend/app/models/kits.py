"""Kits (promotional boxes) — group several products under one commercial SKU.

A kit snapshots nothing: lines point at live ``Productos`` and the total
cost is always computed on the fly with ``calcular_costo_produccion``
(recursive BOM math), so a kit can never go stale when costs move. The
5% safety margin is validated at read time (visual alert, never a block).
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.productos import Producto

#: Minimum margin (utility over promo price) before a visual alert fires.
MARGEN_SEGURIDAD_KIT = Decimal("5")


class Kit(Base):
    __tablename__ = "Kits"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    precio_promocional: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    lineas: Mapped[list[KitProducto]] = relationship(
        back_populates="kit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Kit id={self.id} nombre={self.nombre!r}>"


class KitProducto(Base):
    __tablename__ = "Kit_Productos"
    __table_args__ = (
        UniqueConstraint("kit_id", "producto_id", name="uq_kit_productos_kit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kit_id: Mapped[int] = mapped_column(
        ForeignKey("Kits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("1")
    )

    kit: Mapped[Kit] = relationship(back_populates="lineas")
    producto: Mapped[Producto] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<KitProducto id={self.id} kit_id={self.kit_id} "
            f"producto_id={self.producto_id} cantidad={self.cantidad}>"
        )
