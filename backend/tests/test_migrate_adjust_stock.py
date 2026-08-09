"""Contract tests for migrate.adjust_stock - ajuste manual de stock inicial (fix2).

Covers STRICT TDD acceptance for the fix2 data-adjustment layer (decision
vinculante del usuario: STOCK INICIAL MANUAL — el pipeline NO se modifica para
interpretar cadenas/cremalleras/tapavarilla/satines; un script de ajuste de
negocio fija stock_actual para los 10 insumos residuales de F5):

- Consumo BOM exacto de las 13 ventas historicas (verificado con la explosion
  real sobre ARPIA.xlsx, 2026-08-09): coincide con el hallazgo residual del
  apply-progress #425 (318 / 288 / 240 / 379 / 2.802 / 3 / 0.0396 / 0.045 /
  0.325 / 30). El mapa CONSUMOS_BOM es la fuente de verdad de la capa.
- Margen de seguridad documentado: stock_final = consumo + max(1, ceil(10%));
  nunca por debajo de +1 unidad; cuantizado a la escala NUMERIC(15,4).
- Idempotencia por verificacion: el delta se calcula contra el stock_actual
  REAL (stock_ajuste = max(0, objetivo - actual)); re-ejecutar con el stock ya
  en el objetivo no suma nada. Ademas, un registro JSON (gitignored, reports/)
  marca los insumos ya ajustados con fecha (marca de ajuste documentada);
  --force re-aplica tras una recarga limpia.
- dry-run (default): lee la DB y reporta que haria, 0 escrituras y NO crea el
  registro. commit: aplica los deltas y escribe el registro.
- Insumo inexistente: WARN claro en dry-run (exit 0); ERROR claro en commit
  (exit 1, rollback atomico: nada se aplica).

Test-injected rows use el prefijo 'Migratest ' y mapas inyectados (nunca tocan
CONSUMOS_BOM ni filas reales); el registro se escribe en tmp_path.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from app.db.session import SessionLocal
from app.models import Insumo, TipoProducto

# Names injected by tests; cleanup deletes exactly these, never catalog rows.
P = "Migratest"
P_AJUSTE = f"{P} Ajuste Tela"
P_AJUSTE2 = f"{P} Ajuste Argolla"
P_FANTASMA = f"{P} Ajuste Inexistente"

# Mapa inyectado para tests DB (consumo 2 y 30, respectivamente).
MAPA_TEST = {P_AJUSTE: Decimal("2"), P_AJUSTE2: Decimal("30")}


# --------------------------------------------------------------------------- #
# Module-level DB cleanup (canonical tipos + test rows)
# --------------------------------------------------------------------------- #


def _borrar_filas_test(db) -> None:
    db.query(Insumo).filter(
        Insumo.nombre.in_([P_AJUSTE, P_AJUSTE2, P_FANTASMA])
    ).delete(synchronize_session=False)
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


def _preparar_insumos(db) -> None:
    """F1-ish: bootstrap + 2 insumos de prueba (stock_actual 0 explicitos)."""
    from migrate.catalog import bootstrap_catalogo, upsert_insumo

    bootstrap_catalogo(db)
    upsert_insumo(db, P_AJUSTE, categoria_nombre="Telas")
    upsert_insumo(db, P_AJUSTE2, categoria_nombre="Herrajes")
    # reset de stock por test (la sesion de modulo es compartida entre tests).
    db.query(Insumo).filter(
        Insumo.nombre.in_([P_AJUSTE, P_AJUSTE2])
    ).update({"stock_actual": Decimal("0")}, synchronize_session=False)
    db.commit()


# --------------------------------------------------------------------------- #
# 1. Pure: mapa de consumos (los 10 residuales de #425) + margen + objetivo
# --------------------------------------------------------------------------- #


def test_mapa_consumos_tiene_los_10_insumos_residuales():
    from migrate.adjust_stock import CONSUMOS_BOM

    assert len(CONSUMOS_BOM) == 10
    esperado = {
        "Cadena gris delgada totebag": Decimal("318"),
        "Cadena plateada gruesa totebag": Decimal("288"),
        "Cremallera num 3": Decimal("240"),
        "Tapavarilla negro 10 mts": Decimal("379"),
        "Sublimacion para las totebag": Decimal("2.802"),
        "Super Brioni": Decimal("3"),
        "Satin elastico negro": Decimal("0.0396"),
        "Satin elastico rosa": Decimal("0.045"),
        "Sesgo elastico negro 2cm brillante": Decimal("0.325"),
        "Sesgo rigido para ojales corset": Decimal("30"),
    }
    for nombre, consumo in esperado.items():
        assert CONSUMOS_BOM[nombre] == consumo, nombre


def test_margen_seguridad_minimo_1_y_10_por_ciento_arriba():
    from migrate.adjust_stock import margen_seguridad

    # 10% redondeado hacia arriba: 318 -> 32; 30 -> 3
    assert margen_seguridad(Decimal("318")) == Decimal("32")
    assert margen_seguridad(Decimal("30")) == Decimal("3")
    # minimo 1 unidad (consumos chicos / fraccionales)
    assert margen_seguridad(Decimal("0.0396")) == Decimal("1")
    assert margen_seguridad(Decimal("2.802")) == Decimal("1")
    assert margen_seguridad(Decimal("3")) == Decimal("1")


def test_stock_final_objetivo_es_consumo_mas_margen():
    from migrate.adjust_stock import stock_final_objetivo

    assert stock_final_objetivo(Decimal("318")) == Decimal("350.0000")
    assert stock_final_objetivo(Decimal("30")) == Decimal("33.0000")
    assert stock_final_objetivo(Decimal("0.0396")) == Decimal("1.0396")
    assert stock_final_objetivo(Decimal("2.802")) == Decimal("3.8020")


def test_stock_ajuste_es_max_0_objetivo_menos_actual():
    from migrate.adjust_stock import stock_ajuste_para

    # stock 0 -> ajuste = objetivo completo
    assert stock_ajuste_para(Decimal("318"), Decimal("0")) == Decimal("350.0000")
    # stock parcial -> ajuste = lo que falta
    assert stock_ajuste_para(Decimal("318"), Decimal("340")) == Decimal("10.0000")
    # stock ya en el objetivo -> 0 (nunca suma doble)
    assert stock_ajuste_para(Decimal("318"), Decimal("350")) == Decimal("0")
    assert stock_ajuste_para(Decimal("318"), Decimal("400")) == Decimal("0")


# --------------------------------------------------------------------------- #
# 2. DB dry-run: 0 escrituras y NO crea el registro
# --------------------------------------------------------------------------- #


def test_dry_run_no_escribe_ni_crea_registro(db, tmp_path):
    from migrate.adjust_stock import ejecutar

    _preparar_insumos(db)
    reg = tmp_path / "registry.json"
    insumo = db.query(Insumo).filter(Insumo.nombre == P_AJUSTE).one()
    insumo.stock_actual = Decimal("0")
    db.commit()

    codigo = ejecutar(
        modo="dry-run", consumos=MAPA_TEST, registry_path=reg, fase_final=4
    )
    assert codigo == 0
    db.expire_all()
    insumo = db.query(Insumo).filter(Insumo.nombre == P_AJUSTE).one()
    assert insumo.stock_actual == Decimal("0")  # 0 escrituras
    assert not reg.exists()  # dry-run nunca crea el registro


# --------------------------------------------------------------------------- #
# 3. DB commit: suma el delta y registra; idempotente (2da corrida no suma)
# --------------------------------------------------------------------------- #


def test_commit_suma_stock_ajuste_y_escribe_registro(db, tmp_path):
    from migrate.adjust_stock import ejecutar

    _preparar_insumos(db)
    reg = tmp_path / "registry.json"

    codigo = ejecutar(
        modo="commit", consumos=MAPA_TEST, registry_path=reg, fase_final=4
    )
    assert codigo == 0
    db.expire_all()
    tela = db.query(Insumo).filter(Insumo.nombre == P_AJUSTE).one()
    arg = db.query(Insumo).filter(Insumo.nombre == P_AJUSTE2).one()
    # consumo 2 -> objetivo 3.0000 (margen min 1); consumo 30 -> objetivo 33
    assert tela.stock_actual == Decimal("3.0000")
    assert arg.stock_actual == Decimal("33.0000")
    # registro JSON escrito con la marca de ajuste
    assert reg.exists()
    data = __import__("json").loads(reg.read_text(encoding="utf-8"))
    ajustes = data["ajustes"]
    assert P_AJUSTE in ajustes
    assert ajustes[P_AJUSTE]["consumo"] == "2"
    assert ajustes[P_AJUSTE]["stock_final"] == "3.0000"
    assert "fecha" in ajustes[P_AJUSTE]


def test_commit_idempotente_segunda_corrida_no_suma(db, tmp_path):
    from migrate.adjust_stock import ejecutar

    _preparar_insumos(db)
    reg = tmp_path / "registry.json"

    assert ejecutar(modo="commit", consumos=MAPA_TEST, registry_path=reg) == 0
    db.expire_all()
    assert (
        db.query(Insumo).filter(Insumo.nombre == P_AJUSTE).one().stock_actual
        == Decimal("3.0000")
    )
    # 2da corrida: stock ya en el objetivo -> delta 0 + marca de registro
    assert ejecutar(modo="commit", consumos=MAPA_TEST, registry_path=reg) == 0
    db.expire_all()
    tela = db.query(Insumo).filter(Insumo.nombre == P_AJUSTE).one()
    assert tela.stock_actual == Decimal("3.0000")  # no suma doble


# --------------------------------------------------------------------------- #
# 4. Insumo inexistente: WARN en dry-run, ERROR en commit (rollback atomico)
# --------------------------------------------------------------------------- #


def test_dry_run_insumo_inexistente_warn_y_exit_0(db, tmp_path):
    from migrate.adjust_stock import ejecutar

    _preparar_insumos(db)
    mapa = {P_FANTASMA: Decimal("5")}
    codigo = ejecutar(modo="dry-run", consumos=mapa, registry_path=tmp_path / "r.json")
    assert codigo == 0  # WARN no bloquea el dry-run


def test_commit_insumo_inexistente_error_y_rollback_atomico(db, tmp_path):
    from migrate.adjust_stock import ejecutar

    _preparar_insumos(db)
    # Estado limpio por test (la sesion de modulo es compartida): stock 0.
    ins = db.query(Insumo).filter(Insumo.nombre == P_AJUSTE).one()
    ins.stock_actual = Decimal("0")
    db.commit()
    # mapa con un insumo real (stock 0) + uno inexistente
    mapa = {P_AJUSTE: Decimal("2"), P_FANTASMA: Decimal("5")}
    codigo = ejecutar(modo="commit", consumos=mapa, registry_path=tmp_path / "r.json")
    assert codigo == 1  # ERROR -> exit 1
    db.expire_all()
    # rollback atomico: NADA se aplico (ni el insumo valido)
    assert (
        db.query(Insumo).filter(Insumo.nombre == P_AJUSTE).one().stock_actual
        == Decimal("0.0000")
    )


# --------------------------------------------------------------------------- #
# 5. CLI argparse: dry-run default, --commit, --fase-final, --force
# --------------------------------------------------------------------------- #


def test_cli_dry_run_es_default():
    from migrate.adjust_stock import construir_parser

    args = construir_parser().parse_args([])
    assert args.modo == "dry-run"
    assert args.fase_final == 4


def test_cli_commit_flag_y_fase_final():
    from migrate.adjust_stock import construir_parser

    args = construir_parser().parse_args(["--commit", "--fase-final", "4"])
    assert args.modo == "commit"
    assert args.fase_final == 4


def test_cli_force_flag():
    from migrate.adjust_stock import construir_parser

    args = construir_parser().parse_args(["--commit", "--force"])
    assert args.modo == "commit"
    assert args.force is True


# --------------------------------------------------------------------------- #
# 6. Phase harness: dry-run real (0 escrituras, exit 0) + mapa real de 10
# --------------------------------------------------------------------------- #


def test_ejecutar_dry_run_real_mapa_default_no_escribe(db, tmp_path):
    from migrate.adjust_stock import CONSUMOS_BOM, ejecutar

    antes = db.query(Insumo).count()
    codigo = ejecutar(
        modo="dry-run", consumos=CONSUMOS_BOM, registry_path=tmp_path / "r.json"
    )
    assert codigo == 0
    assert db.query(Insumo).count() == antes  # 0 escrituras
    assert not (tmp_path / "r.json").exists()
