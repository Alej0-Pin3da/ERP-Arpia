from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Cliente(TimestampMixin, Base):
    __tablename__ = "Clientes"
    __table_args__ = (
        Index("ix_clientes_tipo", "tipo"),
        Index("ix_clientes_ciudad", "ciudad"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    documento_identidad: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # CRM extension — 10 nullable cols (0009)
    ciudad: Mapped[str | None] = mapped_column(String(80), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    talla_habitual: Mapped[str | None] = mapped_column(String(10), nullable=True)
    talla_superior: Mapped[str | None] = mapped_column(String(10), nullable=True)
    talla_inferior: Mapped[str | None] = mapped_column(String(10), nullable=True)
    categoria_preferida: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tipo_producto_frecuente: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    medidas: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<Cliente id={self.id} nombre={self.nombre!r}>"
