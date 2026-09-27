from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.insumos import CategoriaInsumo
from app.schemas.categoria_insumo import (
    CategoriaInsumoCreate,
    CategoriaInsumoRead,
    CategoriaInsumoUpdate,
)
from app.schemas.common import Paginated
from app.services.categorias_insumos import (
    actualizar_categoria_insumo,
    crear_categoria_insumo,
    eliminar_categoria_insumo,
    listar_categorias_insumo,
    obtener_categoria_insumo,
)

router = APIRouter(prefix="/categorias-insumos", tags=["categorias-insumos"])

audited_user = require_roles("admin", "operador", "consulta")


@router.get("", response_model=Paginated[CategoriaInsumoRead])
def list_categorias(
    limit: int = 100,
    offset: int = 0,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(audited_user),
):
    rows, total = listar_categorias_insumo(db, limit=limit, offset=offset, q=q)
    return Paginated[CategoriaInsumoRead](items=rows, total=total)


@router.get("/{categoria_id}", response_model=CategoriaInsumoRead)
def get_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(audited_user),
):
    return obtener_categoria_insumo(db, categoria_id)


@router.post("", response_model=CategoriaInsumoRead, status_code=status.HTTP_201_CREATED)
def create_categoria(
    payload: CategoriaInsumoCreate,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(require_admin),
):
    return crear_categoria_insumo(db, payload)


@router.put("/{categoria_id}", response_model=CategoriaInsumoRead)
def update_categoria(
    categoria_id: int,
    payload: CategoriaInsumoUpdate,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(require_admin),
):
    return actualizar_categoria_insumo(db, categoria_id, payload)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(require_admin),
):
    eliminar_categoria_insumo(db, categoria_id)
