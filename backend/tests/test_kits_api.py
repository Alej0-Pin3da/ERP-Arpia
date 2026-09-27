"""Kits API endpoint tests (V6 M1).

Drives /api/v1/kits through the FastAPI TestClient against the real test
PostgreSQL: create with lines (201 + live cost snapshot), margin alert
below the 5% floor, duplicate line 409, unknown product 422, unknown kit
404, add/remove lines, delete, auth 401, cantidad validation 422.

Product costs come from the real recursive BOM math: one line of
2 units x $5 cost => $10 per unit (fijos 0, no waste, no times).
"""

import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    Insumo,
    Kit,
    KitProducto,
    Producto,
    TipoProducto,
)


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _setup_producto(costo_insumo: str = "5") -> tuple[int, int, int, int]:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat Kit {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        ins = Insumo(
            categoria_id=cat.id,
            nombre=f"Tela Kit {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal("100"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal(costo_insumo),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        tipo = TipoProducto(nombre=f"Tipo Kit {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        prod = Producto(
            tipo_producto_id=tipo.id,
            nombre=f"Producto Kit {_unique()}",
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
                cantidad_requerida=Decimal("2"),
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.commit()
        return cat.id, ins.id, tipo.id, prod.id
    finally:
        db.close()


def _cleanup(cat_id: int, insumo_id: int, tipo_id: int, producto_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(KitProducto).filter(
            KitProducto.producto_id == producto_id
        ).delete(synchronize_session=False)
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == cat_id).delete()
        db.commit()
    finally:
        db.close()


def _limpiar_kits() -> None:
    db = SessionLocal()
    try:
        db.query(KitProducto).delete()
        db.query(Kit).delete()
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_post_kit_requires_auth(client):
    assert client.post("/api/v1/kits", json={"nombre": "X"}).status_code == 401


def test_post_kit_snapshot_y_margen_ok(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_kits()
    try:
        resp = client.post(
            "/api/v1/kits",
            json={
                "nombre": "Caja Promo",
                "precio_promocional": "100",
                "lineas": [{"producto_id": producto_id, "cantidad": "2"}],
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        # costo = 2u x (2m x $5) = $20; margen (100-20)/100 = 80%.
        assert Decimal(str(body["costo_total"])) == Decimal("20")
        assert Decimal(str(body["margen_pct"])) == Decimal("80.00")
        assert body["alerta_margen"] is False
        assert len(body["lineas"]) == 1
        assert body["lineas"][0]["producto_id"] == producto_id
        assert Decimal(str(body["lineas"][0]["subtotal"])) == Decimal("20")
    finally:
        _limpiar_kits()
        _cleanup(cat_id, insumo_id, tipo_id, producto_id)


def test_post_kit_alerta_bajo_5(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_kits()
    try:
        resp = client.post(
            "/api/v1/kits",
            json={
                "nombre": "Caja Barata",
                "precio_promocional": "21",
                "lineas": [{"producto_id": producto_id, "cantidad": "2"}],
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        # margen (21-20)/21 = 4.76% < 5% -> alerta visual, no bloqueo.
        assert body["alerta_margen"] is True
        assert Decimal(str(body["margen_pct"])) == Decimal("4.76")
    finally:
        _limpiar_kits()
        _cleanup(cat_id, insumo_id, tipo_id, producto_id)


def test_post_kit_422_producto_inexistente(client, admin_token):
    resp = client.post(
        "/api/v1/kits",
        json={
            "nombre": "Caja Fantasma",
            "precio_promocional": "10",
            "lineas": [{"producto_id": 999999, "cantidad": "1"}],
        },
        headers=_auth(admin_token),
    )
    assert resp.status_code == 422


def test_post_kit_422_cantidad_cero(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    try:
        resp = client.post(
            "/api/v1/kits",
            json={
                "nombre": "Caja Cero",
                "precio_promocional": "10",
                "lineas": [{"producto_id": producto_id, "cantidad": "0"}],
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 422
    finally:
        _cleanup(cat_id, insumo_id, tipo_id, producto_id)


def test_kit_linea_duplicada_409(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_kits()
    try:
        resp = client.post(
            "/api/v1/kits",
            json={"nombre": "Caja Dup", "precio_promocional": "100"},
            headers=_auth(admin_token),
        )
        kit_id = resp.json()["id"]
        url = f"/api/v1/kits/{kit_id}/lineas"
        assert (
            client.post(
                url,
                json={"producto_id": producto_id, "cantidad": "1"},
                headers=_auth(admin_token),
            ).status_code
            == 201
        )
        assert (
            client.post(
                url,
                json={"producto_id": producto_id, "cantidad": "1"},
                headers=_auth(admin_token),
            ).status_code
            == 409
        )
    finally:
        _limpiar_kits()
        _cleanup(cat_id, insumo_id, tipo_id, producto_id)


def test_kit_get_patch_delete(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_kits()
    try:
        kit_id = client.post(
            "/api/v1/kits",
            json={"nombre": "Caja CRUD", "precio_promocional": "50"},
            headers=_auth(admin_token),
        ).json()["id"]
        assert client.get("/api/v1/kits/999999", headers=_auth(admin_token)).status_code == 404
        resp = client.patch(
            f"/api/v1/kits/{kit_id}",
            json={"precio_promocional": "60"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert Decimal(str(resp.json()["precio_promocional"])) == Decimal("60")
        assert (
            client.delete(
                f"/api/v1/kits/{kit_id}", headers=_auth(admin_token)
            ).status_code
            == 204
        )
        assert client.get(f"/api/v1/kits/{kit_id}", headers=_auth(admin_token)).status_code == 404
    finally:
        _limpiar_kits()
        _cleanup(cat_id, insumo_id, tipo_id, producto_id)


def test_kit_remove_linea_404(client, admin_token):
    _limpiar_kits()
    kit_id = client.post(
        "/api/v1/kits",
        json={"nombre": "Caja Vacia", "precio_promocional": "10"},
        headers=_auth(admin_token),
    ).json()["id"]
    try:
        assert (
            client.delete(
                f"/api/v1/kits/{kit_id}/lineas/999999", headers=_auth(admin_token)
            ).status_code
            == 404
        )
    finally:
        _limpiar_kits()
