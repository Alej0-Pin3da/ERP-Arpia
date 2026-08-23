"""Audit API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    """Audit log read schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None
    usuario_rol: str
    entidad: str
    entity_id: int
    accion: str
    valores_old: dict[str, Any] | None
    valores_new: dict[str, Any] | None
    request_id: str | None
    ip: str | None
    user_agent: str | None
    timestamp: datetime


class AuditLogFilter(BaseModel):
    """Filter parameters for audit log queries."""

    usuario_id: int | None = None
    usuario_rol: str | None = None
    entidad: str | None = None
    entity_id: int | None = None
    accion: str | None = None
    fecha_desde: datetime | None = None
    fecha_hasta: datetime | None = None
    request_id: str | None = None
    limit: int = 50
    offset: int = 0
