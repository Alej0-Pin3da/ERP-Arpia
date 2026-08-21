"""Audit service for structured audit logging."""
from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditService:
    """Service for creating audit log entries."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        *,
        usuario_id: int | None,
        usuario_rol: str,
        entidad: str,
        entity_id: int,
        accion: str,
        valores_old: dict[str, Any] | None = None,
        valores_new: dict[str, Any] | None = None,
        request_id: str | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create and persist an audit log entry."""
        audit = AuditLog(
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            entidad=entidad,
            entity_id=entity_id,
            accion=accion,
            valores_old=valores_old,
            valores_new=valores_new,
            request_id=request_id,
            ip=ip,
            user_agent=user_agent,
            timestamp=datetime.now(UTC),
        )
        self.db.add(audit)
        self.db.flush()
        return audit


def _get_request_context(request) -> dict[str, Any]:
    """Extract request context for audit logging."""
    return {
        "request_id": getattr(request.state, "request_id", None),
        "ip": getattr(request.client, "host", None) if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def _serialize_model(obj) -> dict[str, Any]:
    """Serialize SQLAlchemy model to dict for audit."""
    if obj is None:
        return {}
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        # Handle non-serializable types
        if hasattr(value, "isoformat"):  # datetime
            value = value.isoformat()
        result[column.name] = value
    return result


# Domain-specific audit helpers

def audit_venta_create(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    venta,
) -> None:
    """Audit venta creation."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="ventas",
        entity_id=venta.id,
        accion="create",
        valores_new=_serialize_model(venta),
        **ctx,
    )


def audit_venta_update(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    venta_id: int,
    old_values: dict[str, Any],
    new_values: dict[str, Any],
) -> None:
    """Audit venta update with old/new values."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="ventas",
        entity_id=venta_id,
        accion="update",
        valores_old=old_values,
        valores_new=new_values,
        **ctx,
    )


def audit_venta_delete(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    venta_id: int,
    deleted_values: dict[str, Any],
) -> None:
    """Audit venta deletion (anulacion)."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="ventas",
        entity_id=venta_id,
        accion="delete",
        valores_old=deleted_values,
        **ctx,
    )


def audit_devolucion_create(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    devolucion,
) -> None:
    """Audit devolucion creation."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="devoluciones",
        entity_id=devolucion.id,
        accion="create",
        valores_new=_serialize_model(devolucion),
        **ctx,
    )


def audit_compra_create(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    compra,
) -> None:
    """Audit compra insumo creation."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="compras_insumos",
        entity_id=compra.id,
        accion="create",
        valores_new=_serialize_model(compra),
        **ctx,
    )


def audit_movimiento_create(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    movimiento,
) -> None:
    """Audit movimiento financiero creation."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="finanzas_movimientos",
        entity_id=movimiento.id,
        accion="create",
        valores_new=_serialize_model(movimiento),
        **ctx,
    )


def audit_movimiento_update(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    movimiento_id: int,
    old_values: dict[str, Any],
    new_values: dict[str, Any],
) -> None:
    """Audit movimiento financiero update."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="finanzas_movimientos",
        entity_id=movimiento_id,
        accion="update",
        valores_old=old_values,
        valores_new=new_values,
        **ctx,
    )


def audit_movimiento_delete(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    movimiento_id: int,
    deleted_values: dict[str, Any],
) -> None:
    """Audit movimiento financiero deletion (soft delete)."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="finanzas_movimientos",
        entity_id=movimiento_id,
        accion="delete",
        valores_old=deleted_values,
        **ctx,
    )


def audit_usuario_create(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    usuario,
) -> None:
    """Audit usuario creation."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="usuarios",
        entity_id=usuario.id,
        accion="create",
        valores_new=_serialize_model(usuario),
        **ctx,
    )


def audit_usuario_update(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    target_usuario_id: int,
    old_values: dict[str, Any],
    new_values: dict[str, Any],
) -> None:
    """Audit usuario update."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    service.log(
        usuario_id=usuario_id,
        usuario_rol=usuario_rol,
        entidad="usuarios",
        entity_id=target_usuario_id,
        accion="update",
        valores_old=old_values,
        valores_new=new_values,
        **ctx,
    )


def audit_stock_adjust(
    db: Session,
    request,
    usuario_id: int,
    usuario_rol: str,
    adjustments: list[dict[str, Any]],
) -> None:
    """Audit stock adjustment (from migration or manual)."""
    service = AuditService(db)
    ctx = _get_request_context(request)
    for adj in adjustments:
        service.log(
            usuario_id=usuario_id,
            usuario_rol=usuario_rol,
            entidad="inventario_ajuste",
            entity_id=adj.get("insumo_id", 0),
            accion="ajuste_stock",
            valores_old={"stock_anterior": adj.get("stock_anterior")},
            valores_new={"stock_nuevo": adj.get("stock_nuevo"), "cambio": adj.get("cambio")},
            **ctx,
        )