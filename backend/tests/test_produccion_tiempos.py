"""Tiempos por fase: tarifa global de energia + minutos reales por fase.

Regla ENERGY: solo la fase 'costura' (maquinas) genera costo de energia;
corte/acabados/calidad son manuales (costo_energia 0). La mano de obra y
los minutos cuentan TODAS las fases.

- PATCH /maestros/parametros-costeo acepta `costo_minuto_energia` (>= 0).
- POST /pedidos-produccion/{id}/tiempos crea un renglon por fase con costos
  derivados (mano: minutos x tasa global, todas las fases; energia:
  minutos x tasa global solo en costura); el segundo POST de la misma fase
  es 409 y PATCH corrige minutos/operaria.
- Validacion de orden: no se puede registrar una fase por delante del pedido
  (400), `listo`/desconocidas son 422.
- El cierre del lote incluye mano_obra_real (todas) + energia_real (costura)
  y NO toca los estimados manuales Producto.mano_obra/cif_energia.
"""

import uuid
from datetime import date
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


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _make_categoria() -> int:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat Tiempos {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat.id
    finally:
        db.close()


def _make_insumo(cat_id: int, stock: str = "100") -> int:
    db = SessionLocal()
    try:
        ins = Insumo(
            categoria_id=cat_id,
            nombre=f"Tela Tiempos {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal(stock),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("5"),
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
        tipo = TipoProducto(nombre=f"Tipo Tiempos {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        return tipo.id
    finally:
        db.close()


def _make_producto(tipo_id: int) -> int:
    db = SessionLocal()
    try:
        prod = Producto(
            tipo_producto_id=tipo_id,
            nombre=f"Producto Tiempos {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
            mano_obra=Decimal("111"),
            cif_energia=Decimal("222"),
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        return prod.id
    finally:
        db.close()


def _make_linea(producto_id: int, insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.add(
            BomInsumo(
                producto_id=producto_id,
                insumo_id=insumo_id,
                cantidad_requerida=Decimal("2"),
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.commit()
    finally:
        db.close()


def _setup(stock_insumo: str = "100"):
    cat_id = _make_categoria()
    insumo_id = _make_insumo(cat_id, stock=stock_insumo)
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_linea(producto_id, insumo_id)
    return cat_id, insumo_id, tipo_id, producto_id


def _cleanup(producto_id: int, insumo_id: int, tipo_id: int, cat_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(PrendaConfeccionada).filter(
            PrendaConfeccionada.producto_id == producto_id
        ).delete(synchronize_session=False)
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


def _tasas_actuales(client, headers) -> dict:
    return client.get("/api/v1/maestros/parametros-costeo", headers=headers).json()


def _fijar_tasas(client, headers, mano: str, energia: str) -> None:
    resp = client.patch(
        "/api/v1/maestros/parametros-costeo",
        json={"costo_minuto_costura": mano, "costo_minuto_energia": energia},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


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


def test_parametros_energia_patch_roundtrip(client, admin_token):
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        resp = client.patch(
            "/api/v1/maestros/parametros-costeo",
            json={"costo_minuto_energia": "12.5"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(str(resp.json()["costo_minuto_energia"])) == Decimal("12.5")
        # Pre-existing rates untouched by the patch.
        assert Decimal(str(resp.json()["costo_minuto_costura"])) == Decimal(
            str(prev["costo_minuto_costura"])
        )
        # Negative energy rate is rejected.
        resp = client.patch(
            "/api/v1/maestros/parametros-costeo",
            json={"costo_minuto_energia": -1},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )


def test_crear_tiempo_y_totales(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        _fijar_tasas(client, headers, "100", "10")
        pedido_id = _crear_pedido(client, headers, producto_id)

        resp = client.post(
            f"/api/v1/pedidos-produccion/{pedido_id}/tiempos",
            json={"fase": "corte", "operaria": "Ana", "minutos_reales": "30"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        row = resp.json()
        assert row["fase"] == "corte"
        assert row["operaria"] == "Ana"
        assert Decimal(str(row["minutos_reales"])) == Decimal("30")
        assert row["fecha"] == date.today().isoformat()
        # 30 min x 100 mano; corte es manual -> energia 0.
        assert Decimal(str(row["costo_mano_obra"])) == Decimal("3000")
        assert Decimal(str(row["costo_energia"])) == Decimal("0")

        resp = client.get(
            f"/api/v1/pedidos-produccion/{pedido_id}/tiempos", headers=headers
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["items"]) == 1
        assert Decimal(str(body["total_minutos"])) == Decimal("30")
        assert Decimal(str(body["total_mano_obra"])) == Decimal("3000")
        assert Decimal(str(body["total_energia"])) == Decimal("0")

        # Unknown pedido is 404.
        assert (
            client.get("/api/v1/pedidos-produccion/999999/tiempos", headers=headers).status_code
            == 404
        )
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_energia_solo_costura(client, admin_token):
    """ENERGY solo en costura: corte 30min + costura 60min.

    Energia = 60 x tasa_energia (solo costura); mano = 90 x tasa_costura
    (todas las fases); minutos = 90 (es tiempo). El pedido expone los
    mismos totales via mano_obra_real/energia_real.
    """
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        _fijar_tasas(client, headers, "100", "10")
        pedido_id = _crear_pedido(client, headers, producto_id)
        url = f"/api/v1/pedidos-produccion/{pedido_id}/tiempos"

        resp = client.post(
            url,
            json={"fase": "corte", "operaria": "Ana", "minutos_reales": "30"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        assert Decimal(str(resp.json()["costo_mano_obra"])) == Decimal("3000")
        assert Decimal(str(resp.json()["costo_energia"])) == Decimal("0")

        assert _avanzar(client, headers, pedido_id, "costura").status_code == 200
        resp = client.post(
            url,
            json={"fase": "costura", "operaria": "Bea", "minutos_reales": "60"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        assert Decimal(str(resp.json()["costo_mano_obra"])) == Decimal("6000")
        assert Decimal(str(resp.json()["costo_energia"])) == Decimal("600")

        body = client.get(url, headers=headers).json()
        assert Decimal(str(body["total_minutos"])) == Decimal("90")
        assert Decimal(str(body["total_mano_obra"])) == Decimal("9000")
        assert Decimal(str(body["total_energia"])) == Decimal("600")

        body = client.get(
            f"/api/v1/pedidos-produccion/{pedido_id}", headers=headers
        ).json()
        assert Decimal(str(body["mano_obra_real"])) == Decimal("9000")
        assert Decimal(str(body["energia_real"])) == Decimal("600")
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_tiempo_duplicado_409_y_patch_corrige(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        _fijar_tasas(client, headers, "50", "5")
        pedido_id = _crear_pedido(client, headers, producto_id)
        url = f"/api/v1/pedidos-produccion/{pedido_id}/tiempos"

        assert (
            client.post(
                url,
                json={"fase": "corte", "operaria": "Ana", "minutos_reales": "30"},
                headers=headers,
            ).status_code
            == 201
        )
        # Second POST for the same phase is a 409, not a silent overwrite.
        resp = client.post(
            url,
            json={"fase": "corte", "operaria": "Bea", "minutos_reales": "10"},
            headers=headers,
        )
        assert resp.status_code == 409, resp.text
        assert "corte" in resp.json()["detail"]
        assert (
            client.get(url, headers=headers).json()["items"][0]["operaria"] == "Ana"
        )

        # PATCH corrects minutes/operaria (derived money follows).
        tiempo_id = client.get(url, headers=headers).json()["items"][0]["id"]
        resp = client.patch(
            f"{url}/{tiempo_id}",
            json={"operaria": "Bea", "minutos_reales": "40"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["operaria"] == "Bea"
        assert Decimal(str(resp.json()["costo_mano_obra"])) == Decimal("2000")
        # Corte es manual: energia 0 aunque haya minutos.
        assert Decimal(str(resp.json()["costo_energia"])) == Decimal("0")
        # Non-positive minutes are rejected by the schema.
        resp = client.patch(
            f"{url}/{tiempo_id}", json={"minutos_reales": "0"}, headers=headers
        )
        assert resp.status_code == 422, resp.text
        # Unknown tiempo id is 404.
        resp = client.patch(f"{url}/999999", json={"operaria": "X"}, headers=headers)
        assert resp.status_code == 404, resp.text
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_tiempo_fuera_de_orden_400(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    try:
        pedido_id = _crear_pedido(client, headers, producto_id)
        url = f"/api/v1/pedidos-produccion/{pedido_id}/tiempos"

        # Pedido is in corte: costura is ahead -> 400.
        resp = client.post(
            url,
            json={"fase": "costura", "operaria": "Ana", "minutos_reales": "10"},
            headers=headers,
        )
        assert resp.status_code == 400, resp.text
        # `listo` closes the lot, it is never a worked phase -> 422.
        resp = client.post(
            url,
            json={"fase": "listo", "operaria": "Ana", "minutos_reales": "10"},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text
        # Unknown phase -> 422.
        resp = client.post(
            url,
            json={"fase": "planchado", "operaria": "Ana", "minutos_reales": "10"},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # After advancing, costura is loggable (corte stays loggable too).
        assert _avanzar(client, headers, pedido_id, "costura").status_code == 200
        assert (
            client.post(
                url,
                json={"fase": "costura", "operaria": "Ana", "minutos_reales": "10"},
                headers=headers,
            ).status_code
            == 201
        )
        assert (
            client.post(
                url,
                json={"fase": "corte", "operaria": "Ana", "minutos_reales": "5"},
                headers=headers,
            ).status_code
            == 201
        )
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_cierre_incluye_totales_reales_sin_tocar_estimados(client, admin_token):
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        _fijar_tasas(client, headers, "100", "10")
        pedido_id = _crear_pedido(client, headers, producto_id, cantidad=10)
        url = f"/api/v1/pedidos-produccion/{pedido_id}/tiempos"

        plan = (("corte", "60"), ("costura", "120"), ("acabados", "30"), ("calidad", "15"))
        for i, (fase, minutos) in enumerate(plan):
            resp = client.post(
                url,
                json={"fase": fase, "operaria": "Ana", "minutos_reales": minutos},
                headers=headers,
            )
            assert resp.status_code == 201, resp.text
            if i < len(plan) - 1:
                assert _avanzar(client, headers, pedido_id, plan[i + 1][0]).status_code == 200

        resp = _avanzar(client, headers, pedido_id, "listo")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # 225 min x 100 mano (todas las fases); energia solo costura 120 x 10.
        assert Decimal(str(body["mano_obra_real"])) == Decimal("22500")
        assert Decimal(str(body["energia_real"])) == Decimal("1200")
        # Manual estimates on Producto stay exactly as set.
        db = SessionLocal()
        try:
            prod = db.get(Producto, producto_id)
            assert prod is not None
            assert prod.mano_obra == Decimal("111")
            assert prod.cif_energia == Decimal("222")
            assert prod.stock_actual == Decimal("0")
            assert (
                db.query(PrendaConfeccionada)
                .filter(
                    PrendaConfeccionada.producto_id == producto_id,
                    PrendaConfeccionada.estado == "disponible",
                )
                .count()
                == 10
            )
        finally:
            db.close()
        # Totals also ride on plain GET.
        body = client.get(
            f"/api/v1/pedidos-produccion/{pedido_id}", headers=headers
        ).json()
        assert Decimal(str(body["mano_obra_real"])) == Decimal("22500")
        assert Decimal(str(body["energia_real"])) == Decimal("1200")
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)


def test_tiempos_cascada_al_borrar_pedido(client, admin_token, db_session):
    """Deleting the pedido removes its tiempos (DB CASCADE)."""
    cat_id, insumo_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    try:
        pedido_id = _crear_pedido(client, headers, producto_id)
        url = f"/api/v1/pedidos-produccion/{pedido_id}/tiempos"
        assert (
            client.post(
                url,
                json={"fase": "corte", "operaria": "Ana", "minutos_reales": "10"},
                headers=headers,
            ).status_code
            == 201
        )
        assert db_session.query(TiempoFase).filter(
            TiempoFase.pedido_id == pedido_id
        ).count() == 1
        assert (
            client.delete(f"/api/v1/pedidos-produccion/{pedido_id}", headers=headers).status_code
            == 204
        )
        db_session.expire_all()
        assert (
            db_session.query(TiempoFase).filter(TiempoFase.pedido_id == pedido_id).count()
            == 0
        )
    finally:
        _cleanup(producto_id, insumo_id, tipo_id, cat_id)
