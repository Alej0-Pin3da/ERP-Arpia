from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.ventas import Venta
from app.schemas.venta import VentaCreate, VentaRead
from app.services.inventory import registrar_venta

router = APIRouter(prefix="/ventas", tags=["ventas"])

mutation_user = require_roles("admin", "operador")
audited_user = require_roles("admin", "operador", "consulta")


@router.post("", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
def create_venta(
    payload: VentaCreate,
    db: Session = Depends(get_db),
    _: Venta = Depends(mutation_user),
):
    # registrar_venta takes a plain dict; HTTPException->HTTP mapping is
    # handled there (404 missing producto/cliente, 400 foreign variant,
    # 409 insufficient stock). Invalid payloads (canal/cantidad/descuento)
    # are rejected by pydantic -> 422 before this runs.
    venta: Venta = registrar_venta(db, payload.model_dump())
    return venta


@router.get("", response_model=list[VentaRead])
def list_ventas(
    db: Session = Depends(get_db),
    _: Venta = Depends(audited_user),
):
    stmt = select(Venta).order_by(Venta.id)
    return list(db.scalars(stmt).all())