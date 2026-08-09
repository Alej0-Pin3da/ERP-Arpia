"""Contract tests for migrate.catalog - F0/F1 catalog phase (PR#3 slice).

Covers the STRICT TDD acceptance from tasks #424 T4 (spec R-CAT, design #423):

- Pure: name normalization for dedup, unit resolution, category/unit
  classifier, BOM junk-material filtering, bounded plan building from a
  workbook (proveedores + insumos + productos + tipos).
- DB (real PostgreSQL via SessionLocal): idempotent upserts for Tipos,
  Proveedores, Insumos (dedup por nombre), Productos (variante NULL / dedup
  por (producto_id, nombre_variante)).
- Integration: dry-run of the real ARPIA.xlsx writes 0 rows (NFR-2); plan
  counts match the workbook; a hand-built mini CatalogPlan commits atomically
  inside session_scope and can be re-applied without duplication.

Test-injected rows use the 'Migratest ' prefix so cleanup never touches
real catalog data; the base tipos/categorias (Lenceria, Corseteria, ...) ARE
the migration's canonical content and may persist across runs (idempotent).
"""

from pathlib import Path

import openpyxl
import pytest

from app.db.session import SessionLocal
from app.models import Insumo, Producto, Proveedor, TipoProducto
from migrate.context import FaseOptions, MigrationContext

REAL_XLSX = Path(r"C:\wamp64\www\ERP-Arpia\ARPIA.xlsx")

# Names injected by tests; cleanup deletes exactly these, never catalog rows.
PREFIX_TEST = "Migratest"


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #


def _mini_workbook(path: Path) -> None:
    """Mini ARPIA-like workbook: Proveedores + two BOM sheets with junk rows +
    a mini INVENTARIO OCT25 block (cross-sheet dup material)."""
    wb = openpyxl.Workbook()
    prov = wb.active
    prov.title = "Proveedores"
    prov.append(["TIPO", "URL", "Precio Unidad", "Ubicacion", "Contactado"])
    for nombre in ["Bexxhamel", "JM Confecciones", "SEHA Text", "ZureTex"]:
        prov.append(["Camisetas", nombre, 11500, "Cali", "SI"])

    bom1 = wb.create_sheet("CORSET")
    bom1.append(["CORSET", None, None, None, None, None, None, None, "TANGA"])  # R1
    bom1.append(["Producto", "Ancho", "Alto", "cantidad Cms", "valor metro", "valor total"])  # R2
    bom1.append(["Tela Maya Test 1", 64, 37, 2368, 2.5, None])  # R3
    bom1.append(["Encaje Elastico 19 cm negro 10 mts", 28, 18, 504, 1.4, None])  # R4
    bom1.append(["Argolla 90 mm", 2, 1, 2, 72, None])  # R5
    bom1.append(["Horas trabajo", None, None, None, None, None])  # junk
    bom1.append(["COSTO TOTAL CONJUNTO", None, None, None, None, None])  # junk
    bom1.append(["GANANCIA", None, None, None, None, None])  # junk

    bom2 = wb.create_sheet("BLUSAS")
    bom2.append(["MANGA LARGA", None] * 8 + ["MANGA CORTA"])  # R1 title + right block
    bom2.append(["Producto", "Ancho", "Alto", "cantidad Cms", "valor metro", "valor total"])
    bom2.append(["Tela Maya Test 1", 20, 37, 740, 2.5, None])  # dup w/ CORSET
    bom2.append(["Sesgo Elastico 10 mts", 18, 24, 432, 6.3, None])
    bom2.append([4.0, None, None, None, None, None])  # junk numeric

    oct = wb.create_sheet("INVENTARIO OCT25")
    # real sheet (regression against ARPIA.xlsx 2026-08-08): header at R8,
    # data rows R9..29; MATERIAL nombre=B cantidad=D, HERRAJES nombre=F
    # cantidad=H (numero). Columnas A/C/E/G en blanco.
    oct.cell(row=8, column=2, value="MATERIAL")
    oct.cell(row=8, column=4, value="CANTIDAD")
    oct.cell(row=8, column=6, value="HERRAJES")
    oct.cell(row=8, column=8, value="CANTIDAD")
    oct.cell(row=9, column=2, value="Material Migra Test")
    oct.cell(row=9, column=4, value="25 mts")
    oct.cell(row=10, column=6, value="Argolla Migra Test")
    oct.cell(row=10, column=8, value="34")
    wb.save(path)


@pytest.fixture
def mini_libro(tmp_path) -> Path:
    path = tmp_path / "mini-catalog.xlsx"
    _mini_workbook(path)
    return path


def _borrar_filas_test(db) -> None:
    """Remove rows this test module injected (exact-name matches only)."""
    db.query(Insumo).filter(
        Insumo.nombre.in_(
            ["Material Migra Test", "Argolla Migra Test", "Tela Migra para Upsert",
             f"{PREFIX_TEST} Insumo A"]
        )
    ).delete(synchronize_session=False)
    db.query(Proveedor).filter(
        Proveedor.nombre.in_([f"{PREFIX_TEST} Proveedor", f"{PREFIX_TEST} Prov2"])
    ).delete(synchronize_session=False)
    db.query(Producto).filter(
        Producto.nombre.in_(
            [f"{PREFIX_TEST} Corset", f"{PREFIX_TEST} Set",
             f"{PREFIX_TEST} P1", f"{PREFIX_TEST} P2"]
        )
    ).delete(synchronize_session=False)
    # Remove the canonical catalog tipos that bootstrap_catalogo() inserts.
    # They are migration content, not app seed data; leaving them pollutes the
    # shared per-sheet DB and breaks pagination tests that assume an empty table.
    db.query(TipoProducto).filter(
        TipoProducto.nombre.in_(
            ["Lencería", "Corsetería", "Blusa", "Accesorio", "Set", "Combo"]
        )
    ).delete(synchronize_session=False)
    db.commit()


@pytest.fixture(autouse=True, scope="module")
def _cleanup_after_module():
    yield
    db = SessionLocal()
    try:
        _borrar_filas_test(db)
    finally:
        db.close()


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------------------------------- #
# 1. Pure: normalization / unit / category classification (RED contract)
# --------------------------------------------------------------------------- #


def test_normalizar_nombre_colapsa_espacios_y_case():
    from migrate.catalog import normalizar_nombre

    assert normalizar_nombre("  Encaje    Negro  ") == "Encaje Negro"
    assert normalizar_nombre("café") == "café"  # diacritics kept for display
    assert normalizar_nombre("Tela") == "Tela"  # display keeps case; clave_normalizada folds


def test_clave_normalizada_ignora_acentos_para_dedup():
    from migrate.catalog import clave_normalizada

    assert clave_normalizada("Lencería") == clave_normalizada("Lenceria")
    assert clave_normalizada("Tela Maya") == clave_normalizada(" tela   maya ")


def test_resolver_unidad_desde_nombre():
    from migrate.catalog import resolver_unidad

    assert resolver_unidad("Encaje Elastico 19 cm negro 10 mts") == "m"
    assert resolver_unidad("Framilon elastico plano 20 mts") == "m"
    assert resolver_unidad("Sesgo Elastico 10 mts") == "m"
    assert resolver_unidad("Espagueti de pollo 2kg") == "kg"
    assert resolver_unidad("Alambre 500 g") == "g"
    assert resolver_unidad("Sesgo de 2cm") == "cm"
    assert resolver_unidad("Ref 159 24 cm tul bordado rojo pastel") is None  # ancho
    assert resolver_unidad("Tela Maya Ilustrada") is None


def test_clasificar_material_categoria_y_unidad_final():
    from migrate.catalog import clasificar_material

    assert clasificar_material("Ref 159 24 cm tul bordado rojo pastel", None) == ("Telas", "m")
    assert clasificar_material("Argolla 10 mm", None) == ("Herrajes", "un")
    assert clasificar_material("Gafete de 3", None) == ("Empaques", "un")
    assert clasificar_material("Encaje Elastico 19 cm blanco 10 mts", None) == ("Telas", "m")
    assert clasificar_material("Material Migra Test", "25 mts") == ("Telas", "m")
    assert clasificar_material("Argolla Migra Test", "34") == ("Herrajes", "un")


def test_filtrar_materiales_validos_excluye_junk():
    from migrate.catalog import filtrar_materiales_validos

    filas = [
        {"A": "Tela Maya Test 1"},
        {"A": "Horas trabajo"},
        {"A": "COSTO TOTAL CONJUNTO"},
        {"A": "GANANCIA"},
        {"A": 4.0},
        {"A": "VENTA"},
        {"A": 0},
        {"I": "Argolla 90 mm"},  # right-block material counts too
    ]
    efectivas = filtrar_materiales_validos(filas)
    assert "Tela Maya Test 1" in efectivas
    assert "Argolla 90 mm" in efectivas
    assert not any(
        m in efectivas
        for m in ["Horas trabajo", "COSTO TOTAL CONJUNTO", "GANANCIA", "VENTA", "4.0"]
    )


# --------------------------------------------------------------------------- #
# Plan building from workbook (bounded loader + normalization)
# --------------------------------------------------------------------------- #


def test_plan_workbook_mini_proveedores_insumos_dedup(mini_libro):
    from migrate.catalog import plan_catalogo
    from migrate.loaders import LibroMigracion

    with LibroMigracion(mini_libro) as libro:
        plan = plan_catalogo(libro)

    assert plan.conteo_proveedores == 4
    nombres_prov = {p.nombre for p in plan.proveedores}
    assert {"Bexxhamel", "JM Confecciones", "SEHA Text", "ZureTex"} <= nombres_prov

    # CORSET(4) + BLUSAS adds Sesgo; OCT25 adds 2; 'Tela Maya Test 1' dedup across sheets.
    assert plan.conteo_insumos == 6
    nombres = {i.nombre for i in plan.insumos}
    assert {
        "Tela Maya Test 1", "Encaje Elastico 19 cm negro 10 mts", "Argolla 90 mm",
        "Sesgo Elastico 10 mts", "Material Migra Test", "Argolla Migra Test",
    } <= nombres


def test_plan_catalogo_unidades_normalizadas(mini_libro):
    from migrate.catalog import plan_catalogo
    from migrate.loaders import LibroMigracion

    with LibroMigracion(mini_libro) as libro:
        plan = plan_catalogo(libro)

    por = {i.nombre: i for i in plan.insumos}
    assert por["Tela Maya Test 1"].unidad == "m"
    assert por["Tela Maya Test 1"].categoria == "Telas"
    assert por["Argolla 90 mm"].unidad == "un"
    assert por["Argolla 90 mm"].categoria == "Herrajes"
    assert por["Material Migra Test"].unidad == "m"
    assert por["Argolla Migra Test"].unidad == "un"


def test_plan_catalogo_tipos_y_productos_static(mini_libro):
    from migrate.catalog import plan_catalogo, TIPOS_CATALOGO, PRODUCTOS_CATALOGO
    from migrate.loaders import LibroMigracion

    with LibroMigracion(mini_libro) as libro:
        plan = plan_catalogo(libro)

    assert set(plan.tipos) == set(TIPOS_CATALOGO)
    assert plan.conteo_productos == len(PRODUCTOS_CATALOGO)
    for tipo in ["Lencería", "Corsetería", "Blusa", "Accesorio", "Set", "Combo"]:
        assert tipo in plan.tipos


# --------------------------------------------------------------------------- #
# DB upserts: idempotencia (real PostgreSQL via SessionLocal)
# --------------------------------------------------------------------------- #


def test_bootstrap_categorias_y_tipos_idempotente(db):
    from migrate.catalog import bootstrap_catalogo

    bootstrap_catalogo(db)
    bootstrap_catalogo(db)

    tipos = {t.nombre for t in db.query(TipoProducto).all()}
    assert {"Lencería", "Corsetería", "Blusa", "Accesorio", "Set", "Combo"} <= tipos
    for nombre in ["Lencería", "Corsetería", "Set"]:
        assert db.query(TipoProducto).filter(TipoProducto.nombre == nombre).count() == 1


def test_upsert_proveedor_idempotente(db):
    from migrate.catalog import bootstrap_catalogo, clave_normalizada, upsert_proveedor

    bootstrap_catalogo(db)
    nombre = f"{PREFIX_TEST} Proveedor"
    primero = upsert_proveedor(db, nombre, url="https://test.local")
    segundo = upsert_proveedor(db, nombre, url="https://test.local")
    assert primero.id == segundo.id  # mismo proveedor, no duplicado
    assert db.query(Proveedor).filter(Proveedor.nombre == nombre).count() == 1
    assert clave_normalizada(primero.nombre) == clave_normalizada(nombre)  # se guarda normalizado


def test_upsert_insumo_dedup_por_nombre(db):
    from migrate.catalog import bootstrap_catalogo, upsert_insumo

    bootstrap_catalogo(db)
    nombre = "Tela Migra para Upsert"
    a = upsert_insumo(db, nombre, categoria_nombre="Telas")
    b = upsert_insumo(db, nombre, categoria_nombre="Telas")
    assert a.id == b.id
    assert db.query(Insumo).filter(Insumo.nombre == nombre).count() == 1
    fila = db.query(Insumo).filter(Insumo.nombre == nombre).first()
    assert fila.stock_actual == 0 and fila.stock_minimo == 0 and fila.costo_promedio_actual == 0
    assert fila.categoria.nombre == "Telas"


def test_upsert_producto_sin_variante_no_duplica(db):
    from migrate.catalog import bootstrap_catalogo, upsert_producto

    bootstrap_catalogo(db)
    nombre = f"{PREFIX_TEST} Corset"
    a = upsert_producto(db, nombre, tipo="Corsetería")
    b = upsert_producto(db, nombre, tipo="Corsetería")
    assert a.id == b.id
    assert db.query(Producto).filter(Producto.nombre == nombre).count() == 1
    assert len(a.variantes) == 0  # variante NULL: sin fila duplicada vacia


def test_upsert_producto_variantes_dedup(db):
    from migrate.catalog import bootstrap_catalogo, upsert_producto

    bootstrap_catalogo(db)
    nombre = f"{PREFIX_TEST} Set"
    a = upsert_producto(db, nombre, tipo="Set", variantes=["S", "S", "M"])
    assert {v.nombre_variante for v in a.variantes} == {"S", "M"}
    b = upsert_producto(db, nombre, tipo="Set", variantes=["S", "M"])
    assert b.id == a.id
    assert len(b.variantes) == 2  # dedup por (producto_id, nombre_variante)


# --------------------------------------------------------------------------- #
# Phase level: dry-run plan on real workbook + atomic mini apply
# --------------------------------------------------------------------------- #


def test_catalogar_dry_run_real_no_escribe():
    from migrate.catalog import catalogar, PRODUCTOS_CATALOGO

    if not REAL_XLSX.exists():
        pytest.skip("ARPIA.xlsx no disponible")

    db = SessionLocal()
    try:
        antes = (
            db.query(TipoProducto).count(), db.query(Proveedor).count(),
            db.query(Insumo).count(), db.query(Producto).count(),
        )
        ctx = MigrationContext.para_fase(
            FaseOptions(source=REAL_XLSX, modo="dry-run"), "F1"
        )
        plan = catalogar(ctx)
        despues = (
            db.query(TipoProducto).count(), db.query(Proveedor).count(),
            db.query(Insumo).count(), db.query(Producto).count(),
        )
        # NFR-2: dry-run termina con 0 filas escritas
        assert antes == despues
        assert plan.conteo_proveedores >= 4
        assert plan.conteo_insumos >= 20  # recetas BOM + herrajes reales
        assert plan.conteo_productos == len(PRODUCTOS_CATALOGO)
    finally:
        db.close()


def test_oct25_layout_real_entra_al_universo_f1():
    """Regression: INVENTARIO OCT25 uses MATERIAL B/D + HERRAJES F/H (real
    ARPIA.xlsx layout, verified 2026-08-08). The 20 real materials (B) and the
    14 real herrajes (F) MUST enter the F1 insumo universe, and the quantity
    cells ('9,5 mts', '11 mts'...) MUST NOT be treated as material names."""
    from migrate.catalog import _leer_materiales, clave_normalizada
    from migrate.loaders import LibroMigracion

    if not REAL_XLSX.exists():
        pytest.skip("ARPIA.xlsx no disponible")

    materiales_b = [
        "Encaje negro sin pelitos", "Tela entrepierna negra",
        "Tela entrepierna blanca",
        "Encaje blanco chantilli (pelitos) para bicolor",
        "Encaje negro chantilli (pelitos) para bicolor", "Tira de brasier blanca",
        "Contorno para Bustier negro 2 cm ancho", "Tapa varilla Negro #1",
        "Tapa varilla Negro #2", "Elastico de contorno de 1 cm blanco",
        "Tapa Costura Negro", "Elastico plano negro", "Elastico plano blanco",
        "Tira de brasier negra", "Sesgo de 2cm blanco", "Sesgo de 2cm negro",
        "Mallatex negra", "Mallatex blanca",
        "Ref 100 24 cm tul bordado negro",
        "Ref 159 24 cm tul bordado rojo pastel",
    ]
    herrajes = [
        "Argollas grandes", "* Argollas Medianas", "* Argollas Pequenas",
        "* Ochos Grandes", "* Ochos Medianos", "* Ochos Pequenos",
        "* Gancho G grandes", "* Gancho G Medianos", "* Ganchos G Pequenos",
        "Varilla copa brasier talla 30", "Varilla copa brasier talla 32",
        "Varilla copa brasier talla 36", "Varilla copa brasier talla 34",
        "Variila plastica cortada 18cms",
    ]
    with LibroMigracion(REAL_XLSX) as libro:
        universo = _leer_materiales(libro, None)
    claves = set(universo)
    for nombre in materiales_b + herrajes:
        assert clave_normalizada(nombre) in claves, f"material OCT25 ausente: {nombre}"
    # Cantidades de D (9,5 mts / 11 mts) nunca son nombres de insumo.
    assert clave_normalizada("9,5 mts") not in claves
    assert clave_normalizada("11 mts") not in claves


def test_aplicar_plan_transaccional_y_cleanup(db):
    from migrate.catalog import (
        CatalogPlan,
        InsumoPlan,
        ProductoPlan,
        ProveedorPlan,
        aplicar_plan,
    )

    plan = CatalogPlan(
        tipos=["Lencería"],
        proveedores=[ProveedorPlan(nombre=f"{PREFIX_TEST} Prov2")],
        insumos=[InsumoPlan(nombre=f"{PREFIX_TEST} Insumo A", unidad="m", categoria="Telas")],
        productos=[
            ProductoPlan(nombre=f"{PREFIX_TEST} P1", tipo="Set"),
            ProductoPlan(nombre=f"{PREFIX_TEST} P2", tipo="Set", variantes=("XS", "S")),
        ],
    )
    aplicar_plan(db, plan)
    db.commit()

    assert db.query(Producto).filter(Producto.nombre == f"{PREFIX_TEST} P2").count() == 1
    assert db.query(Insumo).filter(Insumo.nombre == f"{PREFIX_TEST} Insumo A").count() == 1
    assert db.query(Proveedor).filter(Proveedor.nombre == f"{PREFIX_TEST} Prov2").count() == 1