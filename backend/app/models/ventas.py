from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

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


class DocumentState(StrEnum):
    """Valid document states with enforced transitions."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


# Valid state transitions: from_state -> allowed next states
VALID_TRANSITIONS: dict[DocumentState, list[DocumentState]] = {
    DocumentState.DRAFT: [DocumentState.CONFIRMED, DocumentState.CANCELLED],
    DocumentState.CONFIRMED: [DocumentState.CANCELLED, DocumentState.REVERSED],
    DocumentState.CANCELLED: [DocumentState.REVERSED],
    DocumentState.REVERSED: [],  # Terminal state
}


class Venta(Base):
    __tablename__ = "Ventas"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('draft', 'confirmed', 'cancelled', 'reversed')",
            name="ck_ventas_estado",
        ),
        CheckConstraint(
            "canal_venta IN ('web', 'whatsapp', 'instagram', 'feria', 'showroom_pereira')",
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
        String(50), nullable=False, server_default="feria", default="feria", index=True
    )
    metodo_pago: Mapped[str | None] = mapped_column(String(50), nullable=True)
    descuento_porcentaje: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DocumentState.CONFIRMED.value, index=True
    )
    total_venta: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )
    es_regalo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    # Reversal tracking
    reversed_motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    reversed_by: Mapped[int | None] = mapped_column(
        ForeignKey("Usuarios.id", ondelete="SET NULL"), nullable=True
    )
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cliente: Mapped[Cliente | None] = relationship(lazy="selectin")  # noqa: F821
    detalles: Mapped[list[DetalleVenta]] = relationship(back_populates="venta", lazy="selectin")
    reversed_by_user: Mapped[Usuario | None] = relationship(lazy="selectin")  # noqa: F821

    @property
    def cliente_nombre(self) -> str | None:
        return self.cliente.nombre if self.cliente is not None else None

    @property
    def codigo(self) -> str | None:
        return f"VEN-{self.id:04d}" if self.id is not None else None

    @property
    def subtotal(self) -> Decimal:
        """Suma bruta de detalles antes de descuento."""
        total = Decimal("0")
        for d in self.detalles or []:
            try:
                total += (d.cantidad or Decimal("0")) * (d.precio_unitario_aplicado or Decimal("0"))
            except Exception:
                continue
        return total

    @property
    def costo_total(self) -> Decimal:
        total = Decimal("0")
        for d in self.detalles or []:
            try:
                total += (d.cantidad or Decimal("0")) * (d.costo_unitario_aplicado or Decimal("0"))
            except Exception:
                continue
        return total

    @property
    def ganancia_neta(self) -> Decimal:
        try:
            return (self.total_venta or Decimal("0")) - self.costo_total
        except Exception:
            return Decimal("0")

    @property
    def margen_pct(self) -> Decimal:
        try:
            total = self.total_venta or Decimal("0")
            if total == 0:
                return Decimal("0")
            return (self.ganancia_neta / total * Decimal("100")).quantize(Decimal("0.1"))
        except Exception:
            return Decimal("0")

    @property
    def reinversion_40(self) -> Decimal:
        try:
            return (self.ganancia_neta * Decimal("0.4")).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0")

    @property
    def margarita_30(self) -> Decimal:
        try:
            return (self.ganancia_neta * Decimal("0.3")).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0")

    @property
    def valqui_30(self) -> Decimal:
        try:
            return (self.ganancia_neta * Decimal("0.3")).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0")

    def __repr__(self) -> str:
        return f"<Venta id={self.id} estado={self.estado!r} total={self.total_venta}>"

    def can_transition_to(self, new_state: DocumentState) -> bool:
        """Check if transition from current state to new_state is valid."""
        current = DocumentState(self.estado)
        return new_state in VALID_TRANSITIONS.get(current, [])

    def transition_to(
        self,
        new_state: DocumentState,
        *,
        motivo: str | None = None,
        reversed_by: int | None = None,
    ) -> None:
        """Transition to new state with validation and audit fields."""
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition: {self.estado} -> {new_state.value}. "
                f"Valid: {[s.value for s in VALID_TRANSITIONS.get(DocumentState(self.estado), [])]}"
            )
        self.estado = new_state.value
        if new_state == DocumentState.REVERSED:
            if not motivo:
                raise ValueError("Reversal requires a motivo (reason)")
            self.reversed_motivo = motivo
            self.reversed_by = reversed_by
            self.reversed_at = datetime.now(datetime.UTC)


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

    @property
    def nombre_prenda(self) -> str | None:
        return self.producto.nombre if self.producto is not None else None

    @property
    def talla(self) -> str | None:
        # VarianteProducto only has nombre_variante (e.g. "M", "S - Rojo")
        return self.variante.nombre_variante if self.variante is not None else None

    @property
    def nombre_variante(self) -> str | None:
        return self.variante.nombre_variante if self.variante is not None else None

    @property
    def color(self) -> str | None:
        # No separate color column; keep None so frontend falls back to '—'
        return None

    @property
    def subtotal(self) -> Decimal:
        try:
            return (self.cantidad or Decimal("0")) * (self.precio_unitario_aplicado or Decimal("0"))
        except Exception:
            return Decimal("0")

    @property
    def costo_subtotal(self) -> Decimal:
        try:
            return (self.cantidad or Decimal("0")) * (self.costo_unitario_aplicado or Decimal("0"))
        except Exception:
            return Decimal("0")

    def __repr__(self) -> str:
        return f"<DetalleVenta id={self.id} venta_id={self.venta_id}>"


class Devolucion(Base):
    __tablename__ = "Devoluciones"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('parcial', 'total')",
            name="ck_devoluciones_tipo",
        ),
        CheckConstraint(
            "estado IN ('draft', 'confirmed', 'cancelled', 'reversed')",
            name="ck_devoluciones_estado",
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
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DocumentState.CONFIRMED.value, index=True
    )
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("Usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Reversal tracking
    reversed_motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    reversed_by: Mapped[int | None] = mapped_column(
        ForeignKey("Usuarios.id", ondelete="SET NULL"), nullable=True
    )
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    venta: Mapped[Venta] = relationship()
    items: Mapped[list[DevolucionItem]] = relationship(back_populates="devolucion", lazy="selectin")
    reversed_by_user: Mapped[Usuario | None] = relationship(  # noqa: F821
        foreign_keys="[Devolucion.reversed_by]", lazy="selectin"
    )
    usuario: Mapped[Usuario | None] = relationship(  # noqa: F821
        foreign_keys="[Devolucion.usuario_id]", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<Devolucion id={self.id} venta_id={self.venta_id} "
            f"tipo={self.tipo!r} estado={self.estado!r}>"
        )

    def can_transition_to(self, new_state: DocumentState) -> bool:
        """Check if transition from current state to new_state is valid."""
        current = DocumentState(self.estado)
        return new_state in VALID_TRANSITIONS.get(current, [])

    def transition_to(
        self,
        new_state: DocumentState,
        *,
        motivo: str | None = None,
        reversed_by: int | None = None,
    ) -> None:
        """Transition to new state with validation and audit fields."""
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition: {self.estado} -> {new_state.value}. "
                f"Valid: {[s.value for s in VALID_TRANSITIONS.get(DocumentState(self.estado), [])]}"
            )
        self.estado = new_state.value
        if new_state == DocumentState.REVERSED:
            if not motivo:
                raise ValueError("Reversal requires a motivo (reason)")
            self.reversed_motivo = motivo
            self.reversed_by = reversed_by
            self.reversed_at = datetime.now(datetime.UTC)


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
