"""Local-AI copy tests (V6 M5).

The Ollama HTTP layer is stubbed (no network): prompt construction is
asserted from the captured payload, plus endpoint wiring, 404s, LLM-down
503s and auth gating — all against the real test PostgreSQL.
"""

import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    Insumo,
    Producto,
    TipoProducto,
)
from app.services import ai_copy as ai_copy_service


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _setup_producto() -> tuple[int, int, int, int]:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat IA {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        ins = Insumo(
            categoria_id=cat.id,
            nombre="Saten Negro IA",
            unidad_medida="metro",
            stock_actual=Decimal("10"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("7"),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        tipo = TipoProducto(nombre=f"Tipo IA {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        prod = Producto(
            tipo_producto_id=tipo.id,
            nombre="Bustier Nocturno",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
            mano_obra=Decimal("0"),
            cif_energia=Decimal("0"),
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        db.add(
            BomInsumo(
                producto_id=prod.id,
                insumo_id=ins.id,
                cantidad_requerida=Decimal("1"),
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.commit()
        return cat.id, ins.id, tipo.id, prod.id
    finally:
        db.close()


def _cleanup(producto_id: int, insumo_id: int, tipo_id: int, cat_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == cat_id).delete()
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class _Resp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_prompt_inyecta_bom_y_tono():
    prompt = ai_copy_service.construir_prompt(
        "Bustier Nocturno", ["Saten Negro IA"]
    )
    assert "Bustier Nocturno" in prompt
    assert "Saten Negro IA" in prompt
    assert "Oscuro" in prompt


def test_generar_copy_ok_con_stub(client, admin_token, monkeypatch):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    try:
        capturado: dict = {}

        def falso_post(url, payload, timeout):
            capturado["prompt"] = payload["prompt"]
            capturado["model"] = payload["model"]
            return _Resp(200, {"response": "  Párrafo oscuro y elegante.  "})

        monkeypatch.setattr(ai_copy_service, "_post_ollama", falso_post)
        resp = client.post(
            "/api/v1/ai/generar-copy",
            json={"producto_id": producto_id},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["producto_id"] == producto_id
        assert body["texto"] == "Párrafo oscuro y elegante."
        assert "Bustier Nocturno" in capturado["prompt"]
        assert "Saten Negro IA" in capturado["prompt"]
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_generar_copy_404_producto(client, admin_token):
    resp = client.post(
        "/api/v1/ai/generar-copy",
        json={"producto_id": 999999},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 404


def test_generar_copy_503_si_ollama_caido(client, admin_token, monkeypatch):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    try:
        def caido(url, payload, timeout):
            raise ConnectionError("refused")

        monkeypatch.setattr(ai_copy_service, "_post_ollama", caido)
        resp = client.post(
            "/api/v1/ai/generar-copy",
            json={"producto_id": producto_id},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 503
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_generar_copy_requires_auth(client):
    assert client.post(
        "/api/v1/ai/generar-copy", json={"producto_id": 1}
    ).status_code in (401, 403)
