"""Lote por cantidad: fases Corte->Listo, completar_lote y stock por cantidad.

- POST /pedidos-produccion defaults fase='corte', snapshot None.
- PATCH fase advances one step (400 skip/back, 422 unknown).
- Reaching 'listo' explodes the BOM (N=cantidad), deducts insumos, credits
  Producto.stock_actual += N, snapshots unit cost; 409 names every short
  insumo with required vs. available and persists nothing.
- Completion runs once (idempotent on later PATCHes).
- POST /ventas consumes Producto.stock_actual (409 if short); anular restores.
"""

import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    DetalleVenta,
    Insumo,
    PedidoProduccion,
    Producto,
    TipoProducto,
    Venta,
)


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _make_categoria() -> int:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat Lote {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat.id
    finally:
        db.close()


def _make_insumo(cat_id: int, costo: str = "5", stock: str = "100") -> int:
    db = SessionLocal()
    try:
        ins = Insumo(
            categoria_id=cat_id,
            nombre=f"Tela Lote {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal(stock),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal(costo),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        return ins.id
    finally:
        db.close()


def _make_tipo() -> int:
    db = SessionLocal()
    try:
        tipo = TipoProducto(nombre=f"Tipo Lote {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        return tipo.id
    finally:
        db.close()


def _make_producto(tipo_id: int) -> int:
    """Product WITHOUT variants and zero finished stock (completion credits it)."""
    db = SessionLocal()
    try:
        prod = Producto(
            tipo_producto_id=tipo_id,
            nombre=f"Producto Lote {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        return prod.id
    finally:
        db.close()


def _make_linea(producto_id: int, insumo_id: int, cantidad: str = "2") -> None:
    db = SessionLocal()
    try:
        db.add(
            BomInsumo(
                producto_id=producto_id,
                insumo_id=insumo_id,
                cantidad_requerida=Decimal(cantidad),
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.commit()
    finally:
        db.close()


def _read_producto_stock(producto_id: int) -> Decimal:
    db = SessionLocal()
    try:
        producto = db.get(Producto, producto_id)
        assert producto is not None
        return producto.stock_actual or Decimal("0")
    finally:
        db.close()


def _read_insumo_stock(insumo_id: int) -> Decimal:
    db = SessionLocal()
    try:
        insumo = db.get(Insumo, insumo_id)
        assert insumo is not None
        return insumo.stock_actual
    finally:
        db.close()


def _setup_lote(stock_insumo: str = "100"):
    """Categoria + insumo(5$/m) + tipo + producto + BOM(2m/u). No variants."""
    cat_id = _make_categoria()
    insumo_id = _make_insumo(cat_id, stock=stock_insumo)
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_linea(producto_id, insumo_id)
    return cat_id, insumo_id, tipo_id, producto_id


def _cleanup(producto_id: int, insumo_id: int, tipo_id: int, cat_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = (
            db.query(DetalleVenta.venta_id)
            .filter(DetalleVenta.producto_id == producto_id)
            .all()
        )
        ven_ids = [v[0] for v in ven_ids]
        if ven_ids:
            db.query(DetalleVenta).filter(DetalleVenta.venta_id.in_(ven_ids)).delete(
                synchronize_session=False
            )
            db.query(Venta).filter(Venta.id.in_(ven_ids)).delete(
                synchronize_session=False
            )
        db.query(PedidoProduccion).filter(
            PedidoProduccion.producto_id == producto_id
        ).delete(synchronize_session=False)
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == cat_id).delete()
        db.commit()
    finally:
        db.close()


def _auth(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


def _avanzar(client, headers, pedido_id: int, fase: str):
    return client.patch(
        f"/api/v1/pedidos-produccion/{pedido_id}", json={"fase": fase}, headers=headers
    )


def test_pedido_defaults_fase_corte(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_lote()
    try:
        resp = client.post(
            "/api/v1/pedidos-produccion",
            json={"producto_id": producto_id, "cantidad": 3},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["fase"] == "corte"
        assert body["costo_unitario_snapshot"] is None
        assert _read_producto_stock(producto_id) == Decimal("0")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_avance_secuencial_y_rechazos(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_lote()
    try:
        headers = _auth(admin_token)
        pedido_id = client.post(
            "/api/v1/pedidos-produccion",
            json={"producto_id": producto_id, "cantidad": 2},
            headers=headers,
        ).json()["id"]

        assert _avanzar(client, headers, pedido_id, "costura").status_code == 200
        # Skipping acabados straight to calidad is rejected.
        resp = _avanzar(client, headers, pedido_id, "calidad")
        assert resp.status_code == 400, resp.text
        # Backwards (devolución) is allowed to any earlier phase.
        resp = _avanzar(client, headers, pedido_id, "corte")
        assert resp.status_code == 200, resp.text
        # Unknown fase is rejected.
        resp = _avanzar(client, headers, pedido_id, "planchado")
        assert resp.status_code == 422, resp.text
        # Back on corte, nothing consumed.
        assert _read_insumo_stock(insumo_id) == Decimal("100")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_devolucion_calidad_a_costura_y_listo_congelado(client, admin_token):
    """calidad -> costura (reproceso) OK; desde listo no hay movimientos."""
    cat_id, insumo_id, tipo_id, producto_id = _setup_lote()
    try:
        headers = _auth(admin_token)
        pedido_id = client.post(
            "/api/v1/pedidos-produccion",
            json={"producto_id": producto_id, "cantidad": 2},
            headers=headers,
        ).json()["id"]
        for fase in ("costura", "acabados", "calidad"):
            assert _avanzar(client, headers, pedido_id, fase).status_code == 200
        # Devolución dos pasos atrás: calidad -> costura.
        resp = _avanzar(client, headers, pedido_id, "costura")
        assert resp.status_code == 200, resp.text
        assert resp.json()["fase"] == "costura"
        assert _read_insumo_stock(insumo_id) == Decimal("100")
        # Re-avance normal hasta listo: acredita una sola vez.
        for fase in ("acabados", "calidad", "listo"):
            assert _avanzar(client, headers, pedido_id, fase).status_code == 200
        assert _read_producto_stock(producto_id) == Decimal("2")
        # Listo congelado: ni atrás ni a otra fase.
        resp = _avanzar(client, headers, pedido_id, "costura")
        assert resp.status_code == 400, resp.text
        assert _read_producto_stock(producto_id) == Decimal("2")
        assert _read_insumo_stock(insumo_id) == Decimal("96")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_completar_lote_acredita_stock_y_snapshot(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_lote()
    try:
        headers = _auth(admin_token)
        pedido_id = client.post(
            "/api/v1/pedidos-produccion",
            json={"producto_id": producto_id, "cantidad": 10},
            headers=headers,
        ).json()["id"]
        for fase in ("costura", "acabados", "calidad"):
            resp = _avanzar(client, headers, pedido_id, fase)
            assert resp.status_code == 200, resp.text
        assert _read_producto_stock(producto_id) == Decimal("0")

        resp = _avanzar(client, headers, pedido_id, "listo")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["fase"] == "listo"
        assert body["cantidad_producida"] == 10
        # 2 m/u x 5 $/m = 10 $/u snapshot.
        assert Decimal(str(body["costo_unitario_snapshot"])) == Decimal("10")
        assert _read_producto_stock(producto_id) == Decimal("10")
        assert _read_insumo_stock(insumo_id) == Decimal("80")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_completar_lote_faltante_409_atomico(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_lote(stock_insumo="1")
    try:
        headers = _auth(admin_token)
        pedido_id = client.post(
            "/api/v1/pedidos-produccion",
            json={"producto_id": producto_id, "cantidad": 10},
            headers=headers,
        ).json()["id"]
        db = SessionLocal()
        try:
            ins = db.get(Insumo, insumo_id)
            assert ins is not None
            nombre_insumo = ins.nombre
        finally:
            db.close()
        for fase in ("costura", "acabados", "calidad"):
            assert _avanzar(client, headers, pedido_id, fase).status_code == 200

        resp = _avanzar(client, headers, pedido_id, "listo")
        assert resp.status_code == 409, resp.text
        assert nombre_insumo in resp.json()["detail"]
        # Atomic: still on calidad, stocks untouched.
        pedido = client.get(
            f"/api/v1/pedidos-produccion/{pedido_id}", headers=headers
        ).json()
        assert pedido["fase"] == "calidad"
        assert _read_producto_stock(producto_id) == Decimal("0")
        assert _read_insumo_stock(insumo_id) == Decimal("1")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_completar_lote_idempotente(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_lote()
    try:
        headers = _auth(admin_token)
        pedido_id = client.post(
            "/api/v1/pedidos-produccion",
            json={"producto_id": producto_id, "cantidad": 10},
            headers=headers,
        ).json()["id"]
        for fase in ("costura", "acabados", "calidad", "listo"):
            assert _avanzar(client, headers, pedido_id, fase).status_code == 200
        assert _read_producto_stock(producto_id) == Decimal("10")

        # A later PATCH must NOT complete (and credit) twice.
        resp = client.patch(
            f"/api/v1/pedidos-produccion/{pedido_id}",
            json={"observaciones": "nota post-cierre"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert _read_producto_stock(producto_id) == Decimal("10")
        assert _read_insumo_stock(insumo_id) == Decimal("80")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_venta_consume_y_anular_repone_stock_producto(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup_lote()
    try:
        headers = _auth(admin_token)
        pedido_id = client.post(
            "/api/v1/pedidos-produccion",
            json={"producto_id": producto_id, "cantidad": 10},
            headers=headers,
        ).json()["id"]
        for fase in ("costura", "acabados", "calidad", "listo"):
            assert _avanzar(client, headers, pedido_id, fase).status_code == 200

        def _payload(cantidad: str) -> dict:
            return {
                "canal_venta": "feria",
                "descuento_porcentaje": "0",
                "detalles": [
                    {
                        "producto_id": producto_id,
                        "variante_id": None,
                        "cantidad": cantidad,
                        "precio_unitario": "10",
                    }
                ],
            }

        # 11 > 10 finished units -> 409 naming the product.
        resp = client.post("/api/v1/ventas", json=_payload("11"), headers=headers)
        assert resp.status_code == 409, resp.text
        assert "Producto Lote" in resp.json()["detail"]

        resp = client.post("/api/v1/ventas", json=_payload("4"), headers=headers)
        assert resp.status_code == 201, resp.text
        venta_id = resp.json()["id"]
        assert _read_producto_stock(producto_id) == Decimal("6")

        resp = client.delete(f"/api/v1/ventas/{venta_id}", headers=headers)
        assert resp.status_code == 200, resp.text
        assert _read_producto_stock(producto_id) == Decimal("10")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)
