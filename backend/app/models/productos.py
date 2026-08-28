from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TipoProducto(Base):
    __tablename__ = "Tipos_Producto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    productos: Mapped[list[Producto]] = relationship(
        back_populates="tipo_producto", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<TipoProducto id={self.id} nombre={self.nombre!r}>"


class Producto(Base):
    __tablename__ = "Productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_producto_id: Mapped[int] = mapped_column(
        ForeignKey("Tipos_Producto.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    requiere_fabricacion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    costos_operativos_fijos: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    precio_venta_sugerido: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )

    tipo_producto: Mapped[TipoProducto] = relationship(back_populates="productos")
    variantes: Mapped[list[VarianteProducto]] = relationship(
        back_populates="producto", lazy="selectin"
    )
    bom_insumos: Mapped[list[BomInsumo]] = relationship(back_populates="producto", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Producto id={self.id} nombre={self.nombre!r}>"


class VarianteProducto(Base):
    __tablename__ = "Variantes_Producto"
    __table_args__ = (
        UniqueConstraint("producto_id", "nombre_variante", name="uq_variantes_producto_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre_variante: Mapped[str] = mapped_column(String(150), nullable=False)
    precio_venta: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    producto: Mapped[Producto] = relationship(back_populates="variantes")

    def __repr__(self) -> str:
        return f"<VarianteProducto id={self.id} nombre={self.nombre_variante!r}>"


class BomInsumo(Base):
    __tablename__ = "BOM_Insumos"
    __table_args__ = (
        UniqueConstraint("producto_id", "insumo_id", "variante_id", name="uq_bom_insumos_combo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    insumo_id: Mapped[int] = mapped_column(
        ForeignKey("Insumos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    variante_id: Mapped[int | None] = mapped_column(
        ForeignKey("Variantes_Producto.id", ondelete="CASCADE"), nullable=True
    )
    cantidad_requerida: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    porcentaje_desperdicio: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    fases: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    tiempo_estimado_minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    markup_porcentual: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    producto: Mapped[Producto] = relationship(back_populates="bom_insumos")
    insumo: Mapped[Insumo] = relationship(lazy="selectin")  # noqa: F821
    variante: Mapped[VarianteProducto | None] = relationship()

    def __repr__(self) -> str:
        return f"<BomInsumo id={self.id} producto_id={self.producto_id} insumo_id={self.insumo_id}>"


class BomProducto(Base):
    __tablename__ = "BOM_Productos"
    __table_args__ = (
        UniqueConstraint("combo_id", "producto_incluido_id", name="uq_bom_productos_combo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    combo_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    producto_incluido_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    fases: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    tiempo_estimado_minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    markup_porcentual: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    combo: Mapped[Producto] = relationship(foreign_keys=[combo_id], backref="combo_items")
    producto_incluido: Mapped[Producto] = relationship(foreign_keys=[producto_incluido_id])

    def __repr__(self) -> str:
        return f"<BomProducto id={self.id} combo_id={self.combo_id}>"
