from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models import CompraInsumo, Usuario
from app.schemas.compra_insumo import CompraInsumoCreate, CompraInsumoRead
from app.services.wac import registrar_compra

router = APIRouter(prefix="/compras-insumos", tags=["compras-insumos"])

audited_user = require_roles("admin", "operador", "consulta")
mutation_user = require_roles("admin", "operador")


@router.post("", response_model=CompraInsumoRead, status_code=status.HTTP_201_CREATED)
def create_compra_insumo(
    payload: CompraInsumoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(mutation_user),
):
    compra = registrar_compra(
        db,
        insumo_id=payload.insumo_id,
        proveedor_id=payload.proveedor_id,
        cantidad=payload.cantidad_comprada,
        precio_unitario=payload.precio_unitario_compra,
    )
    return compra


@router.get("", response_model=list[CompraInsumoRead])
def list_compras_insumos(
    limit: int = 50,
    offset: int = 0,
    insumo_id: int | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    stmt = select(CompraInsumo)
    if insumo_id is not None:
        stmt = stmt.where(CompraInsumo.insumo_id == insumo_id)
    stmt = stmt.order_by(CompraInsumo.id).limit(limit).offset(offset)
    return db.scalars(stmt).all()