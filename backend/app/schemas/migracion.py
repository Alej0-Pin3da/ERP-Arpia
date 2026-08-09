"""Pydantic schemas for the omisiones API surface (MIG-3/MIG-4).

``OmisionRead`` mirrors the Migracion_Omisiones row for the paginated list
and the PATCH response; ``OmisionUpdate`` carries only ``resuelta`` (the
admin marks/unmarks a row as resolved).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OmisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    corrida_id: str | None
    fecha_corrida: datetime
    fase: str | None
    hoja: str | None
    fila: int | None
    celda: str | None
    nivel: str
    mensaje: str
    resuelta: bool
    creado_en: datetime


class OmisionUpdate(BaseModel):
    """PATCH body: mark/unmark the omission as resolved (MIG-4)."""

    resuelta: bool
