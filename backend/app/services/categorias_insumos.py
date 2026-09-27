"""Service layer for CategoriaInsumo CRUD."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.insumos import CategoriaInsumo
from app.schemas.categoria_insumo import CategoriaInsumoCreate, CategoriaInsumoUpdate
from app.services.paginacion import paginar


def listar_categorias_insumo(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
    q: str | None = None,
) -> tuple[list[CategoriaInsumo], int]:
    stmt = select(CategoriaInsumo).order_by(CategoriaInsumo.id)
    if q is not None:
        stmt = stmt.where(CategoriaInsumo.nombre.ilike(f"%{q}%"))
    rows, total = paginar(db, stmt, limit, offset)
    return list(rows), total


def obtener_categoria_insumo(db: Session, categoria_id: int) -> CategoriaInsumo:
    categoria = db.get(CategoriaInsumo, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=404, detail="CategoriaInsumo not found")
    return categoria


def crear_categoria_insumo(db: Session, payload: CategoriaInsumoCreate) -> CategoriaInsumo:
    categoria = CategoriaInsumo(**payload.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def actualizar_categoria_insumo(
    db: Session,
    categoria_id: int,
    payload: CategoriaInsumoUpdate,
) -> CategoriaInsumo:
    categoria = obtener_categoria_insumo(db, categoria_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(categoria, field, value)
    db.commit()
    db.refresh(categoria)
    return categoria


def eliminar_categoria_insumo(db: Session, categoria_id: int) -> None:
    categoria = obtener_categoria_insumo(db, categoria_id)
    db.delete(categoria)
    db.commit()
