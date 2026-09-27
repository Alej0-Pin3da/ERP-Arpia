"""Commercial copy with a local LLM (V6 M5).

Reads the product's real BOM (insumo names via the cost engine), injects
them into a fixed Spanish prompt (dark/elegant/alternative tone) and asks a
local Ollama / llama.cpp server. The HTTP call is injectable so tests never
touch the network. Nothing is persisted — the frontend fills the product's
``descripcion`` field and saves through the normal update flow.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.productos import Producto
from app.services.costos import desglosar_costo_produccion

PROMPT_SISTEMA = (
    "Actúa como un experto en marketing de moda alternativa. "
    "Escribe una descripción de producto de 2 párrafos."
)

TONO = "Tono: Oscuro, elegante, alternativo."


def construir_prompt(nombre_prenda: str, insumos: list[str]) -> str:
    """Fixed prompt: product name + real BOM materials + tone."""
    materiales = ", ".join(insumos) if insumos else "materiales de autor"
    return (
        f"{PROMPT_SISTEMA} Escribe una descripción de producto de 2 párrafos "
        f"para {nombre_prenda}. Menciona que está fabricada con materiales "
        f"de alta calidad, incluyendo: {materiales}. {TONO}"
    )


def _post_ollama(url: str, payload: dict, timeout: int):
    """Default HTTP layer (httpx, non-streaming). Swappable in tests."""
    import httpx

    return httpx.post(url, json=payload, timeout=timeout)


def _llamar_ollama(prompt: str, post=None) -> str:
    """POST /api/generate (non-streaming). Raises HTTPException on failure."""
    http_post = post if post is not None else _post_ollama

    try:
        resp = http_post(
            f"{settings.OLLAMA_URL.rstrip('/')}/api/generate",
            {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            settings.OLLAMA_TIMEOUT_S,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"IA local no disponible en {settings.OLLAMA_URL} ({e})",
        ) from e
    if getattr(resp, "status_code", 200) != 200:
        raise HTTPException(
            status_code=502,
            detail=f"El modelo local respondió {getattr(resp, 'status_code', '?')}",
        )
    try:
        texto = (resp.json() or {}).get("response", "")
    except Exception as e:
        raise HTTPException(
            status_code=502, detail="Respuesta inválida del modelo local"
        ) from e
    if not str(texto).strip():
        raise HTTPException(
            status_code=502, detail="El modelo local devolvió texto vacío"
        )
    return str(texto).strip()


def generar_copy(db: Session, producto_id: int, post=None) -> dict:
    """Generate commercial copy for a product (read-only, no persistence)."""
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    _, lineas = desglosar_costo_produccion(db, producto_id)
    insumos = [l.nombre for l in lineas if l.nombre]
    prompt = construir_prompt(producto.nombre, insumos)
    texto = _llamar_ollama(prompt, post=post)
    return {
        "producto_id": producto_id,
        "producto_nombre": producto.nombre,
        "texto": texto,
        "modelo": settings.OLLAMA_MODEL,
    }
