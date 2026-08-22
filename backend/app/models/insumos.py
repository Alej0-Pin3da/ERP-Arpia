from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CategoriaInsumo(Base):
    __tablename__ = "Categorias_Insumos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    insumos: Mapped[list[Insumo]] = relationship(back_populates="categoria", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CategoriaInsumo id={self.id} nombre={self.nombre!r}>"


class Insumo(Base):
    __tablename__ = "Insumos"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("Categorias_Insumos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    unidad_medida: Mapped[str] = mapped_column(String(50), nullable=False)
    stock_actual: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    stock_minimo: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    costo_promedio_actual: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )

    categoria: Mapped[CategoriaInsumo] = relationship(back_populates="insumos")
    compras: Mapped[list[CompraInsumo]] = relationship(back_populates="insumo", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Insumo id={self.id} nombre={self.nombre!r}>"


class CompraInsumo(Base):
    __tablename__ = "Compras_Insumos"

    id: Mapped[int] = mapped_column(primary_key=True)
    insumo_id: Mapped[int] = mapped_column(
        ForeignKey("Insumos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Proveedores entity was removed (0008_remove_proveedores). Keep column nullable
    # without FK so history can store an optional external reference; no constraint.
    proveedor_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    fecha_compra: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    cantidad_comprada: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    precio_unitario_compra: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    costo_unitario_aplicado: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    factura: Mapped[str | None] = mapped_column(String(100), nullable=True)

    insumo: Mapped[Insumo] = relationship(back_populates="compras")

    def __repr__(self) -> str:
        return f"<CompraInsumo id={self.id} insumo_id={self.insumo_id}>"
