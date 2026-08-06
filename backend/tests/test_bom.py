"""BOM recipes endpoint + validator tests — strict TDD (slice 2, PR 2).

Exercises the bom spec scenarios: nested BOM_Insumos and BOM_Productos CRUD
under /productos/{id}/bom, FK validation (insumo / variante / producto), the
NULL-variant duplicate rule (PostgreSQL NULL != NULL defeats the unique
constraint), waste bounds (0-100), combo duplicates and authorization
(401/403/404/400/409/422). Uses the _unique() uuid4 helper (NOT id(object()))
so rows never collide on unique constraints.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import or_

from app.api.routes.bom import validar_linea_insumo_unica
from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    BomProducto,
    CategoriaInsumo,
    Insumo,
    Producto,
    TipoProducto,
    VarianteProducto,
)

BASE = "/api/v1/productos"


def _unique() -> str:
    return uuid.uuid4().hex[:12]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# DB helpers (direct model setup + cleanup with unique names)
# ---------------------------------------------------------------------------


def _make_categoria(nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        categoria = CategoriaInsumo(nombre=nombre or f"Categoria {_unique()}")
        db.add(categoria)
        db.commit()
        db.refresh(categoria)
        return categoria.id
    finally:
        db.close()


def _make_insumo(categoria_id: int, nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        insumo = Insumo(
            categoria_id=categoria_id,
            nombre=nombre or f"Insumo {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal("0"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("0"),
        )
        db.add(insumo)
        db.commit()
        db.refresh(insumo)
        return insumo.id
    finally:
        db.close()


def _make_tipo(nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        tipo = TipoProducto(nombre=nombre or f"Tipo {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        return tipo.id
    finally:
        db.close()


def _make_producto(tipo_producto_id: int, nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        producto = Producto(
            tipo_producto_id=tipo_producto_id,
            nombre=nombre or f"Producto {_unique()}",
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto.id
    finally:
        db.close()


def _make_variante(producto_id: int, nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        variante = VarianteProducto(
            producto_id=producto_id,
            nombre_variante=nombre or f"Variante {_unique()}",
        )
        db.add(variante)
        db.commit()
        db.refresh(variante)
        return variante.id
    finally:
        db.close()


def _make_linea_insumo(
    producto_id: int,
    insumo_id: int,
    variante_id: int | None = None,
    cantidad: str = "1",
) -> int:
    db = SessionLocal()
    try:
        linea = BomInsumo(
            producto_id=producto_id,
            insumo_id=insumo_id,
            variante_id=variante_id,
            cantidad_requerida=Decimal(cantidad),
            porcentaje_desperdicio=Decimal("0"),
        )
        db.add(linea)
        db.commit()
        db.refresh(linea)
        return linea.id
    finally:
        db.close()


def _make_linea_producto(
    combo_id: int, incluido_id: int, cantidad: str = "1"
) -> int:
    db = SessionLocal()
    try:
        linea = BomProducto(
            combo_id=combo_id,
            producto_incluido_id=incluido_id,
            cantidad=Decimal(cantidad),
        )
        db.add(linea)
        db.commit()
        db.refresh(linea)
        return linea.id
    finally:
        db.close()


def _cleanup_linea_insumo(linea_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.id == linea_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_linea_producto(linea_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomProducto).filter(BomProducto.id == linea_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_insumo(insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.insumo_id == insumo_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
        db.query(BomProducto).filter(
            or_(
                BomProducto.combo_id == producto_id,
                BomProducto.producto_incluido_id == producto_id,
            )
        ).delete(synchronize_session=False)
        db.query(VarianteProducto).filter(
            VarianteProducto.producto_id == producto_id
        ).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_tipo(tipo_id: int) -> None:
    db = SessionLocal()
    try:
        producto_ids = db.query(Producto.id).filter(
            Producto.tipo_producto_id == tipo_id
        )
        db.query(BomInsumo).filter(BomInsumo.producto_id.in_(producto_ids)).delete(
            synchronize_session=False
        )
        db.query(BomProducto).filter(
            or_(
                BomProducto.combo_id.in_(producto_ids),
                BomProducto.producto_incluido_id.in_(producto_ids),
            )
        ).delete(synchronize_session=False)
        db.query(VarianteProducto).filter(
            VarianteProducto.producto_id.in_(producto_ids)
        ).delete(synchronize_session=False)
        db.query(Producto).filter(Producto.tipo_producto_id == tipo_id).delete(
            synchronize_session=False
        )
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_categoria(categoria_id: int) -> None:
    db = SessionLocal()
    try:
        insumo_ids = db.query(Insumo.id).filter(Insumo.categoria_id == categoria_id)
        db.query(BomInsumo).filter(BomInsumo.insumo_id.in_(insumo_ids)).delete(
            synchronize_session=False
        )
        db.query(Insumo).filter(Insumo.categoria_id == categoria_id).delete(
            synchronize_session=False
        )
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == categoria_id).delete()
        db.commit()
    finally:
        db.close()


def _setup_insumo_base() -> tuple[int, int, int]:
    """Returns (categoria_id, insumo_id, tipo_id) with a fresh insumo + tipo."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id)
    tipo_id = _make_tipo()
    return categoria_id, insumo_id, tipo_id


def _teardown_insumo_base(categoria_id: int, insumo_id: int, tipo_id: int) -> None:
    _cleanup_insumo(insumo_id)
    _cleanup_categoria(categoria_id)
    _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# Service-level: validar_linea_insumo_unica (NULL-variant duplicate rule)
# ---------------------------------------------------------------------------


def test_validar_linea_null_null_es_409():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    linea_id = _make_linea_insumo(producto_id, insumo_id, variante_id=None)
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                validar_linea_insumo_unica(db, producto_id, insumo_id, None)
            assert excinfo.value.status_code == 409
        finally:
            db.close()
    finally:
        _cleanup_linea_insumo(linea_id)
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_validar_linea_misma_variante_es_409():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    linea_id = _make_linea_insumo(producto_id, insumo_id, variante_id=variante_id)
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                validar_linea_insumo_unica(db, producto_id, insumo_id, variante_id)
            assert excinfo.value.status_code == 409
        finally:
            db.close()
    finally:
        _cleanup_linea_insumo(linea_id)
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_validar_linea_null_y_variante_ok():
    # A NULL base row and a variant-specific row are distinct rules: a variant
    # line must NOT be flagged as a duplicate of the NULL base line.
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    linea_base_id = _make_linea_insumo(producto_id, insumo_id, variante_id=None)
    try:
        db = SessionLocal()
        try:
            # no raise: NULL base exists, validating a variant-specific line
            validar_linea_insumo_unica(db, producto_id, insumo_id, variante_id)
            linea_variante_id = _make_linea_insumo(
                producto_id, insumo_id, variante_id=variante_id
            )
            try:
                # both rules coexist as separate rows
                assert (
                    db.query(BomInsumo)
                    .filter(
                        BomInsumo.producto_id == producto_id,
                        BomInsumo.insumo_id == insumo_id,
                    )
                    .count()
                    == 2
                )
            finally:
                _cleanup_linea_insumo(linea_variante_id)
        finally:
            db.close()
    finally:
        _cleanup_linea_insumo(linea_base_id)
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


# ---------------------------------------------------------------------------
# BOM_Insumos endpoints
# ---------------------------------------------------------------------------


def test_create_bom_insumo_returns_201_with_waste_default_0(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    try:
        resp = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={"insumo_id": insumo_id, "cantidad_requerida": 2.5},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["producto_id"] == producto_id
        assert body["insumo_id"] == insumo_id
        assert body["variante_id"] is None
        assert Decimal(str(body["cantidad_requerida"])) == Decimal("2.5")
        assert Decimal(str(body["porcentaje_desperdicio"])) == Decimal("0")
        _cleanup_linea_insumo(body["id"])
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_create_bom_insumo_insumo_missing_returns_400(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    try:
        resp = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={"insumo_id": 99999999, "cantidad_requerida": 1},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 400
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_create_bom_insumo_waste_out_of_range_returns_422(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    try:
        for waste in (150, -1):
            resp = client.post(
                f"{BASE}/{producto_id}/bom/insumos",
                json={
                    "insumo_id": insumo_id,
                    "cantidad_requerida": 1,
                    "porcentaje_desperdicio": waste,
                },
                headers=_auth(admin_token),
            )
            assert resp.status_code == 422
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_create_bom_insumo_variante_de_otro_producto_returns_400(
    client, admin_token
):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_a = _make_producto(tipo_id)
    producto_b = _make_producto(tipo_id)
    variante_a = _make_variante(producto_a)
    try:
        resp = client.post(
            f"{BASE}/{producto_b}/bom/insumos",
            json={
                "insumo_id": insumo_id,
                "cantidad_requerida": 1,
                "variante_id": variante_a,
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 400
    finally:
        _cleanup_producto(producto_a)
        _cleanup_producto(producto_b)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_list_bom_insumos_parent_missing_returns_404(client, admin_token):
    resp = client.get(
        f"{BASE}/99999999/bom/insumos", headers=_auth(admin_token)
    )
    assert resp.status_code == 404


def test_create_bom_insumo_dup_null_returns_409(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    try:
        first = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={"insumo_id": insumo_id, "cantidad_requerida": 1},
            headers=_auth(admin_token),
        )
        assert first.status_code == 201
        resp = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={"insumo_id": insumo_id, "cantidad_requerida": 2},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409
        _cleanup_linea_insumo(first.json()["id"])
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_create_bom_insumo_dup_variant_returns_409(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    try:
        first = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={
                "insumo_id": insumo_id,
                "cantidad_requerida": 1,
                "variante_id": variante_id,
            },
            headers=_auth(admin_token),
        )
        assert first.status_code == 201
        resp = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={
                "insumo_id": insumo_id,
                "cantidad_requerida": 1,
                "variante_id": variante_id,
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409
        _cleanup_linea_insumo(first.json()["id"])
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_create_bom_insumo_null_y_variante_returns_201(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    try:
        base = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={"insumo_id": insumo_id, "cantidad_requerida": 1},
            headers=_auth(admin_token),
        )
        assert base.status_code == 201
        especifica = client.post(
            f"{BASE}/{producto_id}/bom/insumos",
            json={
                "insumo_id": insumo_id,
                "cantidad_requerida": 2,
                "variante_id": variante_id,
            },
            headers=_auth(admin_token),
        )
        assert especifica.status_code == 201
        assert especifica.json()["variante_id"] == variante_id
        _cleanup_linea_insumo(base.json()["id"])
        _cleanup_linea_insumo(especifica.json()["id"])
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_list_bom_insumos_returns_lines_ordered(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    insumo_2 = _make_insumo(categoria_id)
    producto_id = _make_producto(tipo_id)
    linea_1 = _make_linea_insumo(producto_id, insumo_id)
    linea_2 = _make_linea_insumo(producto_id, insumo_2)
    try:
        resp = client.get(
            f"{BASE}/{producto_id}/bom/insumos", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 2
        assert [row["id"] for row in rows] == sorted([linea_1, linea_2])
    finally:
        _cleanup_linea_insumo(linea_1)
        _cleanup_linea_insumo(linea_2)
        _cleanup_producto(producto_id)
        _cleanup_insumo(insumo_2)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_update_bom_insumo_returns_200(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    linea_id = _make_linea_insumo(producto_id, insumo_id, variante_id=None)
    try:
        resp = client.put(
            f"{BASE}/{producto_id}/bom/insumos/{linea_id}",
            json={
                "cantidad_requerida": 5,
                "porcentaje_desperdicio": 10,
                "variante_id": variante_id,
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(str(body["cantidad_requerida"])) == Decimal("5")
        assert Decimal(str(body["porcentaje_desperdicio"])) == Decimal("10")
        assert body["variante_id"] == variante_id
        resp = client.put(
            f"{BASE}/{producto_id}/bom/insumos/99999999",
            json={"cantidad_requerida": 1},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404
    finally:
        _cleanup_linea_insumo(linea_id)
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_delete_bom_insumo_returns_204(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    linea_id = _make_linea_insumo(producto_id, insumo_id)
    try:
        resp = client.delete(
            f"{BASE}/{producto_id}/bom/insumos/{linea_id}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204
        rows = client.get(
            f"{BASE}/{producto_id}/bom/insumos", headers=_auth(admin_token)
        ).json()
        assert rows == []
        resp = client.delete(
            f"{BASE}/{producto_id}/bom/insumos/{linea_id}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


# ---------------------------------------------------------------------------
# BOM_Productos endpoints (combos)
# ---------------------------------------------------------------------------


def test_create_bom_producto_returns_201(client, admin_token):
    tipo_id = _make_tipo()
    combo_id = _make_producto(tipo_id)
    incluido_id = _make_producto(tipo_id)
    try:
        resp = client.post(
            f"{BASE}/{combo_id}/bom/productos",
            json={"producto_incluido_id": incluido_id, "cantidad": 3},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["combo_id"] == combo_id
        assert body["producto_incluido_id"] == incluido_id
        assert Decimal(str(body["cantidad"])) == Decimal("3")
        _cleanup_linea_producto(body["id"])
    finally:
        _cleanup_producto(combo_id)
        _cleanup_producto(incluido_id)
        _cleanup_tipo(tipo_id)


def test_create_bom_producto_dup_returns_409(client, admin_token):
    tipo_id = _make_tipo()
    combo_id = _make_producto(tipo_id)
    incluido_id = _make_producto(tipo_id)
    try:
        first = client.post(
            f"{BASE}/{combo_id}/bom/productos",
            json={"producto_incluido_id": incluido_id, "cantidad": 1},
            headers=_auth(admin_token),
        )
        assert first.status_code == 201
        resp = client.post(
            f"{BASE}/{combo_id}/bom/productos",
            json={"producto_incluido_id": incluido_id, "cantidad": 2},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 409
        _cleanup_linea_producto(first.json()["id"])
    finally:
        _cleanup_producto(combo_id)
        _cleanup_producto(incluido_id)
        _cleanup_tipo(tipo_id)


def test_create_bom_producto_included_missing_returns_400(client, admin_token):
    tipo_id = _make_tipo()
    combo_id = _make_producto(tipo_id)
    try:
        resp = client.post(
            f"{BASE}/{combo_id}/bom/productos",
            json={"producto_incluido_id": 99999999, "cantidad": 1},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 400
    finally:
        _cleanup_producto(combo_id)
        _cleanup_tipo(tipo_id)


def test_list_bom_productos_parent_missing_returns_404(client, admin_token):
    resp = client.get(
        f"{BASE}/99999999/bom/productos", headers=_auth(admin_token)
    )
    assert resp.status_code == 404


def test_create_bom_producto_cantidad_zero_returns_422(client, admin_token):
    tipo_id = _make_tipo()
    combo_id = _make_producto(tipo_id)
    incluido_id = _make_producto(tipo_id)
    try:
        for cantidad in (0, -1):
            resp = client.post(
                f"{BASE}/{combo_id}/bom/productos",
                json={"producto_incluido_id": incluido_id, "cantidad": cantidad},
                headers=_auth(admin_token),
            )
            assert resp.status_code == 422
    finally:
        _cleanup_producto(combo_id)
        _cleanup_producto(incluido_id)
        _cleanup_tipo(tipo_id)


def test_list_bom_productos_returns_lines_ordered(client, admin_token):
    tipo_id = _make_tipo()
    combo_id = _make_producto(tipo_id)
    incluido_a = _make_producto(tipo_id)
    incluido_b = _make_producto(tipo_id)
    linea_a = _make_linea_producto(combo_id, incluido_a)
    linea_b = _make_linea_producto(combo_id, incluido_b)
    try:
        resp = client.get(
            f"{BASE}/{combo_id}/bom/productos", headers=_auth(admin_token)
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 2
        assert [row["id"] for row in rows] == sorted([linea_a, linea_b])
    finally:
        _cleanup_linea_producto(linea_a)
        _cleanup_linea_producto(linea_b)
        _cleanup_producto(combo_id)
        _cleanup_producto(incluido_a)
        _cleanup_producto(incluido_b)
        _cleanup_tipo(tipo_id)


def test_update_bom_producto_returns_200(client, admin_token):
    tipo_id = _make_tipo()
    combo_id = _make_producto(tipo_id)
    incluido_a = _make_producto(tipo_id)
    incluido_b = _make_producto(tipo_id)
    linea_id = _make_linea_producto(combo_id, incluido_a)
    try:
        resp = client.put(
            f"{BASE}/{combo_id}/bom/productos/{linea_id}",
            json={"cantidad": 7, "producto_incluido_id": incluido_b},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(str(body["cantidad"])) == Decimal("7")
        assert body["producto_incluido_id"] == incluido_b
        resp = client.put(
            f"{BASE}/{combo_id}/bom/productos/99999999",
            json={"cantidad": 1},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404
    finally:
        _cleanup_linea_producto(linea_id)
        _cleanup_producto(combo_id)
        _cleanup_producto(incluido_a)
        _cleanup_producto(incluido_b)
        _cleanup_tipo(tipo_id)


def test_delete_bom_producto_returns_204(client, admin_token):
    tipo_id = _make_tipo()
    combo_id = _make_producto(tipo_id)
    incluido_id = _make_producto(tipo_id)
    linea_id = _make_linea_producto(combo_id, incluido_id)
    try:
        resp = client.delete(
            f"{BASE}/{combo_id}/bom/productos/{linea_id}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204
        rows = client.get(
            f"{BASE}/{combo_id}/bom/productos", headers=_auth(admin_token)
        ).json()
        assert rows == []
        resp = client.delete(
            f"{BASE}/{combo_id}/bom/productos/{linea_id}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 404
    finally:
        _cleanup_producto(combo_id)
        _cleanup_producto(incluido_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


def test_create_bom_insumo_requires_auth(client):
    resp = client.post(
        f"{BASE}/1/bom/insumos", json={"insumo_id": 1, "cantidad_requerida": 1}
    )
    assert resp.status_code == 401


def test_create_bom_producto_requires_auth(client):
    resp = client.post(
        f"{BASE}/1/bom/productos",
        json={"producto_incluido_id": 1, "cantidad": 1},
    )
    assert resp.status_code == 401


def test_create_bom_insumo_operador_forbidden(client, operador_token):
    resp = client.post(
        f"{BASE}/1/bom/insumos",
        json={"insumo_id": 1, "cantidad_requerida": 1},
        headers=_auth(operador_token),
    )
    assert resp.status_code == 403


def test_create_bom_producto_operador_forbidden(client, operador_token):
    resp = client.post(
        f"{BASE}/1/bom/productos",
        json={"producto_incluido_id": 1, "cantidad": 1},
        headers=_auth(operador_token),
    )
    assert resp.status_code == 403


def test_get_bom_consulta_allowed(client, consulta_token, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base()
    producto_id = _make_producto(tipo_id)
    linea_id = _make_linea_insumo(producto_id, insumo_id)
    try:
        resp = client.get(
            f"{BASE}/{producto_id}/bom/insumos", headers=_auth(consulta_token)
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        resp = client.get(
            f"{BASE}/{producto_id}/bom/productos", headers=_auth(consulta_token)
        )
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        _cleanup_linea_insumo(linea_id)
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)
