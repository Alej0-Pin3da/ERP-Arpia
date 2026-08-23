"""Audit log model for tracking all critical operations."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.usuarios import Usuario


class AuditLog(Base):
    """Immutable audit log entry for critical operations.

    Captures: user, role, entity, entity_id, action, old/new values,
    request_id, IP, user-agent, timestamp.
    """

    __tablename__ = "AuditLog"
    __table_args__ = (
        Index("ix_auditlog_entidad_entity_id", "entidad", "entity_id"),
        Index("ix_auditlog_usuario_fecha", "usuario_id", "timestamp"),
        Index("ix_auditlog_entidad_accion_fecha", "entidad", "accion", "timestamp"),
        Index("ix_auditlog_request_id", "request_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Who performed the action
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("Usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    usuario_rol: Mapped[str] = mapped_column(String(20), nullable=False)

    # What was affected
    entidad: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # What action
    accion: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Old and new values (JSON for flexibility)
    valores_old: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    valores_new: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Request context
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max length
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # When
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationship (optional, for eager loading)
    usuario: Mapped[Usuario | None] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} entidad={self.entidad} entity_id={self.entity_id} "
            f"accion={self.accion} usuario_id={self.usuario_id}>"
        )