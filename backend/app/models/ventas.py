from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.productos import Producto, VarianteProducto


class Venta(Base):
    __tablename__ = "Ventas"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('completada', 'anulada')",
            name="ck_ventas_estado",
        ),
        CheckConstraint(
            "canal_venta IN ('web', 'whatsapp', 'instagram', 'feria')",
            name="ck_ventas_canal_venta",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("Clientes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    canal_venta: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="feria", default="feria", index=True
    )
    descuento_porcentaje: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completada", index=True
    )
    total_venta: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    es_regalo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    cliente: Mapped[Cliente | None] = relationship(lazy="selectin")  # noqa: F821
    detalles: Mapped[list[DetalleVenta]] = relationship(back_populates="venta", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Venta id={self.id} estado={self.estado!r} total={self.total_venta}>"


class DetalleVenta(Base):
    __tablename__ = "Detalle_Ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("Ventas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    variante_id: Mapped[int | None] = mapped_column(
        ForeignKey("Variantes_Producto.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    precio_unitario_aplicado: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    costo_unitario_aplicado: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )

    venta: Mapped[Venta] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship(lazy="selectin")
    variante: Mapped[VarianteProducto | None] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<DetalleVenta id={self.id} venta_id={self.venta_id}>"


class Devolucion(Base):
    __tablename__ = "Devoluciones"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('parcial', 'total')",
            name="ck_devoluciones_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("Ventas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    monto_reembolsado: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="parcial", default="parcial"
    )
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("Usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )

    venta: Mapped[Venta] = relationship()
    items: Mapped[list[DevolucionItem]] = relationship(back_populates="devolucion", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Devolucion id={self.id} venta_id={self.venta_id} tipo={self.tipo!r}>"


class DevolucionItem(Base):
    __tablename__ = "Items_Devolucion"

    id: Mapped[int] = mapped_column(primary_key=True)
    devolucion_id: Mapped[int] = mapped_column(
        ForeignKey("Devoluciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    variante_id: Mapped[int | None] = mapped_column(
        ForeignKey("Variantes_Producto.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    devolucion: Mapped[Devolucion] = relationship(back_populates="items")
    producto: Mapped[Producto] = relationship(lazy="selectin")
    variante: Mapped[VarianteProducto | None] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<DevolucionItem id={self.id} devolucion_id={self.devolucion_id}>"
