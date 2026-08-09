"""Migracion_Omisiones model (spec MIG-1).

Persists every WARN/ERROR entry a migration run reports in commit mode
(see ``migrate.omisiones.persistir_omisiones``). ``fecha_corrida`` records
when the run happened; ``creado_en`` when the row was stored. ``nivel`` is
constrained to WARN|ERROR so the API filter can rely on the Literal.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MigracionOmision(Base):
    __tablename__ = "Migracion_Omisiones"
    __table_args__ = (
        CheckConstraint(
            "nivel IN ('WARN', 'ERROR')",
            name="ck_migracion_omisiones_nivel",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    corrida_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fecha_corrida: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fase: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hoja: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fila: Mapped[int | None] = mapped_column(Integer, nullable=True)
    celda: Mapped[str | None] = mapped_column(String(16), nullable=True)
    nivel: Mapped[str] = mapped_column(String(8), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    resuelta: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=func.false(), default=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<MigracionOmision id={self.id} nivel={self.nivel!r} corrida={self.corrida_id!r}>"
