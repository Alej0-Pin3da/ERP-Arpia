"""Cost engine tests — strict TDD (slice 3, PR 3).

Exercises the costos-produccion spec scenarios: single-level insumo cost,
waste math, multilevel combos, variant override vs base fallback,
non-fabricated / no-BOM cost rule, cycle detection (409), Decimal precision
without engine rounding, memoization (diamond + before_cursor_execute counter)
and the GET /productos/{id}/costo endpoint (200/404/409/401, any role).
Uses the _unique() uuid4 helper (NOT id(object())) and BOM-aware cleanup with
correct FK ordering (BOM lines -> variantes -> productos -> insumos ->
categorias -> tipos).
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import event, or_

from app.core.exceptions import BomCycleDetectedError
from app.db.session import SessionLocal, engine
from app.models import (
    BomInsumo,
    BomProducto,
    CategoriaInsumo,
    Insumo,
    Producto,
    TipoProducto,
    VarianteProducto,
)
from app.services.costos import calcular_costo_produccion, desglosar_costo_produccion

BASE = "/api/v1/productos"


def _unique() -> str:
    return uuid.uuid4().hex[:12]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# DB helpers (direct model setup with unique names + cost parameters)
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


def _make_insumo(categoria_id: int, costo: str = "0", nombre: str | None = None) -> int:
    db = SessionLocal()
    try:
        insumo = Insumo(
            categoria_id=categoria_id,
            nombre=nombre or f"Insumo {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal("0"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal(costo),
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


def _make_producto(
    tipo_producto_id: int,
    fijos: str = "0",
    fabrica: bool = True,
    nombre: str | None = None,
) -> int:
    db = SessionLocal()
    try:
        producto = Producto(
            tipo_producto_id=tipo_producto_id,
            nombre=nombre or f"Producto {_unique()}",
            requiere_fabricacion=fabrica,
            costos_operativos_fijos=Decimal(fijos),
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
    desperdicio: str = "0",
    detalle: str | None = None,
) -> int:
    db = SessionLocal()
    try:
        linea = BomInsumo(
            producto_id=producto_id,
            insumo_id=insumo_id,
            variante_id=variante_id,
            cantidad_requerida=Decimal(cantidad),
            porcentaje_desperdicio=Decimal(desperdicio),
            detalle=detalle,
        )
        db.add(linea)
        db.commit()
        db.refresh(linea)
        return linea.id
    finally:
        db.close()


def _make_linea_producto(combo_id: int, incluido_id: int, cantidad: str = "1") -> int:
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
        db.query(VarianteProducto).filter(VarianteProducto.producto_id == producto_id).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_tipo(tipo_id: int) -> None:
    db = SessionLocal()
    try:
        producto_ids = db.query(Producto.id).filter(Producto.tipo_producto_id == tipo_id)
        db.query(BomInsumo).filter(BomInsumo.producto_id.in_(producto_ids)).delete(
            synchronize_session=False
        )
        db.query(BomProducto).filter(
            or_(
                BomProducto.combo_id.in_(producto_ids),
                BomProducto.producto_incluido_id.in_(producto_ids),
            )
        ).delete(synchronize_session=False)
        db.query(VarianteProducto).filter(VarianteProducto.producto_id.in_(producto_ids)).delete(
            synchronize_session=False
        )
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


def _setup_insumo_base(costo: str = "0") -> tuple[int, int, int]:
    """Returns (categoria_id, insumo_id, tipo_id) with a fresh insumo + tipo."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo=costo)
    tipo_id = _make_tipo()
    return categoria_id, insumo_id, tipo_id


def _teardown_insumo_base(categoria_id: int, insumo_id: int, tipo_id: int) -> None:
    _cleanup_insumo(insumo_id)
    _cleanup_categoria(categoria_id)
    _cleanup_tipo(tipo_id)


def _count_bom_insumo_queries_for(producto_id: int):
    """Return (holder, listener): holder["count"] grows while listener is attached.

    Counts explicit BOM_Productos traversal SELECTs for producto_id. Counting
    BOM_Insumos would double-count because Producto.bom_insumos uses
    lazy="selectin" (fires an extra IN query on db.get(Producto, ...)); the
    Producto model has no eager BOM_Productos relationship, so BOM_Productos
    queries come only from the engine's explicit select.
    """
    holder = {"count": 0}

    def _before_execute(conn, cursor, statement, parameters, context, executemany):
        if '"BOM_Productos"' in statement:
            values = parameters.values() if isinstance(parameters, dict) else (parameters or ())
            if producto_id in values:
                holder["count"] += 1

    return holder, _before_execute


# ---------------------------------------------------------------------------
# Service: calcular_costo_produccion (spec scenarios)
# ---------------------------------------------------------------------------


def test_costo_single_level_insumos():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id, fijos="10")
    _make_linea_insumo(producto_id, insumo_id, cantidad="2")
    try:
        db = SessionLocal()
        try:
            total = calcular_costo_produccion(db, producto_id)
            assert total == Decimal("20.0000")  # 2 x 5 + 10
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_desperdicio_en_contribucion_insumo():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="10", desperdicio="20")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("60.0000")  # 10 x 1.2 x 5
            assert len(lineas) == 1
            linea = lineas[0]
            assert linea.tipo == "insumo"
            assert linea.cantidad == Decimal("12")  # effective qty incl. waste
            assert linea.costo_unitario == Decimal("5")
            assert linea.costo_total == Decimal("60")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_multinivel_combo():
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id, fijos="10")
    b_id = _make_producto(tipo_id)
    _make_linea_producto(a_id, b_id, cantidad="2")
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="30")
    _make_linea_insumo(b_id, insumo_id, cantidad="1")
    try:
        db = SessionLocal()
        try:
            total = calcular_costo_produccion(db, a_id)
            assert total == Decimal("70.0000")  # 2 x 30 + 10
        finally:
            db.close()
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


def test_costo_lineas_repetidas_suman():
    # Blusa case: 3 additive rows of the same insumo SUM instead of
    # overriding — (1 + 2 + 3) x 5 = 30.
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="1")
    _make_linea_insumo(producto_id, insumo_id, cantidad="2")
    _make_linea_insumo(producto_id, insumo_id, cantidad="3")
    try:
        db = SessionLocal()
        try:
            total = calcular_costo_produccion(db, producto_id)
            assert total == Decimal("30.0000")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_detalle_no_cambia_total():
    # detalle is a cost-neutral piece label: labeled lines cost exactly the
    # same as unlabeled ones — (1 + 2) x 5 = 15 either way.
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="1", detalle="torso")
    _make_linea_insumo(producto_id, insumo_id, cantidad="2", detalle="manga izquierda")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("15.0000")
            assert sum((l.costo_total for l in lineas), Decimal("0")) == Decimal("15.0000")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_variante_repetidas_suman_sin_base():
    # Variant override is cross-level only: with ANY variant row for the
    # insumo, ALL NULL base rows are ignored, while the variant rows
    # themselves still SUM — (2 + 3) x 5 = 25, base 1 x 5 NOT added.
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    _make_linea_insumo(producto_id, insumo_id, variante_id=None, cantidad="1")
    _make_linea_insumo(producto_id, insumo_id, variante_id=variante_id, cantidad="2")
    _make_linea_insumo(producto_id, insumo_id, variante_id=variante_id, cantidad="3")
    try:
        db = SessionLocal()
        try:
            assert calcular_costo_produccion(db, producto_id, variante_id) == Decimal("25.0000")
            assert calcular_costo_produccion(db, producto_id) == Decimal("5.0000")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_variante_override_no_se_suma_base():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    _make_linea_insumo(producto_id, insumo_id, variante_id=None, cantidad="1")
    _make_linea_insumo(producto_id, insumo_id, variante_id=variante_id, cantidad="2")
    try:
        db = SessionLocal()
        try:
            total = calcular_costo_produccion(db, producto_id, variante_id)
            assert total == Decimal("10.0000")  # 2 x 5, base 1 x 5 NOT summed
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_variante_sin_reglas_cae_a_base():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    _make_linea_insumo(producto_id, insumo_id, variante_id=None, cantidad="1")
    try:
        db = SessionLocal()
        try:
            total = calcular_costo_produccion(db, producto_id, variante_id)
            assert total == Decimal("5.0000")  # NULL base rule applies
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_no_fabricado_ignora_bom():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id, fijos="15", fabrica=False)
    _make_linea_insumo(producto_id, insumo_id, cantidad="1")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("15.0000")  # BOM traversal skipped
            assert len(lineas) == 1
            assert lineas[0].tipo == "operativos_fijos"
            assert lineas[0].costo_total == Decimal("15")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_fabricado_sin_bom_solo_fijos():
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id, fijos="15")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("15.0000")
            assert len(lineas) == 1
            assert lineas[0].tipo == "operativos_fijos"
            assert lineas[0].costo_unitario == Decimal("15")
            assert lineas[0].costo_total == Decimal("15")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_costo_ciclo_directo_409():
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id)
    b_id = _make_producto(tipo_id)
    _make_linea_producto(a_id, b_id, cantidad="1")
    _make_linea_producto(b_id, a_id, cantidad="1")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(BomCycleDetectedError) as excinfo:
                calcular_costo_produccion(db, a_id)
            assert excinfo.value.status_code == 409
        finally:
            db.close()
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_tipo(tipo_id)


def test_costo_precision_sin_redondeo():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="10", desperdicio="33.3333")
    try:
        db = SessionLocal()
        try:
            total = calcular_costo_produccion(db, producto_id)
            # 10 x (1 + 0.333333) x 5 = 66.66665 — engine must NOT round to 66.6667
            assert total == Decimal("66.66665")
            assert total != Decimal("66.6667")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_costo_diamante_subproducto_compartido_una_vez():
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id)
    b_id = _make_producto(tipo_id)
    c_id = _make_producto(tipo_id)
    d_id = _make_producto(tipo_id)
    _make_linea_producto(a_id, b_id, cantidad="1")
    _make_linea_producto(a_id, c_id, cantidad="1")
    _make_linea_producto(b_id, d_id, cantidad="1")
    _make_linea_producto(c_id, d_id, cantidad="1")
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="30")
    _make_linea_insumo(d_id, insumo_id, cantidad="1")
    try:
        db = SessionLocal()
        try:
            holder, listener = _count_bom_insumo_queries_for(d_id)
            event.listen(engine, "before_cursor_execute", listener)
            try:
                total = calcular_costo_produccion(db, a_id)
            finally:
                event.remove(engine, "before_cursor_execute", listener)
            assert total == Decimal("60.0000")  # B(30) + C(30)
            assert holder["count"] == 1  # D's subtree traversed exactly once (memo hit)
        finally:
            db.close()
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_producto(c_id)
        _cleanup_producto(d_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# Service: desglosar_costo_produccion (1-level breakdown shape)
# ---------------------------------------------------------------------------


def test_desglose_single_level_insumo_line():
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id, fijos="10")
    nombre_insumo = f"Insumo {_unique()}"
    # replace generated insumo name with a known one via direct update
    db = SessionLocal()
    try:
        insumo = db.get(Insumo, insumo_id)
        insumo.nombre = nombre_insumo
        db.commit()
    finally:
        db.close()
    _make_linea_insumo(producto_id, insumo_id, cantidad="2")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("20.0000")
            assert len(lineas) == 1
            linea = lineas[0]
            assert linea.tipo == "insumo"
            assert linea.id == insumo_id
            assert linea.nombre == nombre_insumo
            assert linea.cantidad == Decimal("2")
            assert linea.costo_unitario == Decimal("5")
            assert linea.costo_total == Decimal("10")
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


def test_desglose_combo_line_lleva_costo_recursivo():
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id)
    b_id = _make_producto(tipo_id, nombre=f"Sub {_unique()}")
    _make_linea_producto(a_id, b_id, cantidad="2")
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="30")
    _make_linea_insumo(b_id, insumo_id, cantidad="1")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, a_id)
            assert total == Decimal("60.0000")
            assert len(lineas) == 1
            linea = lineas[0]
            assert linea.tipo == "producto"
            assert linea.id == b_id
            assert linea.cantidad == Decimal("2")
            assert linea.costo_unitario == Decimal("30")  # full recursive child cost
            assert linea.costo_total == Decimal("60")
        finally:
            db.close()
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# Endpoint: GET /productos/{id}/costo
# ---------------------------------------------------------------------------


def test_get_costo_returns_total_y_desglose(client, admin_token):
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id, fijos="10")
    b_id = _make_producto(tipo_id)
    _make_linea_producto(a_id, b_id, cantidad="2")
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="30")
    _make_linea_insumo(b_id, insumo_id, cantidad="1")
    try:
        resp = client.get(f"{BASE}/{a_id}/costo", headers=_auth(admin_token))
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(str(body["total"])) == Decimal("70.0000")  # 2 x 30 + 10
        assert len(body["lineas"]) == 1
        linea = body["lineas"][0]
        assert linea["tipo"] == "producto"
        assert linea["id"] == b_id
        assert Decimal(str(linea["costo_unitario"])) == Decimal("30")
        assert Decimal(str(linea["costo_total"])) == Decimal("60")
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


def test_get_costo_missing_returns_404(client, admin_token):
    resp = client.get(f"{BASE}/99999999/costo", headers=_auth(admin_token))
    assert resp.status_code == 404


def test_get_costo_ciclo_returns_409(client, admin_token):
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id)
    b_id = _make_producto(tipo_id)
    _make_linea_producto(a_id, b_id, cantidad="1")
    _make_linea_producto(b_id, a_id, cantidad="1")
    try:
        resp = client.get(f"{BASE}/{a_id}/costo", headers=_auth(admin_token))
        assert resp.status_code == 409
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_tipo(tipo_id)


def test_get_costo_consulta_allowed(client, consulta_token):
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id, fijos="15")
    try:
        resp = client.get(f"{BASE}/{producto_id}/costo", headers=_auth(consulta_token))
        assert resp.status_code == 200
        assert Decimal(str(resp.json()["total"])) == Decimal("15.0000")
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_get_costo_requires_auth(client):
    resp = client.get(f"{BASE}/1/costo")
    assert resp.status_code == 401


def test_get_costo_variante_query_param_override(client, admin_token):
    categoria_id, insumo_id, tipo_id = _setup_insumo_base(costo="5")
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    _make_linea_insumo(producto_id, insumo_id, variante_id=None, cantidad="1")
    _make_linea_insumo(producto_id, insumo_id, variante_id=variante_id, cantidad="2")
    try:
        base = client.get(f"{BASE}/{producto_id}/costo", headers=_auth(admin_token))
        assert base.status_code == 200
        assert Decimal(str(base.json()["total"])) == Decimal("5.0000")
    finally:
        _cleanup_producto(producto_id)
        _teardown_insumo_base(categoria_id, insumo_id, tipo_id)


# ---------------------------------------------------------------------------
# Standard times -> automatic labor/energy (BOM tiempos alimentan el costo)
# ---------------------------------------------------------------------------


def _set_tiempos(producto_id: int, corte=None, costura=None, acabados=None, calidad=None) -> None:
    db = SessionLocal()
    try:
        p = db.get(Producto, producto_id)
        p.tiempo_corte_min = corte
        p.tiempo_costura_min = costura
        p.tiempo_acabados_min = acabados
        p.tiempo_calidad_min = calidad
        db.commit()
    finally:
        db.close()


def _set_manual(producto_id: int, mano=None, cif=None) -> None:
    db = SessionLocal()
    try:
        p = db.get(Producto, producto_id)
        p.mano_obra = Decimal(mano) if mano is not None else None
        p.cif_energia = Decimal(cif) if cif is not None else None
        db.commit()
    finally:
        db.close()


def _set_tasas(mano: str, energia: str):
    """Set singleton tasas in the TEST db; returns the previous (mano, energia)."""
    from app.models.maestros import ParametrosCosteo

    db = SessionLocal()
    try:
        row = db.get(ParametrosCosteo, 1)
        if row is None:
            row = ParametrosCosteo(id=1)
            db.add(row)
            db.flush()
        previas = (row.costo_minuto_costura, row.costo_minuto_energia)
        row.costo_minuto_costura = Decimal(mano)
        row.costo_minuto_energia = Decimal(energia)
        db.commit()
        return previas
    finally:
        db.close()


def _restore_tasas(previas) -> None:
    from app.models.maestros import ParametrosCosteo

    db = SessionLocal()
    try:
        row = db.get(ParametrosCosteo, 1)
        row.costo_minuto_costura, row.costo_minuto_energia = previas
        db.commit()
    finally:
        db.close()


def test_costo_tiempos_estandar_automatico():
    """Tiempos 60/120/10/10 -> mano = 200 x tasa_mano, energia = 120 x tasa_energia."""
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _set_tiempos(producto_id, corte=60, costura=120, acabados=10, calidad=10)
    previas = _set_tasas("100", "12.33")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("21479.60")  # 200x100 + 120x12.33
            tipos = {l.tipo for l in lineas}
            assert "mano_obra" in tipos
            assert "cif_energia" in tipos
            mano = next(l for l in lineas if l.tipo == "mano_obra")
            assert mano.cantidad == Decimal(200)
            assert mano.costo_unitario == Decimal("100.0000")
            assert mano.costo_total == Decimal("20000.0000")
            energia = next(l for l in lineas if l.tipo == "cif_energia")
            assert energia.cantidad == Decimal(120)
            assert energia.costo_unitario == Decimal("12.3300")
            assert energia.costo_total == Decimal("1479.6000")
        finally:
            db.close()
    finally:
        _restore_tasas(previas)
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_costo_manual_sin_tiempos():
    """Sin tiempos -> se suman mano_obra/cif_energia guardados (fallback)."""
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id, fijos="100")
    _set_manual(producto_id, mano="5000", cif="2000")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("7100.0000")
            tipos = {l.tipo for l in lineas}
            assert "mano_obra" in tipos
            assert "cif_energia" in tipos
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_costo_tiempos_ganan_a_manual():
    """Con tiempos, el automatico manda (el manual guardado no se suma dos veces)."""
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _set_tiempos(producto_id, corte=10, costura=20, acabados=0, calidad=0)
    _set_manual(producto_id, mano="9999", cif="9999")
    previas = _set_tasas("100", "10")
    try:
        db = SessionLocal()
        try:
            total = calcular_costo_produccion(db, producto_id)
            assert total == Decimal("3200.0000")  # 30x100 + 20x10, manual ignorado
        finally:
            db.close()
    finally:
        _restore_tasas(previas)
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)


def test_costo_sin_tiempos_ni_manual_no_agrega_lineas():
    """Sin tiempos y sin manual -> 0 y sin lineas nuevas (forma vieja intacta)."""
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id, fijos="15")
    try:
        db = SessionLocal()
        try:
            total, lineas = desglosar_costo_produccion(db, producto_id)
            assert total == Decimal("15.0000")
            assert {l.tipo for l in lineas} == {"operativos_fijos"}
        finally:
            db.close()
    finally:
        _cleanup_producto(producto_id)
        _cleanup_tipo(tipo_id)
