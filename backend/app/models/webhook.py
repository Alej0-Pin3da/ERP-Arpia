"""Inbound webhook receipts (V6 M3).

One row per external event (WooCommerce order id). The UNIQUE
(source, external_id) pair is the idempotency guard: a duplicate delivery
acks with the already-created sale instead of selling twice.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ventas import Venta


class WebhookEvento(Base):
    __tablename__ = "Webhook_Eventos"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_webhook_eventos_source_ext"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="woo")
    external_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    venta_id: Mapped[int | None] = mapped_column(
        ForeignKey("Ventas.id", ondelete="SET NULL"), nullable=True
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="procesado")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    venta: Mapped[Venta | None] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<WebhookEvento source={self.source!r} external_id={self.external_id!r} "
            f"venta_id={self.venta_id}>"
        )
