from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.models.insumos import CategoriaInsumo, Insumo
from app.models.produccion import PedidoProduccion, PrendaConfeccionada
from app.models.productos import BomInsumo, Producto, TipoProducto, VarianteProducto


def test_insumos_fase4_fields(client: TestClient, db_session, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    cat = CategoriaInsumo(nombre="Telas Fase 4")
    db_session.add(cat)
    db_session.commit()

    # Create insumo with new fields
    payload = {
        "categoria_id": cat.id,
        "nombre": "Seda Negra Especial",
        "unidad_medida": "metros",
        "codigo": "INS-SEDA-01",
        "descripcion": "Seda italiana para forro",
        "tipo": "Directo",
        "ubicacion": "Estante A-1",
        "stock_actual": 50,
        "stock_minimo": 10,
        "costo_promedio_actual": 25000,
    }
    resp = client.post("/api/v1/insumos", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["codigo"] == "INS-SEDA-01"
    assert data["descripcion"] == "Seda italiana para forro"
    assert data["tipo"] == "Directo"
    assert data["ubicacion"] == "Estante A-1"
    insumo_id = data["id"]

    # Filter by q (codigo/tipo/ubicacion)
    resp_q = client.get("/api/v1/insumos?q=SEDA-01", headers=headers)
    assert resp_q.status_code == 200
    assert any(i["id"] == insumo_id for i in resp_q.json()["items"])

    # Filter by tipo
    resp_tipo = client.get("/api/v1/insumos?tipo=Directo", headers=headers)
    assert resp_tipo.status_code == 200
    assert any(i["id"] == insumo_id for i in resp_tipo.json()["items"])

    # Update patch
    resp_patch = client.patch(
        f"/api/v1/insumos/{insumo_id}",
        json={"ubicacion": "Estante B-2"},
        headers=headers,
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["ubicacion"] == "Estante B-2"


def test_bom_fase4_fields(client: TestClient, db_session, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    cat = CategoriaInsumo(nombre="Avíos Fase 4")
    tipo_p = TipoProducto(nombre="Corsetería Fase 4")
    db_session.add_all([cat, tipo_p])
    db_session.commit()

    insumo = Insumo(
        categoria_id=cat.id,
        nombre="Varilla de Acero",
        unidad_medida="unidades",
        stock_actual=Decimal("100"),
        stock_minimo=Decimal("20"),
        costo_promedio_actual=Decimal("1500"),
    )
    prod = Producto(
        tipo_producto_id=tipo_p.id,
        nombre="Corset Noir",
        costos_operativos_fijos=Decimal("10000"),
    )
    db_session.add_all([insumo, prod])
    db_session.commit()

    # Create BomInsumo with fases and markup
    fases = [
        {"nombre": "Corte", "minutos": 15},
        {"nombre": "Costura", "minutos": 45},
    ]
    payload = {
        "insumo_id": insumo.id,
        "cantidad_requerida": 8,
        "porcentaje_desperdicio": 0,
        "fases": fases,
        "tiempo_estimado_minutos": 60,
        "markup_porcentual": 200,
    }
    resp = client.post(f"/api/v1/productos/{prod.id}/bom/insumos", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["fases"] == fases
    assert data["tiempo_estimado_minutos"] == 60
    assert float(data["markup_porcentual"]) == 200.0


def test_prendas_y_pedidos_crud(client: TestClient, db_session, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    tipo_p = TipoProducto(nombre="Vestidos Fase 4")
    db_session.add(tipo_p)
    db_session.commit()

    prod = Producto(
        tipo_producto_id=tipo_p.id,
        nombre="Vestido Gala",
        costos_operativos_fijos=Decimal("20000"),
    )
    db_session.add(prod)
    db_session.commit()

    var = VarianteProducto(
        producto_id=prod.id,
        nombre_variante="Vestido Gala - Negro / M",
        precio_venta=Decimal("250000"),
    )
    db_session.add(var)
    db_session.commit()

    # 1. Create PedidoProduccion
    pedido_payload = {
        "producto_id": prod.id,
        "variante_id": var.id,
        "cantidad": 5,
        "prioridad": "alta",
        "observaciones": "Pedido para evento de moda",
    }
    resp_ped = client.post("/api/v1/pedidos-produccion", json=pedido_payload, headers=headers)
    assert resp_ped.status_code == 201, resp_ped.text
    pedido_data = resp_ped.json()
    assert pedido_data["id"] is not None
    assert pedido_data["prioridad"] == "alta"
    assert pedido_data["estado"] == "pendiente"
    assert pedido_data["nombre_producto"] == "Vestido Gala"
    assert pedido_data["nombre_variante"] == "Vestido Gala - Negro / M"
    pedido_id = pedido_data["id"]

    # 2. List Pedidos
    resp_list_ped = client.get("/api/v1/pedidos-produccion?prioridad=alta", headers=headers)
    assert resp_list_ped.status_code == 200
    assert any(p["id"] == pedido_id for p in resp_list_ped.json()["items"])

    # 3. Update Pedido
    resp_up_ped = client.patch(
        f"/api/v1/pedidos-produccion/{pedido_id}",
        json={"estado": "en_produccion", "cantidad_producida": 2},
        headers=headers,
    )
    assert resp_up_ped.status_code == 200
    assert resp_up_ped.json()["estado"] == "en_produccion"
    assert resp_up_ped.json()["cantidad_producida"] == 2

    # 4. Create PrendaConfeccionada linked to pedido
    prenda_payload = {
        "variante_id": var.id,
        "talla": "M",
        "estado": "disponible",
        "ubicacion": "Perchero Principal",
        "costo_real": 120000,
        "precio_venta": 250000,
        "pedido_id": pedido_id,
    }
    resp_prenda = client.post("/api/v1/prendas-confeccionadas", json=prenda_payload, headers=headers)
    assert resp_prenda.status_code == 201, resp_prenda.text
    prenda_data = resp_prenda.json()
    assert prenda_data["id"] is not None
    assert prenda_data["pedido_id"] == pedido_id
    assert prenda_data["ubicacion"] == "Perchero Principal"
    assert prenda_data["nombre_producto"] == "Vestido Gala"
    assert prenda_data["nombre_variante"] == "Vestido Gala - Negro / M"
    prenda_id = prenda_data["id"]

    # 5. List Prendas
    resp_list_prendas = client.get("/api/v1/prendas-confeccionadas?estado=disponible", headers=headers)
    assert resp_list_prendas.status_code == 200
    assert any(p["id"] == prenda_id for p in resp_list_prendas.json()["items"])

    # 6. Update Prenda
    resp_up_prenda = client.patch(
        f"/api/v1/prendas-confeccionadas/{prenda_id}",
        json={"estado": "vendida"},
        headers=headers,
    )
    assert resp_up_prenda.status_code == 200
    assert resp_up_prenda.json()["estado"] == "vendida"

    # 7. Delete Prenda
    resp_del_prenda = client.delete(f"/api/v1/prendas-confeccionadas/{prenda_id}", headers=headers)
    assert resp_del_prenda.status_code == 204

    # 8. Delete Pedido
    resp_del_ped = client.delete(f"/api/v1/pedidos-produccion/{pedido_id}", headers=headers)
    assert resp_del_ped.status_code == 204


def test_prendas_y_pedidos_invalid_fks_400(client: TestClient, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Prenda with non-existing variante
    resp = client.post(
        "/api/v1/prendas-confeccionadas",
        json={"variante_id": 999999, "talla": "S"},
        headers=headers,
    )
    assert resp.status_code == 400

    # Pedido with non-existing producto
    resp2 = client.post(
        "/api/v1/pedidos-produccion",
        json={"producto_id": 999999, "cantidad": 5},
        headers=headers,
    )
    assert resp2.status_code == 400


def test_prendas_y_pedidos_not_found_404(client: TestClient, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    assert client.get("/api/v1/prendas-confeccionadas/999999", headers=headers).status_code == 404
    assert client.patch("/api/v1/prendas-confeccionadas/999999", json={"talla": "L"}, headers=headers).status_code == 404
    assert client.delete("/api/v1/prendas-confeccionadas/999999", headers=headers).status_code == 404

    assert client.get("/api/v1/pedidos-produccion/999999", headers=headers).status_code == 404
    assert client.patch("/api/v1/pedidos-produccion/999999", json={"cantidad": 10}, headers=headers).status_code == 404
    assert client.delete("/api/v1/pedidos-produccion/999999", headers=headers).status_code == 404
