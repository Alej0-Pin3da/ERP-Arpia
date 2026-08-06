from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.usuarios import Usuario
from app.schemas.costo import CostoProduccionRead
from app.services.costos import desglosar_costo_produccion

router = APIRouter(prefix="/productos", tags=["costos"])

audited_user = require_roles("admin", "operador", "consulta")


@router.get("/{producto_id}/costo", response_model=CostoProduccionRead)
def get_costo_produccion(
    producto_id: int,
    variante_id: int | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(audited_user),
):
    total, lineas = desglosar_costo_produccion(db, producto_id, variante_id)
    return CostoProduccionRead(total=total, lineas=lineas)
