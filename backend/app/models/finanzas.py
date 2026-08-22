from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentState(str, Enum):
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
    porcentaje_participacion: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
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
        String(20), nullable=False, server_default=DocumentState.CONFIRMED.value, default=DocumentState.CONFIRMED.value
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
        return f"<MovimientoFinanciero id={self.id} tipo={self.tipo!r} monto={self.monto} estado={self.estado!r}>"

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
