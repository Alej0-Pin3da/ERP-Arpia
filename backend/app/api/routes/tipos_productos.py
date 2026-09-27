from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.productos import TipoProducto
from app.schemas.common import Paginated
from app.schemas.producto import TipoProductoCreate, TipoProductoRead, TipoProductoUpdate
from app.services.tipos_productos import (
    actualizar_tipo_producto,
    crear_tipo_producto,
    eliminar_tipo_producto,
    listar_tipos_producto,
    obtener_tipo_producto,
)

router = APIRouter(prefix="/tipos-producto", tags=["tipos-producto"])

audited_user = require_roles("admin", "operador", "consulta")


@router.get("", response_model=Paginated[TipoProductoRead])
def list_tipos_producto(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(audited_user),
):
    rows, total = listar_tipos_producto(db, limit=limit, offset=offset, q=q)
    return Paginated[TipoProductoRead](items=rows, total=total)


@router.get("/{tipo_producto_id}", response_model=TipoProductoRead)
def get_tipo_producto(
    tipo_producto_id: int,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(audited_user),
):
    return obtener_tipo_producto(db, tipo_producto_id)


@router.post("", response_model=TipoProductoRead, status_code=status.HTTP_201_CREATED)
def create_tipo_producto(
    payload: TipoProductoCreate,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(require_admin),
):
    return crear_tipo_producto(db, payload)


@router.put("/{tipo_producto_id}", response_model=TipoProductoRead)
def update_tipo_producto(
    tipo_producto_id: int,
    payload: TipoProductoUpdate,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(require_admin),
):
    return actualizar_tipo_producto(db, tipo_producto_id, payload)


@router.delete("/{tipo_producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_producto(
    tipo_producto_id: int,
    db: Session = Depends(get_db),
    _: TipoProducto = Depends(require_admin),
):
    eliminar_tipo_producto(db, tipo_producto_id)
