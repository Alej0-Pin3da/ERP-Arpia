"""Tests for migrate.cli - argparse contract (PR#1 slice) + the commit-only
omisiones persistence hook (PR3, task T4 / spec MIG-1/MIG-2).

The hook runs after ``run_report.write()`` in commit mode only: every
WARN/ERROR entry of the run is inserted into Migracion_Omisiones with
corrida = the JSON trace file stem. Contract under test:
- commit inserts rows (WARN/ERROR only; INFO skipped; resuelta False;
  corrida_id = trace stem; fase = run fase) — MIG-1/MIG-2 normal.
- dry-run inserts 0 rows — MIG-2 edge.
- a DB failure in the persist is NON-fatal: exit code untouched and the
  JSON trace (content + hash) byte-identical to a successful run — MIG-2 error.

A fake F0 runner injects deterministic WARN/ERROR/INFO entries into the
phase report without touching the DB, so the tests never write catalog
rows. Test rows in Migracion_Omisiones are wiped at module start/end.
"""

import json
from pathlib import Path

import openpyxl
import pytest

from app.db.session import SessionLocal
from app.models import MigracionOmision
from migrate import cli
from migrate.context import FaseOptions


@pytest.fixture(autouse=True)
def _omisiones_tabla_limpia():
    """Every test starts with zero Migracion_Omisiones rows (the corrida id
    is the trace file stem — second resolution — so rows must never leak
    between tests)."""
    db = SessionLocal()
    try:
        db.query(MigracionOmision).delete()
        db.commit()
    finally:
        db.close()


def _mini_workbook(path: Path) -> None:
    """Minimal workbook so the infra read never fails."""
    wb = openpyxl.Workbook()
    bom = wb.active
    bom.title = "CORSET"
    bom.append(["CORSET", None, None, None, None, None, None, None, "TANGA"])
    bom.append(["Producto", "Ancho", "Alto", "cantidad Cms", "valor metro", "valor total"])
    bom.append(["", None, None, None, None, None])
    wb.save(path)


def _runner_con_omisiones(ctx) -> None:
    """Fake F0 runner: INFO + WARN + ERROR with known messages, no DB writes."""
    ctx.report.info("HojaX", 1, "A1", "fila informativa")
    ctx.report.warn("HojaX", 3, "B2", "celda con divergencia")
    ctx.report.error("HojaX", 5, "C3", "fila invalida")


def _runner_solo_warns(ctx) -> None:
    """Fake F0 runner: only WARN entries -> exit code stays 0."""
    ctx.report.warn("HojaX", 3, "B2", "celda con divergencia")


def _corrida_para(reports_dir: Path) -> str:
    jsons = sorted(reports_dir.glob("migracion_*.json"))
    assert len(jsons) == 1
    return jsons[0].stem


def _contar_omisiones(corrida: str) -> int:
    db = SessionLocal()
    try:
        return db.query(MigracionOmision).filter(MigracionOmision.corrida_id == corrida).count()
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# MIG-2: commit persiste, dry-run no, fallo no-fatal, JSON intacto
# --------------------------------------------------------------------------- #


def test_commit_persiste_omisiones_warn_error_no_info(tmp_path, monkeypatch):
    monkeypatch.setitem(cli.FASE_RUNNERS, "F0", _runner_con_omisiones)
    mini = tmp_path / "mini.xlsx"
    _mini_workbook(mini)
    reports_dir = tmp_path / "reports"

    codigo = cli.ejecutar(
        FaseOptions(source=mini, modo="commit"),
        ["F0"],
        reports_dir=reports_dir,
    )
    assert codigo == 1  # the fake runner reports an ERROR -> exit 1

    corrida = _corrida_para(reports_dir)
    db = SessionLocal()
    try:
        filas = db.query(MigracionOmision).filter(MigracionOmision.corrida_id == corrida).all()
        mensajes = {f.mensaje for f in filas}
        niveles = {f.nivel for f in filas}
        # The runner's WARN and ERROR entries were persisted...
        assert "celda con divergencia" in mensajes
        assert "fila invalida" in mensajes
        assert niveles == {"WARN", "ERROR"}
        # ... INFO entries were skipped, defaults hold, fase = run fase.
        assert not any(f.nivel == "INFO" for f in filas)
        assert all(f.resuelta is False for f in filas)
        assert all(f.fase == "F0" for f in filas)
        assert all(f.corrida_id == corrida for f in filas)
        assert any(f.hoja == "HojaX" and f.fila == 3 and f.celda == "B2" for f in filas)
    finally:
        db.close()


def test_dry_run_no_persiste_omisiones(tmp_path, monkeypatch):
    monkeypatch.setitem(cli.FASE_RUNNERS, "F0", _runner_con_omisiones)
    mini = tmp_path / "mini.xlsx"
    _mini_workbook(mini)
    reports_dir = tmp_path / "reports"

    codigo = cli.ejecutar(
        FaseOptions(source=mini, modo="dry-run"),
        ["F0"],
        reports_dir=reports_dir,
    )
    assert codigo == 1  # ERROR present in the run report

    corrida = _corrida_para(reports_dir)
    assert _contar_omisiones(corrida) == 0  # MIG-2 edge: dry-run -> 0 rows


def test_fallo_persistencia_db_no_fatal_y_json_intacto(tmp_path, monkeypatch):
    """MIG-2 error: a DB failure in the persist does NOT abort the run, does
    NOT change the exit code, and leaves the JSON trace byte-identical (the
    trace is written before the hook; the failure WARN is in-memory only)."""
    monkeypatch.setitem(cli.FASE_RUNNERS, "F0", _runner_solo_warns)
    mini = tmp_path / "mini.xlsx"
    _mini_workbook(mini)

    # Control run (persist succeeds) -> reference hash + trace.
    reports_a = tmp_path / "reports_a"
    cli.ejecutar(FaseOptions(source=mini, modo="commit"), ["F0"], reports_dir=reports_a)
    jsons_a = sorted(reports_a.glob("migracion_*.json"))
    control = json.loads(jsons_a[0].read_text(encoding="utf-8"))
    corrida_a = jsons_a[0].stem
    db = SessionLocal()
    try:
        filas_antes = db.query(MigracionOmision).count()
    finally:
        db.close()
    try:

        def _db_caida(db, run_report, corrida_id):
            raise RuntimeError("db caida simulada")

        monkeypatch.setattr("migrate.omisiones.persistir_omisiones", _db_caida)
        reports_b = tmp_path / "reports_b"
        codigo = cli.ejecutar(
            FaseOptions(source=mini, modo="commit"), ["F0"], reports_dir=reports_b
        )
        assert codigo == 0  # WARN-only run: exit code intact despite the failure

        jsons_b = sorted(reports_b.glob("migracion_*.json"))
        assert len(jsons_b) == 1
        fallido = json.loads(jsons_b[0].read_text(encoding="utf-8"))
        # Same content hash and same entries -> the hook never altered the trace.
        assert fallido["hash_contenido"] == control["hash_contenido"]
        assert fallido["entradas"] == control["entradas"]
        # The failed run persisted nothing (whole-table count is unchanged —
        # the corrida stem may collide with the control run within the same
        # second, so counting by corrida is not reliable here).
        db = SessionLocal()
        try:
            assert db.query(MigracionOmision).count() == filas_antes
        finally:
            db.close()
    finally:
        db = SessionLocal()
        try:
            db.query(MigracionOmision).filter(MigracionOmision.corrida_id == corrida_a).delete()
            db.commit()
        finally:
            db.close()


def test_dry_run_es_default():
    parser = cli.construir_parser()
    args = parser.parse_args([])
    assert args.modo == "dry-run"


def test_commit_flag():
    parser = cli.construir_parser()
    args = parser.parse_args(["--commit"])
    assert args.modo == "commit"


def test_fase_simple():
    parser = cli.construir_parser()
    args = parser.parse_args(["--fase", "2"])
    assert args.fase == "2"
    assert args.todas is False


def test_fase_f0_aceptado():
    assert cli._normalizar_fase("0") == "F0"
    assert cli._normalizar_fase("F7") == "F7"


def test_all_flag_setea_todas():
    parser = cli.construir_parser()
    args = parser.parse_args(["--all"])
    assert args.todas is True


def test_fase_y_all_son_mutuamente_excluyentes():
    parser = cli.construir_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--fase", "1", "--all"])


def test_fases_a_correr():
    fases = cli._fases_a_correr(type("A", (), {"todas": False, "fase": "0"})())
    assert fases == ["F0"]

    fases_all = cli._fases_a_correr(type("A", (), {"todas": True, "fase": None})())
    assert fases_all[0] == "F0"
    assert fases_all[-1] == "F7"


def test_fase_inexistente_es_clara():
    from migrate import get_fase

    with pytest.raises(KeyError, match="F9"):
        get_fase("F9")
