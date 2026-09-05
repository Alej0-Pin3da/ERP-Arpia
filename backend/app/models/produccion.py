from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.clientes import Cliente
from app.models.productos import Producto, VarianteProducto


class PrendaEstado(StrEnum):
    DISPONIBLE = "disponible"
    RESERVADA = "reservada"
    VENDIDA = "vendida"
    DEFECTUOSA = "defectuosa"


class PedidoProduccionEstado(StrEnum):
    PENDIENTE = "pendiente"
    EN_PRODUCCION = "en_produccion"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"


class PedidoProduccionPrioridad(StrEnum):
    BAJA = "baja"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"


class PedidoProduccion(Base):
    __tablename__ = "pedidos_produccion"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'en_produccion', 'completado', 'cancelado')",
            name="ck_pedidos_produccion_estado",
        ),
        CheckConstraint(
            "prioridad IN ('baja', 'normal', 'alta', 'urgente')",
            name="ck_pedidos_produccion_prioridad",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("Productos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Clienta que realiza el pedido (0026, nullable: pedidos de mostrador sin cliente).
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("Clientes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    variante_id: Mapped[int | None] = mapped_column(
        ForeignKey("Variantes_Producto.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_producida: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default=PedidoProduccionEstado.PENDIENTE)
    prioridad: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PedidoProduccionPrioridad.NORMAL
    )
    fecha_pedido: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    fecha_entrega_estimada: Mapped[date | None] = mapped_column(Date, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    producto: Mapped[Producto] = relationship(lazy="selectin")
    variante: Mapped[VarianteProducto | None] = relationship(lazy="selectin")
    cliente: Mapped[Cliente | None] = relationship(lazy="selectin")
    prendas: Mapped[list[PrendaConfeccionada]] = relationship(
        back_populates="pedido", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<PedidoProduccion id={self.id} producto_id={self.producto_id} estado={self.estado!r}>"


class PrendaConfeccionada(Base):
    __tablename__ = "prendas_confeccionadas"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('disponible', 'reservada', 'vendida', 'defectuosa')",
            name="ck_prendas_confeccionadas_estado",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    variante_id: Mapped[int | None] = mapped_column(
        ForeignKey("Variantes_Producto.id", ondelete="CASCADE"), nullable=True, index=True
    )
    talla: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default=PrendaEstado.DISPONIBLE)
    ubicacion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    costo_real: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    precio_venta: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    fecha_confeccion: Mapped[date | None] = mapped_column(Date, nullable=True)
    pedido_id: Mapped[int | None] = mapped_column(
        ForeignKey("pedidos_produccion.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    variante: Mapped[VarianteProducto | None] = relationship(lazy="selectin")
    pedido: Mapped[PedidoProduccion | None] = relationship(
        back_populates="prendas", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<PrendaConfeccionada id={self.id} variante_id={self.variante_id} estado={self.estado!r}>"
