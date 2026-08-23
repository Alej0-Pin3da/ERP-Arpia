from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, require_roles
from app.core.limiter import user_limiter
from app.models import CompraInsumo, Insumo, Usuario
from app.schemas.common import Paginated
from app.schemas.compra_insumo import CompraInsumoCreate, CompraInsumoRead
from app.services.paginacion import aplicar_orden, paginar
from app.services.audit import audit_compra_create
from app.services.wac import registrar_compra

router = APIRouter(prefix="/compras-insumos", tags=["compras-insumos"])

# Rate limiter for critical write endpoints
_critical_limiter = user_limiter if settings.ENVIRONMENT != "test" else Limiter(key_func=lambda r: "test", enabled=False)

audited_user = require_roles("admin", "operador", "consulta")
mutation_user = require_roles("admin", "operador")

# Whitelisted server-side sort keys. insumo is a joined column.
_SORTABLE_COMPRAS = {
    "id": CompraInsumo.id,
    "fecha_compra": CompraInsumo.fecha_compra,
    "cantidad_comprada": CompraInsumo.cantidad_comprada,
    "precio_unitario_compra": CompraInsumo.precio_unitario_compra,
    "insumo": Insumo.nombre,
}


@router.post("", response_model=CompraInsumoRead, status_code=status.HTTP_201_CREATED)
@_critical_limiter.limit("30/minute")
def create_compra_insumo(
    request: Request,
    payload: CompraInsumoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(mutation_user),
):
    # Proveedor validation: Proveedores was removed (0008). If proveedor_id is provided,
    # treat as 400 unless the table exists and the id is found. This keeps the
    # spec's 400 contract while respecting the current schema without FK.
    if payload.proveedor_id is not None:
        try:
            has_table = db.execute(text("SELECT to_regclass('public.Proveedores')")).scalar()
        except Exception:
            has_table = None
        if has_table is None:
            raise HTTPException(status_code=400, detail="Proveedor not found")
        # Table exists — verify id exists via raw SQL to avoid model import
        found = db.execute(
            text("SELECT 1 FROM \"Proveedores\" WHERE id = :pid"),
            {"pid": payload.proveedor_id},
        ).scalar()
        if not found:
            raise HTTPException(status_code=400, detail="Proveedor not found")

    compra = registrar_compra(
        db,
        insumo_id=payload.insumo_id,
        cantidad=payload.cantidad_comprada,
        precio_unitario=payload.precio_unitario_compra,
        costo_total=payload.costo_total,
        modo=payload.modo,
        factura=payload.factura,
        proveedor_id=payload.proveedor_id,
    )
    compra_id = compra.id
    try:
        audit_compra_create(db, request, current_user.id, current_user.rol, compra)
        db.commit()
    except Exception:
        pass
    compra = db.get(CompraInsumo, compra_id)
    return compra


@router.get("", response_model=Paginated[CompraInsumoRead])
@user_limiter.limit("300/minute")
def list_compras_insumos(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    insumo_id: int | None = None,
    q: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    # Single join build for BOTH filtering and sorting: SQLAlchemy does not
    # dedupe repeated joins, so Insumo is joined exactly once.
    stmt = select(CompraInsumo).join(CompraInsumo.insumo)
    if insumo_id is not None:
        stmt = stmt.where(CompraInsumo.insumo_id == insumo_id)
    if q is not None:
        stmt = stmt.where(Insumo.nombre.ilike(f"%{q}%"))
    # Default ordering: fecha_compra DESC for history (REQ-CI-003). Custom sort
    # via sort_by/order still allowed through aplicar_orden.
    if sort_by is None:
        stmt = stmt.order_by(CompraInsumo.fecha_compra.desc(), CompraInsumo.id.desc())
    else:
        stmt = stmt.order_by(CompraInsumo.id)
        stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_COMPRAS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[CompraInsumoRead](items=list(rows), total=total)