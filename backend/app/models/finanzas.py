from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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


class LiquidacionEstado(StrEnum):
    BORRADOR = "BORRADOR"
    APROBADA = "APROBADA"
    PAGADA = "PAGADA"


class DistribucionEstado(StrEnum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"
    RETENIDO = "RETENIDO"


class AnticipoEstado(StrEnum):
    PENDIENTE_DESCUENTO = "PENDIENTE_DESCUENTO"
    DESCONTADO = "DESCONTADO"
    ANULADO = "ANULADO"


LIQUIDACION_TRANSITIONS: dict[LiquidacionEstado, list[LiquidacionEstado]] = {
    LiquidacionEstado.BORRADOR: [LiquidacionEstado.APROBADA],
    LiquidacionEstado.APROBADA: [LiquidacionEstado.PAGADA],
    LiquidacionEstado.PAGADA: [],
}

ANTICIPO_TRANSITIONS: dict[AnticipoEstado, list[AnticipoEstado]] = {
    AnticipoEstado.PENDIENTE_DESCUENTO: [AnticipoEstado.DESCONTADO, AnticipoEstado.ANULADO],
    AnticipoEstado.DESCONTADO: [],
    AnticipoEstado.ANULADO: [],
}


class SociosConfiguracion(Base):
    __tablename__ = "Socios_Configuracion"
    __table_args__ = (
        CheckConstraint(
            "porcentaje_participacion > 0",
            name="ck_socios_participacion_positiva",
        ),
        Index("ix_socios_rol", "rol"),
        Index("ix_socios_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    porcentaje_participacion: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    # Extended profile — 10 nullable cols matching SociaAtelier
    rol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    banco: Mapped[str | None] = mapped_column(String(100), nullable=True)
    es_fondo_taller: Mapped[bool | None] = mapped_column(nullable=True, server_default=text("false"), default=False)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tipo_cuenta: Mapped[str | None] = mapped_column(String(50), nullable=True)
    numero_cuenta: Mapped[str | None] = mapped_column(String(50), nullable=True)
    titular_cuenta: Mapped[str | None] = mapped_column(String(150), nullable=True)
    activo: Mapped[bool | None] = mapped_column(nullable=True, server_default=text("true"), default=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        CheckConstraint(
            "estado IN ('draft', 'confirmed', 'cancelled', 'reversed')",
            name="ck_movimientos_estado",
        ),
        # One-time settlement guard: a liquidacion_id may be used at most once.
        Index(
            "uq_liquidacion",
            "liquidacion_id",
            unique=True,
            postgresql_where=text("liquidacion_id IS NOT NULL"),
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
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=DocumentState.CONFIRMED.value,
        default=DocumentState.CONFIRMED.value,
    )
    liquidacion_id: Mapped[str | None] = mapped_column(String(12), nullable=True)
    # Reversal tracking
    reversed_motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    reversed_by: Mapped[int | None] = mapped_column(
        ForeignKey("Usuarios.id", ondelete="SET NULL"), nullable=True
    )
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    socio: Mapped[SociosConfiguracion | None] = relationship()
    reversed_by_user: Mapped[Usuario | None] = relationship(lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<MovimientoFinanciero id={self.id} tipo={self.tipo!r} "
            f"monto={self.monto} estado={self.estado!r}>"
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
            from datetime import timezone

            self.reversed_at = datetime.now(timezone.utc)


class Liquidacion(Base):
    __tablename__ = "liquidaciones"
    __table_args__ = (
        CheckConstraint("estado IN ('BORRADOR', 'APROBADA', 'PAGADA')", name="ck_liquidaciones_estado"),
        UniqueConstraint("codigo", name="uq_liquidaciones_codigo"),
        Index("ix_liquidaciones_periodo", "periodo"),
        Index("ix_liquidaciones_estado", "estado"),
        Index("ix_liquidaciones_codigo", "codigo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_cierre: Mapped[datetime] = mapped_column(Date(), nullable=False)
    total_ventas_brutas: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    costo_taller_insumos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gastos_operativos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    utilidad_neta_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fondo_reinversion_monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    utilidad_repartible: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'BORRADOR'"), default=LiquidacionEstado.BORRADOR.value)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    distribucion: Mapped[list["LiquidacionDistribucion"]] = relationship(back_populates="liquidacion", cascade="all, delete-orphan", lazy="selectin")

    def can_transition_to(self, new_state: LiquidacionEstado) -> bool:
        current = LiquidacionEstado(self.estado)
        return new_state in LIQUIDACION_TRANSITIONS.get(current, [])

    def transition_to(self, new_state: LiquidacionEstado) -> None:
        if not self.can_transition_to(new_state):
            raise ValueError(f"Invalid liquidacion transition: {self.estado} -> {new_state.value}")
        self.estado = new_state.value

    def __repr__(self) -> str:
        return f"<Liquidacion id={self.id} codigo={self.codigo!r} estado={self.estado!r}>"


class LiquidacionDistribucion(Base):
    __tablename__ = "liquidacion_distribucion"
    __table_args__ = (
        CheckConstraint("estado_pago IN ('PENDIENTE', 'PAGADO', 'RETENIDO')", name="ck_distribucion_estado_pago"),
        UniqueConstraint("liquidacion_id", "socia_id", name="uq_distribucion_liquidacion_socia"),
        Index("ix_distribucion_liquidacion_id", "liquidacion_id"),
        Index("ix_distribucion_socia_id", "socia_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    liquidacion_id: Mapped[int] = mapped_column(ForeignKey("liquidaciones.id", ondelete="CASCADE"), nullable=False)
    socia_id: Mapped[int] = mapped_column(ForeignKey("Socios_Configuracion.id", ondelete="CASCADE"), nullable=False)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    monto_bruto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deduccion_anticipos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"), default=Decimal("0"))
    monto_neto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado_pago: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'PENDIENTE'"), default=DistribucionEstado.PENDIENTE.value)

    liquidacion: Mapped[Liquidacion] = relationship(back_populates="distribucion")
    socia: Mapped[SociosConfiguracion] = relationship()

    def __repr__(self) -> str:
        return f"<LiquidacionDistribucion liq={self.liquidacion_id} socia={self.socia_id} neto={self.monto_neto}>"


class Anticipo(Base):
    __tablename__ = "anticipos"
    __table_args__ = (
        CheckConstraint("monto > 0", name="ck_anticipos_monto_positivo"),
        CheckConstraint("estado IN ('PENDIENTE_DESCUENTO', 'DESCONTADO', 'ANULADO')", name="ck_anticipos_estado"),
        Index("ix_anticipos_socia_fecha", "socia_id", "fecha"),
        Index("ix_anticipos_estado", "estado"),
        Index("ix_anticipos_liquidacion_id", "liquidacion_id"),
        Index("ix_anticipos_socia_liquidacion", "socia_id", "liquidacion_id", unique=True, postgresql_where=text("liquidacion_id IS NOT NULL")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    socia_id: Mapped[int] = mapped_column(ForeignKey("Socios_Configuracion.id", ondelete="CASCADE"), nullable=False)
    liquidacion_id: Mapped[int | None] = mapped_column(ForeignKey("liquidaciones.id", ondelete="SET NULL"), nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha: Mapped[datetime] = mapped_column(Date(), nullable=False, server_default=text("CURRENT_DATE"))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'PENDIENTE_DESCUENTO'"), default=AnticipoEstado.PENDIENTE_DESCUENTO.value)
    concepto: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metodo_desembolso: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comprobante: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    socia: Mapped[SociosConfiguracion] = relationship()
    liquidacion: Mapped[Liquidacion | None] = relationship()

    def can_transition_to(self, new_state: AnticipoEstado) -> bool:
        current = AnticipoEstado(self.estado)
        return new_state in ANTICIPO_TRANSITIONS.get(current, [])

    def transition_to(self, new_state: AnticipoEstado) -> None:
        if not self.can_transition_to(new_state):
            raise ValueError(f"Invalid anticipo transition: {self.estado} -> {new_state.value}")
        self.estado = new_state.value

    def __repr__(self) -> str:
        return f"<Anticipo id={self.id} socia={self.socia_id} monto={self.monto} estado={self.estado!r}>"
