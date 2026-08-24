"""PR2 Backend API RED tests — filters, canal/metodo whitelist, seeder mirror.

Strict TDD RED: these must FAIL before PR2 implementation, PASS after.
covers tasks 2.3 (clientes q/tipo/ciudad ILIKE combinable), 2.4 (ventas canal 5 + metodo 4 + null 422), 2.5 (seeder mirror idempotent).
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models import Cliente
from app.seeder import seed_canales_venta, seed_metodos_pago

URL_CLIENTES = "/api/v1/clientes"
URL_VENTAS = "/api/v1/ventas"


def _unique() -> str:
    return uuid.uuid4().hex[:12]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_cliente_raw(**overrides) -> int:
    db = SessionLocal()
    try:
        defaults = dict(nombre=f"Cliente {_unique()}")
        defaults.update(overrides)
        cli = Cliente(**defaults)
        db.add(cli)
        db.commit()
        db.refresh(cli)
        return cli.id
    finally:
        db.close()


def _cleanup_clientes(ids: list[int]) -> None:
    db = SessionLocal()
    try:
        for cid in ids:
            db.query(Cliente).filter(Cliente.id == cid).delete()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2.3 clientes filters
# ---------------------------------------------------------------------------


class TestClientesFilters:
    def test_filter_by_tipo_exact(self, client, admin_token):
        ids = [
            _make_cliente_raw(nombre=f"F2_3 Tipo {_unique()}", tipo="mayorista", ciudad="Pereira"),
            _make_cliente_raw(nombre=f"F2_3 Tipo {_unique()}", tipo="minorista", ciudad="Pereira"),
            _make_cliente_raw(nombre=f"F2_3 Tipo {_unique()}", tipo="mayorista", ciudad="Bogota"),
        ]
        try:
            resp = client.get(URL_CLIENTES, params={"tipo": "mayorista", "q": "F2_3 Tipo"}, headers=_auth(admin_token))
            assert resp.status_code == 200
            body = resp.json()
            # only mayorista rows (2)
            tipos = [r["tipo"] for r in body["items"]]
            assert all(t == "mayorista" for t in tipos), tipos
            assert body["total"] == 2
        finally:
            _cleanup_clientes(ids)

    def test_filter_by_ciudad_exact(self, client, admin_token):
        ids = [
            _make_cliente_raw(nombre=f"F2_3 Ciudad {_unique()}", tipo="mayorista", ciudad="Pereira"),
            _make_cliente_raw(nombre=f"F2_3 Ciudad {_unique()}", tipo="mayorista", ciudad="Bogota"),
        ]
        try:
            resp = client.get(URL_CLIENTES, params={"ciudad": "Pereira", "q": "F2_3 Ciudad"}, headers=_auth(admin_token))
            assert resp.status_code == 200
            body = resp.json()
            assert body["total"] == 1
            assert body["items"][0]["ciudad"] == "Pereira"
        finally:
            _cleanup_clientes(ids)

    def test_filter_tipo_ciudad_q_combinables(self, client, admin_token):
        # q searches nombre|ciudad|direccion case-insensitive, combined with tipo+ciudad
        ids = [
            _make_cliente_raw(nombre=f"Maria Lopez {_unique()}", tipo="mayorista", ciudad="Pereira", direccion="Calle 123"),
            _make_cliente_raw(nombre=f"Juan Perez {_unique()}", tipo="mayorista", ciudad="Pereira", direccion="Avenida 5"),
            _make_cliente_raw(nombre=f"Maria Gomez {_unique()}", tipo="minorista", ciudad="Pereira", direccion="Calle 456"),
            _make_cliente_raw(nombre=f"Maria Diaz {_unique()}", tipo="mayorista", ciudad="Bogota", direccion="Calle 789"),
        ]
        try:
            # tipo=mayorista + ciudad=Pereira + q=maria => only first
            resp = client.get(
                URL_CLIENTES,
                params={"tipo": "mayorista", "ciudad": "Pereira", "q": "maria"},
                headers=_auth(admin_token),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["total"] == 1
            assert "Maria Lopez" in body["items"][0]["nombre"]

            # q by ciudad ILIKE (should find Pereira rows)
            resp = client.get(URL_CLIENTES, params={"q": "pereira", "tipo": "mayorista"}, headers=_auth(admin_token))
            assert resp.status_code == 200
            body = resp.json()
            ciudades = [r["ciudad"] for r in body["items"]]
            assert all(c == "Pereira" for c in ciudades)

            # q by direccion ILIKE
            resp = client.get(URL_CLIENTES, params={"q": "avenida"}, headers=_auth(admin_token))
            assert resp.status_code == 200
            body = resp.json()
            assert any("Avenida 5" in (r["direccion"] or "") for r in body["items"])

            # case-insensitive: MARIA finds same as maria
            resp2 = client.get(URL_CLIENTES, params={"q": "MARIA", "tipo": "mayorista", "ciudad": "Pereira"}, headers=_auth(admin_token))
            assert resp2.status_code == 200
            assert resp2.json()["total"] == 1
        finally:
            _cleanup_clientes(ids)

    def test_filter_paginated_with_tipo(self, client, admin_token):
        prefix = f"F2_3 Pag {_unique()}"
        ids = [_make_cliente_raw(nombre=f"{prefix} {i}", tipo="mayorista", ciudad="Pereira") for i in range(5)]
        try:
            resp = client.get(
                URL_CLIENTES,
                params={"tipo": "mayorista", "q": prefix, "limit": 2, "offset": 2},
                headers=_auth(admin_token),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["items"]) == 2
            assert body["total"] == 5
        finally:
            _cleanup_clientes(ids)


# ---------------------------------------------------------------------------
# 2.4 ventas whitelist canal 5 + metodo 4 + null
# ---------------------------------------------------------------------------

# need helpers for venta tests (reuse pattern from test_ventas_api)
from app.models import BomInsumo, CategoriaInsumo, Insumo, Producto, TipoProducto, VarianteProducto, DetalleVenta, Venta  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _make_categoria() -> int:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat PR2 {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat.id
    finally:
        db.close()


def _make_insumo(cat_id: int) -> int:
    db = SessionLocal()
    try:
        ins = Insumo(categoria_id=cat_id, nombre=f"Ins PR2 {_unique()}", unidad_medida="metro", stock_actual=Decimal("100"), stock_minimo=Decimal("0"), costo_promedio_actual=Decimal("5"))
        db.add(ins)
        db.commit()
        db.refresh(ins)
        return ins.id
    finally:
        db.close()


def _make_tipo() -> int:
    db = SessionLocal()
    try:
        t = TipoProducto(nombre=f"Tipo PR2 {_unique()}")
        db.add(t)
        db.commit()
        db.refresh(t)
        return t.id
    finally:
        db.close()


def _make_producto(tipo_id: int) -> int:
    db = SessionLocal()
    try:
        p = Producto(tipo_producto_id=tipo_id, nombre=f"Prod PR2 {_unique()}", requiere_fabricacion=True, costos_operativos_fijos=Decimal("0"))
        db.add(p)
        db.commit()
        db.refresh(p)
        return p.id
    finally:
        db.close()


def _make_linea(producto_id: int, insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.add(BomInsumo(producto_id=producto_id, insumo_id=insumo_id, cantidad_requerida=Decimal("1"), porcentaje_desperdicio=Decimal("0")))
        db.commit()
    finally:
        db.close()


def _cleanup_ventas_for_producto(prod_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = select(DetalleVenta.venta_id).where(DetalleVenta.producto_id == prod_id)
        db.query(Venta).filter(Venta.id.in_(ven_ids)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _cleanup_producto(pid: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.producto_id == pid).delete()
        db.query(Producto).filter(Producto.id == pid).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_insumo(iid: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.insumo_id == iid).delete()
        db.query(Insumo).filter(Insumo.id == iid).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_categoria(cid: int) -> None:
    db = SessionLocal()
    try:
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == cid).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_tipo(tid: int) -> None:
    db = SessionLocal()
    try:
        db.query(TipoProducto).filter(TipoProducto.id == tid).delete()
        db.commit()
    finally:
        db.close()


def _venta_payload(prod_id: int, canal: str = "web", metodo: str | None = None) -> dict:
    payload = {"canal_venta": canal, "descuento_porcentaje": "0", "detalles": [{"producto_id": prod_id, "cantidad": "1", "precio_unitario": "10"}]}
    if metodo is not None:
        payload["metodo_pago"] = metodo
    return payload


class TestVentasWhitelist:
    @pytest.mark.parametrize("canal", ["web", "whatsapp", "instagram", "feria", "showroom_pereira"])
    def test_create_venta_valid_canal_5_values(self, client, operador_token, canal):
        cat = _make_categoria()
        ins = _make_insumo(cat)
        tipo = _make_tipo()
        prod = _make_producto(tipo)
        _make_linea(prod, ins)
        try:
            resp = client.post(URL_VENTAS, json=_venta_payload(prod, canal=canal), headers=_auth(operador_token))
            assert resp.status_code == 201, resp.text
            assert resp.json()["canal_venta"] == canal
        finally:
            _cleanup_ventas_for_producto(prod)
            _cleanup_producto(prod)
            _cleanup_insumo(ins)
            _cleanup_categoria(cat)
            _cleanup_tipo(tipo)

    def test_create_venta_invalid_canal_422(self, client, operador_token):
        cat = _make_categoria()
        ins = _make_insumo(cat)
        tipo = _make_tipo()
        prod = _make_producto(tipo)
        _make_linea(prod, ins)
        try:
            resp = client.post(URL_VENTAS, json=_venta_payload(prod, canal="telefono"), headers=_auth(operador_token))
            assert resp.status_code == 422
        finally:
            _cleanup_producto(prod)
            _cleanup_insumo(ins)
            _cleanup_categoria(cat)
            _cleanup_tipo(tipo)

    @pytest.mark.parametrize("metodo", ["efectivo", "transferencia", "tarjeta", "contraentrega"])
    def test_create_venta_valid_metodo_4_values(self, client, operador_token, metodo):
        cat = _make_categoria()
        ins = _make_insumo(cat)
        tipo = _make_tipo()
        prod = _make_producto(tipo)
        _make_linea(prod, ins)
        try:
            resp = client.post(URL_VENTAS, json=_venta_payload(prod, canal="web", metodo=metodo), headers=_auth(operador_token))
            assert resp.status_code == 201, resp.text
            assert resp.json()["metodo_pago"] == metodo
        finally:
            _cleanup_ventas_for_producto(prod)
            _cleanup_producto(prod)
            _cleanup_insumo(ins)
            _cleanup_categoria(cat)
            _cleanup_tipo(tipo)

    def test_create_venta_null_metodo_allowed(self, client, operador_token):
        cat = _make_categoria()
        ins = _make_insumo(cat)
        tipo = _make_tipo()
        prod = _make_producto(tipo)
        _make_linea(prod, ins)
        try:
            # omit metodo_pago entirely => None
            resp = client.post(URL_VENTAS, json=_venta_payload(prod, canal="web"), headers=_auth(operador_token))
            assert resp.status_code == 201, resp.text
            body = resp.json()
            assert body["metodo_pago"] is None
            # need cleanup before next request product still exists
            _cleanup_ventas_for_producto(prod)
            # explicit null
            resp2 = client.post(URL_VENTAS, json={**_venta_payload(prod, canal="web"), "metodo_pago": None}, headers=_auth(operador_token))
            assert resp2.status_code == 201, resp2.text
            assert resp2.json()["metodo_pago"] is None
        finally:
            _cleanup_ventas_for_producto(prod)
            _cleanup_producto(prod)
            _cleanup_insumo(ins)
            _cleanup_categoria(cat)
            _cleanup_tipo(tipo)

    def test_create_venta_invalid_metodo_422(self, client, operador_token):
        cat = _make_categoria()
        ins = _make_insumo(cat)
        tipo = _make_tipo()
        prod = _make_producto(tipo)
        _make_linea(prod, ins)
        try:
            resp = client.post(URL_VENTAS, json=_venta_payload(prod, canal="web", metodo="cripto"), headers=_auth(operador_token))
            assert resp.status_code == 422
        finally:
            _cleanup_producto(prod)
            _cleanup_insumo(ins)
            _cleanup_categoria(cat)
            _cleanup_tipo(tipo)

    def test_list_ventas_filter_showroom_pereira(self, client, operador_token):
        """GET /ventas?canal_venta=showroom_pereira must be accepted (PR2 adds 5th value to Literal)."""
        cat = _make_categoria()
        ins = _make_insumo(cat)
        tipo = _make_tipo()
        prod = _make_producto(tipo)
        _make_linea(prod, ins)
        try:
            resp = client.post(URL_VENTAS, json=_venta_payload(prod, canal="showroom_pereira"), headers=_auth(operador_token))
            assert resp.status_code == 201, resp.text
            resp = client.get(URL_VENTAS, params={"canal_venta": "showroom_pereira"}, headers=_auth(operador_token))
            assert resp.status_code == 200
            assert any(v["canal_venta"] == "showroom_pereira" for v in resp.json()["items"])
        finally:
            _cleanup_ventas_for_producto(prod)
            _cleanup_producto(prod)
            _cleanup_insumo(ins)
            _cleanup_categoria(cat)
            _cleanup_tipo(tipo)


# ---------------------------------------------------------------------------
# 2.5 seeder mirror idempotent
# ---------------------------------------------------------------------------


class TestSeederMirror:
    def test_seeder_inserts_5_canales_4_metodos(self):
        db = SessionLocal()
        try:
            seed_canales_venta(db)
            seed_metodos_pago(db)
            cnt_canales = db.execute(text("SELECT COUNT(*) FROM maestros_canales_venta")).scalar()
            cnt_metodos = db.execute(text("SELECT COUNT(*) FROM maestros_metodos_pago")).scalar()
            assert cnt_canales == 5, f"canales={cnt_canales}"
            assert cnt_metodos == 4, f"metodos={cnt_metodos}"
        finally:
            db.close()

    def test_seeder_idempotent(self):
        db = SessionLocal()
        try:
            seed_canales_venta(db)
            seed_canales_venta(db)
            seed_metodos_pago(db)
            seed_metodos_pago(db)
            cnt_canales = db.execute(text("SELECT COUNT(*) FROM maestros_canales_venta")).scalar()
            cnt_metodos = db.execute(text("SELECT COUNT(*) FROM maestros_metodos_pago")).scalar()
            assert cnt_canales == 5
            assert cnt_metodos == 4
            # verify canonical claves
            canales = {r[0] for r in db.execute(text("SELECT codigo FROM maestros_canales_venta")).fetchall()}
            assert canales == {"web", "whatsapp", "instagram", "feria", "showroom_pereira"}
            metodos = {r[0] for r in db.execute(text("SELECT codigo FROM maestros_metodos_pago")).fetchall()}
            assert metodos == {"efectivo", "transferencia", "tarjeta", "contraentrega"}
        finally:
            db.close()
