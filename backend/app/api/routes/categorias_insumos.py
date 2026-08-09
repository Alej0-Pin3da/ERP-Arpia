from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.insumos import CategoriaInsumo
from app.schemas.categoria_insumo import (
    CategoriaInsumoCreate,
    CategoriaInsumoRead,
    CategoriaInsumoUpdate,
)
from app.schemas.common import Paginated
from app.services.paginacion import paginar

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
    stmt = select(CategoriaInsumo).order_by(CategoriaInsumo.id)
    if q is not None:
        stmt = stmt.where(CategoriaInsumo.nombre.ilike(f"%{q}%"))
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[CategoriaInsumoRead](items=list(rows), total=total)


@router.get("/{categoria_id}", response_model=CategoriaInsumoRead)
def get_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(audited_user),
):
    categoria = db.get(CategoriaInsumo, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=404, detail="CategoriaInsumo not found")
    return categoria


@router.post("", response_model=CategoriaInsumoRead, status_code=status.HTTP_201_CREATED)
def create_categoria(
    payload: CategoriaInsumoCreate,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(require_admin),
):
    categoria = CategoriaInsumo(**payload.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaInsumoRead)
def update_categoria(
    categoria_id: int,
    payload: CategoriaInsumoUpdate,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(require_admin),
):
    categoria = db.get(CategoriaInsumo, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=404, detail="CategoriaInsumo not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(categoria, field, value)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    _: CategoriaInsumo = Depends(require_admin),
):
    categoria = db.get(CategoriaInsumo, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=404, detail="CategoriaInsumo not found")
    db.delete(categoria)
    db.commit()