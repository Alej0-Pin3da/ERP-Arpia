from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_admin, require_roles
from app.models.insumos import CategoriaInsumo, Insumo
from app.schemas.common import Paginated
from app.schemas.insumo import InsumoCreate, InsumoRead, InsumoUpdate
from app.services.paginacion import aplicar_orden, paginar

router = APIRouter(prefix="/insumos", tags=["insumos"])

audited_user = require_roles("admin", "operador", "consulta")

# Whitelisted server-side sort keys; categoria is the joined category name
# (inner join — categoria_id is NOT NULL).
_SORTABLE_INSUMOS = {
    "id": Insumo.id,
    "nombre": Insumo.nombre,
    "unidad_medida": Insumo.unidad_medida,
    "stock_actual": Insumo.stock_actual,
    "stock_minimo": Insumo.stock_minimo,
    "costo_promedio_actual": Insumo.costo_promedio_actual,
    "categoria": CategoriaInsumo.nombre,
}


def _to_read(insumo: Insumo) -> InsumoRead:
    data = InsumoRead.model_validate(insumo)
    data.nombre_categoria = (
        insumo.categoria.nombre if insumo.categoria is not None else None
    )
    return data


@router.get("", response_model=Paginated[InsumoRead])
def list_insumos(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    categoria_id: int | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Insumo = Depends(audited_user),
):
    # Categoria joined once up-front so the categoria sort key works without
    # adding joins later (categoria_id is NOT NULL, so the inner join is safe).
    stmt = (
        select(Insumo)
        .join(Insumo.categoria)
        .options(selectinload(Insumo.categoria))
        .order_by(Insumo.id)
    )
    if q is not None:
        stmt = stmt.where(
            or_(
                Insumo.nombre.ilike(f"%{q}%"),
                Insumo.unidad_medida.ilike(f"%{q}%"),
            )
        )
    if categoria_id is not None:
        stmt = stmt.where(Insumo.categoria_id == categoria_id)
    stmt = aplicar_orden(stmt, sort_by, order, _SORTABLE_INSUMOS)
    rows, total = paginar(db, stmt, limit, offset)
    return Paginated[InsumoRead](items=[_to_read(i) for i in rows], total=total)


@router.get("/{insumo_id}", response_model=InsumoRead)
def get_insumo(
    insumo_id: int,
    db: Session = Depends(get_db),
    _: Insumo = Depends(audited_user),
):
    insumo = db.get(Insumo, insumo_id)
    if insumo is None:
        raise HTTPException(status_code=404, detail="Insumo not found")
    return _to_read(insumo)


@router.post("", response_model=InsumoRead, status_code=status.HTTP_201_CREATED)
def create_insumo(
    payload: InsumoCreate,
    db: Session = Depends(get_db),
    _: Insumo = Depends(require_admin),
):
    if db.get(CategoriaInsumo, payload.categoria_id) is None:
        raise HTTPException(status_code=400, detail="Categoria does not exist")
    insumo = Insumo(**payload.model_dump())
    db.add(insumo)
    db.commit()
    db.refresh(insumo)
    insumo = db.get(Insumo, insumo.id)
    return _to_read(insumo)


@router.put("/{insumo_id}", response_model=InsumoRead)
def update_insumo(
    insumo_id: int,
    payload: InsumoUpdate,
    db: Session = Depends(get_db),
    _: Insumo = Depends(require_admin),
):
    insumo = db.get(Insumo, insumo_id)
    if insumo is None:
        raise HTTPException(status_code=404, detail="Insumo not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(insumo, field, value)
    db.commit()
    db.refresh(insumo)
    insumo = db.get(Insumo, insumo_id)
    return _to_read(insumo)


@router.delete("/{insumo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insumo(
    insumo_id: int,
    db: Session = Depends(get_db),
    _: Insumo = Depends(require_admin),
):
    insumo = db.get(Insumo, insumo_id)
    if insumo is None:
        raise HTTPException(status_code=404, detail="Insumo not found")
    db.delete(insumo)
    db.commit()