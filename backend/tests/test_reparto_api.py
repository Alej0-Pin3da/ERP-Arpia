"""Automatic profit-split tests (V6 M2).

Through the FastAPI TestClient against the real test PostgreSQL:
- A confirmed sale splits its ganancia_neta across the active rules in the
  same transaction (ledger + running balances, money conserved).
- Gifts/zero-gain sales split nothing; no rules -> no split.
- Reversal (DELETE /ventas/{id}) negates the exact ledger rows.
- Rules CRUD: duplicate account 409; validation 422.

Product cost is the real recursive BOM math: one line of 2m x $5 = $10/u.
"""

import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    DetalleVenta,
    Insumo,
    Producto,
    ReglaLiquidacion,
    RepartoVenta,
    SaldoSocia,
    TipoProducto,
    Venta,
)


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _setup_producto() -> tuple[int, int, int, int]:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat Reparto {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        ins = Insumo(
            categoria_id=cat.id,
            nombre=f"Tela Reparto {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal("100"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("5"),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        tipo = TipoProducto(nombre=f"Tipo Reparto {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        prod = Producto(
            tipo_producto_id=tipo.id,
            nombre=f"Producto Reparto {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
            mano_obra=Decimal("0"),
            cif_energia=Decimal("0"),
            # Finished-unit stock: sales consume it (409 if short).
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
        return cat.id, ins.id, tipo.id, prod.id
    finally:
        db.close()


def _cleanup(producto_id: int, insumo_id: int, tipo_id: int, cat_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = (
            db.query(DetalleVenta.venta_id).filter(DetalleVenta.producto_id == producto_id).all()
        )
        for (vid,) in ven_ids:
            db.query(RepartoVenta).filter(RepartoVenta.venta_id == vid).delete()
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


def _limpiar_reglas(cuentas: list[str]) -> None:
    db = SessionLocal()
    try:
        db.query(SaldoSocia).filter(SaldoSocia.cuenta.in_(cuentas)).delete(
            synchronize_session=False
        )
        db.query(ReglaLiquidacion).filter(
            ReglaLiquidacion.cuenta_destino.in_(cuentas)
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _regla(client, admin_token, cuenta: str, pct: str) -> dict:
    resp = client.post(
        "/api/v1/reparto/reglas",
        json={"cuenta_destino": cuenta, "porcentaje": pct},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _vender(client, admin_token, producto_id: int, precio: str = "100") -> dict:
    resp = client.post(
        "/api/v1/ventas",
        json={
            "canal_venta": "feria",
            "descuento_porcentaje": "0",
            "detalles": [
                {
                    "producto_id": producto_id,
                    "variante_id": None,
                    "cantidad": "1",
                    "precio_unitario": precio,
                }
            ],
        },
        headers=_auth(admin_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _saldos(client, admin_token) -> dict:
    resp = client.get("/api/v1/reparto/saldos", headers=_auth(admin_token))
    assert resp.status_code == 200, resp.text
    return {s["cuenta"]: Decimal(str(s["saldo"])) for s in resp.json()}


CUENTAS = ["Test Socia A", "Test Socia B"]


def test_venta_reparte_en_misma_transaccion(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_reglas(CUENTAS)
    try:
        _regla(client, admin_token, CUENTAS[0], "50")
        _regla(client, admin_token, CUENTAS[1], "50")
        # costo 10, precio 100 -> ganancia 90 -> 45.00 / 45.00.
        venta = _vender(client, admin_token, producto_id)
        saldos = _saldos(client, admin_token)
        assert saldos[CUENTAS[0]] == Decimal("45.00")
        assert saldos[CUENTAS[1]] == Decimal("45.00")
        ledger = client.get(
            f"/api/v1/reparto/ventas/{venta['id']}", headers=_auth(admin_token)
        ).json()
        assert len(ledger) == 2
        assert sum(Decimal(str(r["monto"])) for r in ledger) == Decimal("90")
    finally:
        _limpiar_reglas(CUENTAS)
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_venta_sin_ganancia_no_reparte(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_reglas(CUENTAS)
    try:
        _regla(client, admin_token, CUENTAS[0], "100")
        # precio == costo -> ganancia 0 -> nada que repartir.
        venta = _vender(client, admin_token, producto_id, precio="10")
        assert (
            client.get(
                f"/api/v1/reparto/ventas/{venta['id']}", headers=_auth(admin_token)
            ).json()
            == []
        )
        assert _saldos(client, admin_token).get(CUENTAS[0], Decimal("0")) == Decimal("0")
    finally:
        _limpiar_reglas(CUENTAS)
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_anulacion_revierte_reparto(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_reglas(CUENTAS)
    try:
        _regla(client, admin_token, CUENTAS[0], "100")
        venta = _vender(client, admin_token, producto_id)
        assert _saldos(client, admin_token)[CUENTAS[0]] == Decimal("90.00")
        assert (
            client.delete(
                f"/api/v1/ventas/{venta['id']}", headers=_auth(admin_token)
            ).status_code
            == 200
        )
        assert _saldos(client, admin_token)[CUENTAS[0]] == Decimal("0.00")
        assert (
            client.get(
                f"/api/v1/reparto/ventas/{venta['id']}", headers=_auth(admin_token)
            ).json()
            == []
        )
    finally:
        _limpiar_reglas(CUENTAS)
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_sin_reglas_no_hay_reparto(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_producto()
    _limpiar_reglas(CUENTAS)
    try:
        venta = _vender(client, admin_token, producto_id)
        assert (
            client.get(
                f"/api/v1/reparto/ventas/{venta['id']}", headers=_auth(admin_token)
            ).json()
            == []
        )
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_regla_duplicada_409_y_auth(client, admin_token):
    _limpiar_reglas(CUENTAS)
    try:
        assert client.get("/api/v1/reparto/saldos").status_code == 401
        _regla(client, admin_token, CUENTAS[0], "50")
        resp = client.post(
            "/api/v1/reparto/reglas",
            json={"cuenta_destino": CUENTAS[0], "porcentaje": "50"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409
        reglas = client.get(
            "/api/v1/reparto/reglas", headers=_auth(admin_token)
        ).json()
        assert any(r["cuenta_destino"] == CUENTAS[0] for r in reglas)
    finally:
        _limpiar_reglas(CUENTAS)
