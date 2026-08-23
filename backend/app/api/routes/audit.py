"""Audit API routes — read-only access to audit logs."""
from datetime import date, datetime, time
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.audit import AuditLog
from app.models.usuarios import Usuario
from app.schemas.audit import AuditLogRead
from app.schemas.common import Paginated
from app.services.paginacion import paginar

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

# All authenticated roles can read audit logs
audited_user = require_roles("admin", "operador", "consulta")


@router.get("", response_model=Paginated[AuditLogRead])
def list_audit_logs(
    usuario_id: int | None = Query(default=None, description="Filter by user ID"),
    usuario_rol: str | None = Query(default=None, description="Filter by user role"),
    entidad: str | None = Query(default=None, description="Filter by entity"),
    entity_id: int | None = Query(default=None, description="Filter by entity ID"),
    accion: str | None = Query(default=None, description="Filter by action"),
    fecha_desde: datetime | date | None = Query(default=None, description="Filter from date (YYYY-MM-DD or ISO datetime)"),
    fecha_hasta: datetime | date | None = Query(default=None, description="Filter to date (YYYY-MM-DD or ISO datetime)"),
    request_id: str | None = Query(default=None, description="Filter by request ID"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """List audit logs with filters and pagination.

    Read-only endpoint accessible to all authenticated roles.
    """
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if usuario_id is not None:
        stmt = stmt.where(AuditLog.usuario_id == usuario_id)
    if usuario_rol is not None:
        stmt = stmt.where(AuditLog.usuario_rol == usuario_rol)
    if entidad is not None:
        stmt = stmt.where(AuditLog.entidad == entidad)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if accion is not None:
        stmt = stmt.where(AuditLog.accion == accion)
    if fecha_desde is not None:
        # Accept date-only (YYYY-MM-DD) as midnight start of day
        if isinstance(fecha_desde, date) and not isinstance(fecha_desde, datetime):
            fecha_desde = datetime.combine(fecha_desde, time.min)
        stmt = stmt.where(AuditLog.timestamp >= fecha_desde)
    if fecha_hasta is not None:
        # Accept date-only as end of day inclusive
        if isinstance(fecha_hasta, date) and not isinstance(fecha_hasta, datetime):
            fecha_hasta = datetime.combine(fecha_hasta, time.max)
        stmt = stmt.where(AuditLog.timestamp <= fecha_hasta)
    if request_id is not None:
        stmt = stmt.where(AuditLog.request_id == request_id)

    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[AuditLogRead](items=list(rows), total=total)


@router.get("/entidades", response_model=list[str])
def list_audit_entidades(
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Get list of distinct entities that have audit logs."""
    stmt = select(AuditLog.entidad).distinct().order_by(AuditLog.entidad)
    return [row[0] for row in db.execute(stmt).all()]


@router.get("/acciones", response_model=list[str])
def list_audit_acciones(
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Get list of distinct actions that have audit logs."""
    stmt = select(AuditLog.accion).distinct().order_by(AuditLog.accion)
    return [row[0] for row in db.execute(stmt).all()]


@router.get("/{audit_id}", response_model=AuditLogRead)
def get_audit_log(
    audit_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    """Get single audit log by ID."""
    audit = db.get(AuditLog, audit_id)
    if audit is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audit log not found")
    return audit