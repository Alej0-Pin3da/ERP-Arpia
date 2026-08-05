from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_admin, require_roles
from app.models.insumos import CategoriaInsumo, Insumo
from app.schemas.insumo import InsumoCreate, InsumoRead, InsumoUpdate

router = APIRouter(prefix="/insumos", tags=["insumos"])

audited_user = require_roles("admin", "operador", "consulta")


def _to_read(insumo: Insumo) -> InsumoRead:
    data = InsumoRead.model_validate(insumo)
    data.nombre_categoria = (
        insumo.categoria.nombre if insumo.categoria is not None else None
    )
    return data


@router.get("", response_model=list[InsumoRead])
def list_insumos(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: Insumo = Depends(audited_user),
):
    stmt = (
        select(Insumo)
        .options(selectinload(Insumo.categoria))
        .order_by(Insumo.id)
        .limit(limit)
        .offset(offset)
    )
    return [_to_read(i) for i in db.scalars(stmt).all()]


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