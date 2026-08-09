"""Contract tests for migrate.purchases - F2 historical WAC purchases (PR#4).

Covers the STRICT TDD acceptance from tasks #424 T5 (spec EXM-2/3/4/5, D1/D5,
NFR-1/2):

- Pure: quantity normalization to the insumo's canonical unit ('4 mts'->4 m,
  '50 cm'->0.5 m, numeric->as-is), non-inferable values rejected.
- Workbook -> plan: ONLY catalog (BOM) insumos become WAC purchases; non-BOM
  rows (equipo, gastos) are excluded (-> finanzas F6); right-hand price
  sub-tables (J..N / H..L) that duplicate left blocks are never loaded; empty
  células de fecha follow D5 (inherit contiguous same insumo+proveedor,
  otherwise omit + WARN), never now().
- DB (real PostgreSQL): applying the plan registers CompraInsumo rows with the
  REAL excel fecha, updates insumo stock_actual + costo_promedio_actual via
  wac.registrar_compra (WAC formula), is idempotent on re-run (natural key
  insumo+fecha+cantidad+precio), and a rollback leaves cero filas persistidas
  (no internal commit of the service).
- Phase: F2 registered in the runner registry; dry-run on the real workbook
  writes 0 rows (NFR-2) and reports the BOM purchase plan.

Test-injected rows use the 'MigraTest ' prefix so cleanup never touches real
migration data.
"""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from app.db.session import SessionLocal
from app.models import CompraInsumo, Insumo
from migrate.context import FaseOptions, MigrationContext
from migrate.loaders import LibroMigracion

REAL_XLSX = Path(r"C:\wamp64\www\ERP-Arpia\ARPIA.xlsx")
PREFIX_TEST = "Migratest"

DIA = datetime(2026, 2, 17, tzinfo=timezone.utc)
DIA2 = datetime(2026, 3, 3, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #


def _mini_workbook(path: Path) -> None:
    """Mini workbook: a CORSET sheet providing BOM materials (catalog universe)
    + INVERSION VALQUI with the Excel purchase layout (left block A..E, right
    price sub-table J..N starting at R13)."""
    wb = openpyxl.Workbook()
    bom = wb.active
    bom.title = "CORSET"
    bom.append(["CORSET", None, None, None, None, None, None, None, "TANGA"])
    bom.append(["Producto", "Ancho", "Alto", "cantidad Cms", "valor metro", "valor total"])
    bom.append([f"{PREFIX_TEST} Tela", 64, 37, 2368, 2.5, None])  # R3 material BOM
    bom.append([f"{PREFIX_TEST} Argolla", 2, 1, 2, 72, None])
    bom.append([f"{PREFIX_TEST} Encaje", 28, 18, 504, 4.0, None])
    bom.append(["Horas trabajo", None, None, None, None, None])
    bom.append(["COSTO TOTAL CONJUNTO", None, None, None, None, None])

    inv = wb.create_sheet("INVERSION VALQUI")
    inv.cell(row=2, column=1, value="Cantidad")
    inv.cell(row=2, column=2, value="Producto")
    inv.cell(row=2, column=4, value="Costo")
    inv.cell(row=2, column=5, value="Fecha")
    inv.cell(row=2, column=6, value="Provedor")
    # R3: fabric purchase 4 mts @ 200 total -> unit price 50
    inv.cell(row=3, column=1, value="4 mts")
    inv.cell(row=3, column=2, value=f"{PREFIX_TEST} Tela")
    inv.cell(row=3, column=4, value=200)
    inv.cell(row=3, column=5, value=datetime(2026, 2, 17))
    # R4: another BOM purchase with empty fecha (R6 hereda de R3 mismo insumo? no, distinto)
    inv.cell(row=4, column=1, value=12)
    inv.cell(row=4, column=2, value=f"{PREFIX_TEST} Argolla")
    inv.cell(row=4, column=4, value=2400)
    inv.cell(row=4, column=5, value=datetime(2026, 3, 3))
    # R5: EQUIPO row (no BOM) -> excluded
    inv.cell(row=5, column=1, value=1)
    inv.cell(row=5, column=2, value=f"{PREFIX_TEST} Equipo")
    inv.cell(row=5, column=4, value=5000)
    inv.cell(row=5, column=5, value=datetime(2026, 3, 3))
    # R6: BOM compra SIN fecha -> hereda DIA2? no: mismo insumo sin fecha previa -> omitted+WARN
    inv.cell(row=6, column=1, value="5 mts")
    inv.cell(row=6, column=2, value=f"{PREFIX_TEST} Encaje")
    inv.cell(row=6, column=4, value=1200)
    # R7: BOM compra SIN fecha pero mismo insumo (Tela) + mismo proveedor que R3 -> hereda DIA
    inv.cell(row=7, column=1, value="2 mts")
    inv.cell(row=7, column=2, value=f"{PREFIX_TEST} Tela")
    inv.cell(row=7, column=4, value=60)
    inv.cell(row=7, column=6, value=f"{PREFIX_TEST} Prov")
    inv.cell(row=3, column=6, value=f"{PREFIX_TEST} Prov")
    # Derecha: la sub-tabla de precios duplica la compra (400cm x 1cm = 4 mts a M=200)
    inv.cell(row=14, column=10, value=f"{PREFIX_TEST} Tela")  # J
    inv.cell(row=14, column=11, value=400)  # K Largo CMS
    inv.cell(row=14, column=12, value=1)  # L Ancho CMS
    inv.cell(row=14, column=13, value=200)  # M Valor
    wb.save(path)


@pytest.fixture
def mini_libro(tmp_path) -> Path:
    path = tmp_path / "mini-purchases.xlsx"
    _mini_workbook(path)
    return path


def _plan_de(mini_libro):
    from migrate.purchases import plan_compras

    with LibroMigracion(mini_libro) as libro:
        return plan_compras(libro)


def _preparar_catalogo(db) -> dict[str, int]:
    """F1 bootstrap + insumos BOM del mini: insumos y proveedor de prueba."""
    from migrate.catalog import bootstrap_catalogo, upsert_insumo, upsert_proveedor

    bootstrap_catalogo(db)
    db.flush()
    ids = {}
    ids[PREFIX_TEST + " Tela"] = upsert_insumo(
        db, f"{PREFIX_TEST} Tela", categoria_nombre="Telas"
    ).id
    ids[PREFIX_TEST + " Argolla"] = upsert_insumo(
        db, f"{PREFIX_TEST} Argolla", categoria_nombre="Herrajes"
    ).id
    ids[PREFIX_TEST + " Encaje"] = upsert_insumo(
        db, f"{PREFIX_TEST} Encaje", categoria_nombre="Telas"
    ).id
    ids[PREFIX_TEST + " Prov"] = upsert_proveedor(db, f"{PREFIX_TEST} Prov").id
    db.commit()
    return ids


def _borrar_filas_test(db) -> None:
    """Remove rows injected by this test module (exact-name matches only)."""
    from app.models import CompraInsumo, Insumo, Proveedor, TipoProducto

    nombres_insumo = [
        f"{PREFIX_TEST} Tela", f"{PREFIX_TEST} Argolla", f"{PREFIX_TEST} Encaje"
    ]
    insumos = db.query(Insumo).filter(Insumo.nombre.in_(nombres_insumo)).all()
    for insumo in insumos:
        db.query(CompraInsumo).filter(CompraInsumo.insumo_id == insumo.id).delete(
            synchronize_session=False
        )
    db.query(Insumo).filter(Insumo.nombre.in_(nombres_insumo)).delete(
        synchronize_session=False
    )
    db.query(Proveedor).filter(Proveedor.nombre == f"{PREFIX_TEST} Prov").delete(
        synchronize_session=False
    )
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
# 1. Pure: quantity normalization (canonical unit)
# --------------------------------------------------------------------------- #


def test_normalizar_cantidad_compra_metros_y_numerico():
    from migrate.purchases import normalizar_cantidad_compra

    assert normalizar_cantidad_compra("4 mts", "m") == 4
    assert normalizar_cantidad_compra("2,90 mts", "m") == Decimal("2.9")
    assert normalizar_cantidad_compra(12, "un") == 12
    assert normalizar_cantidad_compra(0.5, "m") == 0.5


def test_normalizar_cantidad_compra_cm_a_metros():
    from migrate.purchases import normalizar_cantidad_compra

    assert normalizar_cantidad_compra("50 cm", "m") == 0.5
    assert normalizar_cantidad_compra("100 cm", "m") == 1


def test_normalizar_cantidad_compra_rechaza_no_interpretables():
    from migrate.purchases import normalizar_cantidad_compra

    assert normalizar_cantidad_compra(None, "m") is None
    assert normalizar_cantidad_compra("#DIV/0!", "m") is None
    assert normalizar_cantidad_compra("un metro aprox", "m") is None


# --------------------------------------------------------------------------- #
# 2. Workbook -> plan: BOM filter, right sub-table, fecha policy
# --------------------------------------------------------------------------- #


def test_plan_compras_solo_insumos_bom(mini_libro):
    plan = _plan_de(mini_libro)
    nombres = {c.insumo_nombre for c in plan.compras}
    assert f"{PREFIX_TEST} Tela" in nombres
    assert f"{PREFIX_TEST} Argolla" in nombres
    # R5 es EQUIPO (no esta en el universos BOM): no es compra WAC
    assert not any(c.insumo_nombre == f"{PREFIX_TEST} Equipo" for c in plan.compras)
    # La sub-tabla derecha (R14) no genera compra duplicada
    assert plan.conteo_compras == 3


def test_plan_compras_calcula_precio_unitario(mini_libro):
    plan = _plan_de(mini_libro)
    # First-wins: R3 (4 mts @ 50) y R7 (2 mts @ 30) son dos compras del mismo
    # insumo; la heredada no debe pisar la fila original en el lookup.
    por = {}
    for c in plan.compras:
        por.setdefault(c.insumo_nombre, c)
    assert por[f"{PREFIX_TEST} Tela"].cantidad == Decimal(4)
    assert por[f"{PREFIX_TEST} Tela"].precio_unitario == Decimal(50)
    assert por[f"{PREFIX_TEST} Argolla"].cantidad == 12
    assert por[f"{PREFIX_TEST} Argolla"].precio_unitario == Decimal(200)


def test_plan_compras_fecha_heredada_contigua(mini_libro):
    plan = _plan_de(mini_libro)
    por = {c.insumo_nombre: c for c in plan.compras}
    # R7 hereda la fecha DIA de la compra R3 (mismo insumo Tela + mismo proveedor)
    tela_2m = [c for c in plan.compras if c.insumo_nombre == f"{PREFIX_TEST} Tela"]
    heredada = [c for c in tela_2m if c.fecha_heredada]
    assert len(heredada) == 1
    # (fecha no normalizada -> coerce a aware utc)
    assert heredada[0].fecha == DIA


def test_plan_compras_sin_fecha_ni_heredable_omitida(mini_libro):
    plan = _plan_de(mini_libro)
    # R6 (Encaje sin fecha y sin previo del mismo insumo) no debe entrar
    assert plan.conteo_compras == 3
    assert not any(c.insumo_nombre == f"{PREFIX_TEST} Encaje" for c in plan.compras)
    assert plan.conteos.sin_fecha == 1


# --------------------------------------------------------------------------- #
# 3. DB: aplicar + WAC + idempotencia + rollback
# --------------------------------------------------------------------------- #


def test_aplicar_plan_persiste_fechas_y_wac(db, mini_libro):
    from migrate.purchases import aplicar_compras

    _preparar_catalogo(db)
    plan = _plan_de(mini_libro)
    aplicar_compras(db, plan)
    db.commit()

    insumo_tela = db.query(Insumo).filter(Insumo.nombre == f"{PREFIX_TEST} Tela").one()
    compras = db.query(CompraInsumo).filter(CompraInsumo.insumo_id == insumo_tela.id).all()
    assert len(compras) == 2  # R3 + R7 heredada
    fechas = sorted(c.fecha_compra for c in compras)
    assert fechas[0] == DIA
    assert fechas[1] == DIA  # la heredada persiste la MISMA fecha real (no now())
    # WAC: (4 x 50 + 2 x 30) / 6 = 43.3333... (NUMERIC(15,4) storage)
    assert insumo_tela.stock_actual == 6
    assert insumo_tela.costo_promedio_actual == Decimal("43.3333")

    argolla = db.query(Insumo).filter(Insumo.nombre == f"{PREFIX_TEST} Argolla").one()
    compras_a = db.query(CompraInsumo).filter(CompraInsumo.insumo_id == argolla.id).all()
    assert len(compras_a) == 1
    assert argolla.stock_actual == 12
    assert argolla.costo_promedio_actual == 200


def test_aplicar_es_idempotente(db, mini_libro):
    from migrate.purchases import aplicar_compras

    ids = _preparar_catalogo(db)
    plan = _plan_de(mini_libro)
    aplicar_compras(db, plan)
    db.commit()
    aplicar_compras(db, plan)
    db.commit()

    from app.models import CompraInsumo

    tela = db.get(Insumo, ids[PREFIX_TEST + " Tela"])
    compras = db.query(CompraInsumo).filter(CompraInsumo.insumo_id == tela.id).all()
    assert len(compras) == 2  # sin duplicados tras re-ejecutaron
    assert tela.stock_actual == 6  # WAC no se re-aplica


def test_rollback_no_persiste_nada(db):
    """commit=False del servicio respetado: si el caller hace rollback, 0 filas."""
    from app.models import CompraInsumo
    from app.services.wac import registrar_compra

    ups = _preparar_catalogo(db)
    tela_id = ups[PREFIX_TEST + " Tela"]
    # Aislamiento: tests de plan previos ya insertaron compras de Tela.
    db.query(CompraInsumo).filter(CompraInsumo.insumo_id == tela_id).delete(
        synchronize_session=False
    )
    db.commit()
    registrar_compra(
        db, tela_id, None, 10, 25, fecha_compra=DIA, commit=False
    )
    db.rollback()
    assert db.query(CompraInsumo).filter(CompraInsumo.insumo_id == tela_id).count() == 0


# --------------------------------------------------------------------------- #
# 4. Phase: runner registry + real workbook dry run (NFR-2)
# --------------------------------------------------------------------------- #


def test_f2_registrada_en_runner():
    from migrate import FASE_RUNNERS, FASES, FASES_IMPLEMENTADAS

    assert any(f.id == "F2" for f in FASES)
    assert "F2" in FASE_RUNNERS
    assert "F2" in FASES_IMPLEMENTADAS


def test_cargar_compras_dry_run_real_no_escribe():
    from app.models import CompraInsumo
    from migrate.purchases import cargar_compras

    if not REAL_XLSX.exists():
        pytest.skip("ARPIA.xlsx no disponible")

    db = SessionLocal()
    try:
        antes = db.query(CompraInsumo).count()
        ctx = MigrationContext.para_fase(
            FaseOptions(source=REAL_XLSX, modo="dry-run"), "F2"
        )
        cargar_compras(ctx)
        despues = db.query(CompraInsumo).count()
        assert antes == despues  # NFR-2: 0 filas escritas
        assert not ctx.report.tenga_errores
        assert ctx.report.count("WARN") >= 7  # filas con fecha omitida/otros
    finally:
        db.close()