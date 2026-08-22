from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Cliente(TimestampMixin, Base):
    __tablename__ = "Clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    documento_identidad: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Cliente id={self.id} nombre={self.nombre!r}>"
