"""Stock reservation tests (V6 M4).

Against the real test PostgreSQL, through the FastAPI TestClient:
- Creating a pedido reserves its full BOM explosion (actual untouched).
- Completing releases the lot's share AND deducts actual stock.
- A second open pedido can starve the first: completion judges
  (actual - others' reservations) and 409s with detail.
- A failed completion keeps the lot's reservation (retry stays possible).
- Deleting an open pedido releases its share; double completion is a no-op.

Setup: one BOM line of 2m x $5 (fijos 0), insumo stock parametrizable.
"""

import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    Insumo,
    PedidoProduccion,
    PrendaConfeccionada,
    Producto,
    TiempoFase,
    TipoProducto,
)

FASES = ["costura", "acabados", "calidad", "listo"]


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _setup(stock_insumo: str = "100"):
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat Reserva {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        ins = Insumo(
            categoria_id=cat.id,
            nombre=f"Tela Reserva {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal(stock_insumo),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("5"),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        tipo = TipoProducto(nombre=f"Tipo Reserva {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        prod = Producto(
            tipo_producto_id=tipo.id,
            nombre=f"Producto Reserva {_unique()}",
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


def _cleanup(producto_id: int, insumo_id: int, tipo_id: int, cat_id: int) -> None:
    db = SessionLocal()
    try:
        pids = (
            db.query(PedidoProduccion.id)
            .filter(PedidoProduccion.producto_id == producto_id)
            .all()
        )
        for (pid,) in pids:
            db.query(TiempoFase).filter(TiempoFase.pedido_id == pid).delete()
        db.query(PrendaConfeccionada).filter(
            PrendaConfeccionada.producto_id == producto_id
        ).delete(synchronize_session=False)
        db.query(PedidoProduccion).filter(
            PedidoProduccion.producto_id == producto_id
        ).delete()
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


def _crear_pedido(client, headers, producto_id: int, cantidad: int = 4) -> int:
    resp = client.post(
        "/api/v1/pedidos-produccion",
        json={"producto_id": producto_id, "cantidad": cantidad},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _avanzar(client, headers, pedido_id: int, fase: str):
    return client.patch(
        f"/api/v1/pedidos-produccion/{pedido_id}", json={"fase": fase}, headers=headers
    )


def _cerrar(client, headers, pedido_id: int):
    for fase in FASES:
        resp = _avanzar(client, headers, pedido_id, fase)
        assert resp.status_code == 200, resp.text


def _stocks(insumo_id: int) -> tuple[Decimal, Decimal]:
    db = SessionLocal()
    try:
        ins = db.get(Insumo, insumo_id)
        assert ins is not None
        return Decimal(ins.stock_actual), Decimal(ins.stock_reservado)
    finally:
        db.close()


def test_crear_pedido_reserva_sin_tocar_actual(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    try:
        _crear_pedido(client, headers, producto_id, cantidad=4)
        actual, reservado = _stocks(insumo_id)
        assert actual == Decimal("100")
        assert reservado == Decimal("8")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_completar_libera_y_descuenta(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    try:
        pedido_id = _crear_pedido(client, headers, producto_id, cantidad=4)
        _cerrar(client, headers, pedido_id)
        actual, reservado = _stocks(insumo_id)
        assert reservado == Decimal("0")
        assert actual == Decimal("92")
        # Double completion is a no-op: nothing moves twice.
        assert _avanzar(client, headers, pedido_id, "listo").status_code == 200
        actual, reservado = _stocks(insumo_id)
        assert (actual, reservado) == (Decimal("92"), Decimal("0"))
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_segundo_pedido_puede_bloquear_cierre(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup(stock_insumo="10")
    headers = _auth(admin_token)
    try:
        # A reserves 8 (disponible 2); B reserves 6 (over-books to 14).
        pedido_a = _crear_pedido(client, headers, producto_id, cantidad=4)
        pedido_b = _crear_pedido(client, headers, producto_id, cantidad=3)
        # B cannot close: free = 10 - 8 (A's) = 2 < 6 -> honest 409.
        resp = _avanzar(client, headers, pedido_b, "costura")
        assert resp.status_code == 200
        for fase in ["acabados", "calidad"]:
            assert _avanzar(client, headers, pedido_b, fase).status_code == 200
        resp = _avanzar(client, headers, pedido_b, "listo")
        assert resp.status_code == 409, resp.text
        # The failed close kept B's reservation: still starved, still honest.
        actual, reservado = _stocks(insumo_id)
        assert actual == Decimal("10")
        assert reservado == Decimal("14")
        # Overbooking is real (14 > 10): B must yield before A can close.
        assert (
            client.delete(
                f"/api/v1/pedidos-produccion/{pedido_b}", headers=headers
            ).status_code
            == 204
        )
        assert _stocks(insumo_id) == (Decimal("10"), Decimal("8"))
        _cerrar(client, headers, pedido_a)
        actual, reservado = _stocks(insumo_id)
        assert actual == Decimal("2")
        assert reservado == Decimal("0")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_borrar_pedido_libera_reserva(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    try:
        pedido_id = _crear_pedido(client, headers, producto_id, cantidad=4)
        assert _stocks(insumo_id)[1] == Decimal("8")
        assert (
            client.delete(
                f"/api/v1/pedidos-produccion/{pedido_id}", headers=headers
            ).status_code
            == 204
        )
        actual, reservado = _stocks(insumo_id)
        assert actual == Decimal("100")
        assert reservado == Decimal("0")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_respuesta_expone_reservado_y_disponible(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    try:
        _crear_pedido(client, headers, producto_id, cantidad=4)
        resp = client.get("/api/v1/insumos", headers=headers)
        assert resp.status_code == 200, resp.text
        items = resp.json()["items"]
        row = next(r for r in items if r["nombre"].startswith("Tela Reserva"))
        assert Decimal(str(row["stock_reservado"])) == Decimal("8")
        assert Decimal(str(row["disponible"])) == Decimal("92")
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)
