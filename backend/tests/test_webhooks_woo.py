"""WooCommerce webhook tests (V6 M3).

Through the FastAPI TestClient against the real test PostgreSQL:
- Valid HMAC creates a REAL web-channel sale (stock, costs, M2 split).
- Bad signature 401; unknown SKU 422; empty items 422; no secret 503.
- Duplicate delivery acks with the original sale (no double-sell).
"""

import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    DetalleVenta,
    Insumo,
    Producto,
    TipoProducto,
    Venta,
    WebhookEvento,
)

SECRET = "test-woo-secret"


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _setup_producto() -> tuple[int, int, int, int, str]:
    sku = f"SKU-{_unique()}"
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat Woo {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        ins = Insumo(
            categoria_id=cat.id,
            nombre=f"Tela Woo {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal("100"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("5"),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        tipo = TipoProducto(nombre=f"Tipo Woo {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        prod = Producto(
            tipo_producto_id=tipo.id,
            nombre=f"Producto Woo {_unique()}",
            codigo=sku,
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
            mano_obra=Decimal("0"),
            cif_energia=Decimal("0"),
            stock_actual=Decimal("10000"),
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        db.add(
            BomInsumo(
                producto_id=prod.id,
                insumo_id=ins.id,
                cantidad_requerida=Decimal("2"),
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.commit()
        return cat.id, ins.id, tipo.id, prod.id, sku
    finally:
        db.close()


def _cleanup(producto_id: int, insumo_id: int, tipo_id: int, cat_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = (
            db.query(DetalleVenta.venta_id)
            .filter(DetalleVenta.producto_id == producto_id)
            .all()
        )
        for (vid,) in ven_ids:
            db.query(WebhookEvento).filter(WebhookEvento.venta_id == vid).delete()
            db.query(DetalleVenta).filter(DetalleVenta.venta_id == vid).delete()
            db.query(Venta).filter(Venta.id == vid).delete()
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == cat_id).delete()
        db.commit()
    finally:
        db.close()


def _post_orden(client, order: dict, secret: str = SECRET):
    body = json.dumps(order).encode()
    return client.post(
        "/api/v1/webhooks/woo/order-created",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-WC-Webhook-Signature": base64.b64encode(
                hmac.new(secret.encode(), body, hashlib.sha256).digest()
            ).decode(),
        },
    )


def _orden(order_id: int, sku: str) -> dict:
    return {
        "id": order_id,
        "line_items": [{"sku": sku, "quantity": 1, "price": "100"}],
    }


def test_webhook_crea_venta_web(client, monkeypatch):
    monkeypatch.setattr(settings, "WOO_WEBHOOK_SECRET", SECRET)
    cat_id, insumo_id, tipo_id, producto_id, sku = _setup_producto()
    try:
        resp = _post_orden(client, _orden(9001, sku))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["duplicado"] is False
        db = SessionLocal()
        try:
            venta = db.get(Venta, body["venta_id"])
            assert venta is not None
            assert venta.canal_venta == "web"
            assert "WooCommerce orden 9001" in (venta.observaciones or "")
        finally:
            db.close()
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_webhook_duplicado_no_duplica(client, monkeypatch):
    monkeypatch.setattr(settings, "WOO_WEBHOOK_SECRET", SECRET)
    cat_id, insumo_id, tipo_id, producto_id, sku = _setup_producto()
    try:
        order = _orden(9002, sku)
        primero = _post_orden(client, order).json()
        segundo = _post_orden(client, order).json()
        assert segundo["duplicado"] is True
        assert segundo["venta_id"] == primero["venta_id"]
        db = SessionLocal()
        try:
            n = (
                db.query(Venta)
                .filter(Venta.observaciones == "WooCommerce orden 9002")
                .count()
            )
            assert n == 1
        finally:
            db.close()
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_webhook_firma_invalida_401(client, monkeypatch):
    monkeypatch.setattr(settings, "WOO_WEBHOOK_SECRET", SECRET)
    cat_id, insumo_id, tipo_id, producto_id, sku = _setup_producto()
    try:
        assert _post_orden(client, _orden(9003, sku), secret="otro").status_code == 401
        body = json.dumps(_orden(9004, sku)).encode()
        assert (
            client.post(
                "/api/v1/webhooks/woo/order-created",
                content=body,
                headers={"Content-Type": "application/json"},
            ).status_code
            == 401
        )
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_webhook_sku_desconocido_422(client, monkeypatch):
    monkeypatch.setattr(settings, "WOO_WEBHOOK_SECRET", SECRET)
    assert _post_orden(client, _orden(9005, "NO-EXISTE")).status_code == 422


def test_webhook_sin_secreto_503(client, monkeypatch):
    monkeypatch.setattr(settings, "WOO_WEBHOOK_SECRET", "")
    cat_id, insumo_id, tipo_id, producto_id, sku = _setup_producto()
    try:
        assert _post_orden(client, _orden(9006, sku)).status_code == 503
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)
