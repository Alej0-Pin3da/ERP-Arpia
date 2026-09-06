"""Contract tests for migrate.backfill_precios_costos (hidratacion-datos-faltantes).

Pure plan_* tests need no DB. DB tests use 'Migratest' rows on the shared
test database (module session, exact-name cleanup, never catalog rows):
- dry-run writes nothing; apply hydrates + stamps provenance; re-apply diffs zero
- Celeno 75000 lock; non-zero pipeline values preserved; Compras untouched
"""
from decimal import Decimal

import pytest

from app.db.session import SessionLocal
from app.models import CompraInsumo, Insumo, Producto, ProveedorMaestro, TipoProducto
from migrate.backfill_precios_costos import (
    CELENO_PRECIO,
    CostUpdate,
    PriceUpdate,
    SupplierPlan,
    aplicar_costos,
    aplicar_precios,
    aplicar_proveedores,
    plan_costos,
    plan_precios,
    plan_proveedores,
)
from migrate.report import Report

P = "Migratest"
P1, P2 = f"{P} Precio Uno", f"{P} Precio Dos"
I1, I2 = f"{P} Costo Uno", f"{P} Costo Dos"


def _csv(producto, precio, desc="", fecha="13/12/2025"):
    return {"Producto": producto, "Precio Venta": precio, "Columna 2": desc, "Fecha": fecha}


# --- pure planners (no DB) --- #

def test_csv_wins_divergence_warns():
    rep = Report(fase="T", modo="dry-run")
    planes = plan_precios([_csv("SET AELO", "$80.000")],
                          {"Set Aelo": [("VENTAS!G7", Decimal("82500.0000"))]}, rep)
    assert [(p.nombre, p.precio) for p in planes] == [("Set Aelo", Decimal("80000.0000"))]
    assert any("csv wins" in e.mensaje for e in rep.entradas if e.nivel == "WARN")


def test_discount_error_dateless_cells_warn_and_skip():
    rep = Report(fase="T", modo="dry-run")
    rows = [_csv("SET AELO", "$82.500", desc="DESC 25%"),
            _csv("TOTEBAG", "#VALUE!"),
            {"Producto": "TOTEBAG", "Precio Venta": "$45.000", "Columna 2": "", "Fecha": ""}]
    assert plan_precios(rows, {}, rep) == []
    assert sum(1 for e in rep.entradas if e.nivel == "WARN") == 3


def test_cost_first_wins_and_supplier_normalization():
    rep = Report(fase="T", modo="dry-run")
    costos = plan_costos([("S", 3, "Tela X", 4.5), ("S", 4, "Tela X", 9.0),
                          ("S", 5, "Horas trabajo", None)], [], rep)
    assert [(c.nombre, c.costo) for c in costos] == [("Tela X", Decimal("4.5000"))]
    assert sum(1 for e in rep.entradas if e.nivel == "WARN") == 2
    rep2 = Report(fase="T", modo="dry-run")
    plan = plan_proveedores([("H", 3, "Kilotelas"), ("H", 4, "kilotelas "),
                             ("H", 5, "-"), ("H", 6, "Provedor")], rep2)
    assert plan.nombres == ["Kilotelas"]
    assert sum(1 for e in rep2.entradas if e.nivel == "WARN") == 2


# --- DB-backed (module session, Migratest rows only) --- #

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True, scope="module")
def _cleanup_after_module():
    yield
    db = SessionLocal()
    try:
        db.query(Insumo).filter(Insumo.nombre.in_([I1, I2])).delete(synchronize_session=False)
        db.query(Producto).filter(Producto.nombre.in_([P1, P2])).delete(synchronize_session=False)
        db.query(ProveedorMaestro).filter(ProveedorMaestro.nombre.like(f"{P}%")).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _seed(db):
    from migrate.catalog import bootstrap_catalogo, upsert_insumo, upsert_producto
    bootstrap_catalogo(db)
    upsert_producto(db, P1, "Accesorio")
    upsert_producto(db, P2, "Accesorio")
    upsert_insumo(db, I1, categoria_nombre="Telas")
    upsert_insumo(db, I2, categoria_nombre="Herrajes")
    db.query(Producto).filter(Producto.nombre.in_([P1, P2])).update(
        {"precio_venta_sugerido": Decimal("0"), "origen_precio": None},
        synchronize_session=False)
    db.query(Insumo).filter(Insumo.nombre.in_([I1, I2])).update(
        {"stock_actual": Decimal("5"), "costo_promedio_actual": Decimal("0"),
         "origen_costo": None}, synchronize_session=False)
    db.commit()


def _fixture_plans():
    rep = Report(fase="T", modo="dry-run")
    assert plan_precios([_csv("TOTEBAG", "$45.000")], {}, rep)[0].precio == Decimal("45000")
    return ([PriceUpdate(nombre=P1, precio=Decimal("45000"), fuente="test")],
            [CostUpdate(clave=I1.casefold(), nombre=I1, costo=Decimal("23"),
                        fuente="test")],
            SupplierPlan(nombres=[f"{P} Prov A", f"{P} Prov A"]))


def test_dry_run_apply_idempotent_no_compras_touch(db):
    _seed(db)
    pp, pc, ps = _fixture_plans()
    compras_antes = db.query(CompraInsumo).count()
    rep = Report(fase="T", modo="dry-run")
    aplicar_precios(db, pp, modo="dry-run", report=rep)
    aplicar_costos(db, pc, modo="dry-run", report=rep)
    aplicar_proveedores(db, ps, modo="dry-run", report=rep)
    db.rollback()
    assert db.query(Producto).filter_by(nombre=P1).one().precio_venta_sugerido == 0
    assert db.query(ProveedorMaestro).filter_by(nombre=f"{P} Prov A").one_or_none() is None
    rep2 = Report(fase="T", modo="apply")
    assert aplicar_precios(db, pp, modo="apply", report=rep2)["updated"] == 1
    assert aplicar_costos(db, pc, modo="apply", report=rep2)["updated"] == 1
    assert aplicar_proveedores(db, ps, modo="apply", report=rep2)["updated"] == 1
    db.commit()
    p1 = db.query(Producto).filter_by(nombre=P1).one()
    assert (p1.precio_venta_sugerido, p1.origen_precio) == (Decimal("45000"), "backfill")
    i1 = db.query(Insumo).filter_by(nombre=I1).one()
    assert (i1.costo_promedio_actual, i1.origen_costo) == (Decimal("23"), "backfill")
    assert db.query(CompraInsumo).count() == compras_antes  # no WAC contamination
    assert all(c.proveedor_id is None or db.get(ProveedorMaestro, c.proveedor_id)
               for c in db.query(CompraInsumo).all())  # NULL-safe FK
    rep3 = Report(fase="T", modo="apply")
    assert aplicar_precios(db, pp, modo="apply", report=rep3)["updated"] == 0
    assert aplicar_costos(db, pc, modo="apply", report=rep3)["updated"] == 0
    assert aplicar_proveedores(db, ps, modo="apply", report=rep3)["updated"] == 0
    db.rollback()


def test_celeno_lock_and_pipeline_values_preserved(db):
    _seed(db)
    db.query(Producto).filter_by(nombre=P2).update(
        {"precio_venta_sugerido": CELENO_PRECIO}, synchronize_session=False)
    db.commit()
    rep = Report(fase="T", modo="apply")
    assert CELENO_PRECIO == Decimal("75000")
    res = aplicar_precios(db, [PriceUpdate(nombre=P2, precio=Decimal("65000"),
                                           fuente="forged")], modo="apply", report=rep)
    db.rollback()
    assert res["updated"] == 0
    assert db.query(Producto).filter_by(nombre=P2).one().precio_venta_sugerido == CELENO_PRECIO
    assert any(e.nivel == "WARN" for e in rep.entradas)
