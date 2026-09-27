from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_roles
from app.models.clientes import Cliente
from app.schemas.cliente import ClienteCreate, ClienteRead, ClienteUpdate
from app.schemas.common import Paginated
from app.services import clientes as clientes_service

router = APIRouter(prefix="/clientes", tags=["clientes"])

audited_user = require_roles("admin", "operador", "consulta")


@router.get("", response_model=Paginated[ClienteRead])
def list_clientes(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    tipo: str | None = None,
    ciudad: str | None = None,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _: Cliente = Depends(audited_user),
):
    rows, total = clientes_service.listar_clientes(
        db,
        limit=limit,
        offset=offset,
        q=q,
        tipo=tipo,
        ciudad=ciudad,
        sort_by=sort_by,
        order=order,
    )
    return Paginated[ClienteRead](items=rows, total=total)


@router.get("/{cliente_id}", response_model=ClienteRead)
def get_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Cliente = Depends(audited_user),
):
    return clientes_service.obtener_cliente(db, cliente_id)


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def create_cliente(
    payload: ClienteCreate,
    db: Session = Depends(get_db),
    _: Cliente = Depends(require_admin),
):
    return clientes_service.crear_cliente(db, payload)


@router.put("/{cliente_id}", response_model=ClienteRead)
def update_cliente(
    cliente_id: int,
    payload: ClienteUpdate,
    db: Session = Depends(get_db),
    _: Cliente = Depends(require_admin),
):
    return clientes_service.actualizar_cliente(db, cliente_id, payload)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Cliente = Depends(require_admin),
):
    clientes_service.eliminar_cliente(db, cliente_id)
