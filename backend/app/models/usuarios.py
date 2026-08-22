from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.refresh_token import RefreshToken


class Usuario(Base):
    __tablename__ = "Usuarios"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('admin', 'operador', 'consulta')",
            name="ck_usuarios_rol",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="consulta")

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email!r} rol={self.rol!r}>"
