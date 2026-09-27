"""Local-AI commercial copy router (V6 M5).

POST /ai/generar-copy reads the product's real BOM and asks the local LLM.
Read-only: nothing is persisted — the frontend fills ``descripcion`` and
saves through the normal product update flow.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.usuarios import Usuario
from app.services import ai_copy as ai_copy_service

router = APIRouter(prefix="/ai", tags=["ai"])

editor_user = require_roles("admin", "operador")


class GenerarCopyRequest(BaseModel):
    producto_id: int


class GenerarCopyResponse(BaseModel):
    producto_id: int
    producto_nombre: str
    texto: str
    modelo: str


@router.post("/generar-copy", response_model=GenerarCopyResponse)
def generar_copy(
    payload: GenerarCopyRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(editor_user),
):
    """Generate commercial copy for a product with the local LLM."""
    return ai_copy_service.generar_copy(db, payload.producto_id)
