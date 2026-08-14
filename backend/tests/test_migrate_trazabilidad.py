"""Contract tests for migration traceability (spec EXM-6) + CLI per-phase
counts (NFR-2) — remediation of verify-report findings.

- EXM-6: every run (dry-run and commit) persists a JSON trace under
  ``reports/migracion_YYYYMMDD_HHMMSS.json`` with the executed phases, counts
  per phase, errors/WARN entries, a timestamp and a content hash (drift /
  re-run detection). ``Report.write()`` must have a real caller: the CLI.
- NFR-2: the CLI must surface each runner's internal report (INFO/ERROR/WARN)
  on stdout — the per-phase counts were previously swallowed.

Pure CLI-level tests: dry-run on a mini workbook, no DB needed.
"""

import json
from pathlib import Path

import openpyxl

from migrate import cli
from migrate.context import FaseOptions

PREFIX = "MigraTraza"


def _mini_workbook(path: Path) -> None:
    """Mini workbook with Proveedores + CORSET (F1 plan with real counts)."""
    wb = openpyxl.Workbook()
    prov = wb.active
    prov.title = "Proveedores"
    prov.append(["Proveedor", "URL", "Precio Unidad", "Ubicacion", "Contactado"])
    prov.append(["", "Bexxhamel", None, "Cali", "SI"])  # B=nombre
    bom = wb.create_sheet("CORSET")
    bom.append(["CORSET", None, None, None, None, None, None, None, "TANGA"])
    bom.append(["Producto", "Ancho", "Alto", "cantidad Cms", "valor metro", "valor total"])
    bom.append([f"{PREFIX} Tela", 64, 37, 2368, 2.5, None])  # A=material, D=cm2
    wb.save(path)


def _ejecutar(tmp_path: Path, fases: list[str]):
    reports_dir = tmp_path / "reports"
    mini = tmp_path / "mini.xlsx"
    _mini_workbook(mini)
    codigo = cli.ejecutar(FaseOptions(source=mini, modo="dry-run"), fases, reports_dir=reports_dir)
    jsons = sorted(reports_dir.glob("migracion_*.json"))
    return codigo, jsons


# --------------------------------------------------------------------------- #
# EXM-6: the run persists a JSON trace with fases / results / hash
# --------------------------------------------------------------------------- #


def test_dry_run_genera_json_trazabilidad(tmp_path):
    codigo, jsons = _ejecutar(tmp_path, ["F1"])
    assert codigo == 0
    assert len(jsons) == 1
    data = json.loads(jsons[0].read_text(encoding="utf-8"))
    assert data["modo"] == "dry-run"
    assert data["fases"] == ["F1"]
    assert "generado" in data  # timestamp
    assert data["hash_contenido"]  # content hash for drift detection
    # Per-phase counts of the runner report are captured.
    assert "F1" in data["conteos_por_fase"]
    assert data["conteos_por_fase"]["F1"]["INFO"] >= 1
    # The trace holds real entries (runner INFO lines), not only markers.
    assert any(e["nivel"] == "INFO" for e in data["entradas"])


def test_json_trazabilidad_conteos_y_error(tmp_path):
    codigo, jsons = _ejecutar(tmp_path, ["F1", "F2"])
    assert codigo == 0
    data = json.loads(jsons[0].read_text(encoding="utf-8"))
    assert data["fases"] == ["F1", "F2"]
    # Both phases counted; missing purchase sheets produce WARN entries.
    assert set(data["conteos_por_fase"]) == {"F1", "F2"}
    assert any(e["nivel"] == "WARN" for e in data["entradas"])
    assert data["conteos_por_fase"]["F1"]["INFO"] >= 1


def test_hash_contenido_estable_para_mismo_run(tmp_path):
    """Same content -> same hash (re-run/drift detection, EXM-6)."""
    _, jsons_a = _ejecutar(tmp_path, ["F1"])
    data_a = json.loads(jsons_a[0].read_text(encoding="utf-8"))

    reports_dir = tmp_path / "reports2"
    mini = tmp_path / "mini2.xlsx"
    _mini_workbook(mini)
    cli.ejecutar(FaseOptions(source=mini, modo="dry-run"), ["F1"], reports_dir=reports_dir)
    jsons_b = sorted(reports_dir.glob("migracion_*.json"))
    data_b = json.loads(jsons_b[0].read_text(encoding="utf-8"))

    assert data_a["hash_contenido"] == data_b["hash_contenido"]
    assert len(data_a["hash_contenido"]) == 64  # sha256 hex


# --------------------------------------------------------------------------- #
# NFR-2: the CLI prints the runner's INFO/ERROR/WARN (per-phase counts)
# --------------------------------------------------------------------------- #


def test_cli_emite_conteos_por_fase_en_stdout(tmp_path, capsys):
    reports_dir = tmp_path / "reports"
    mini = tmp_path / "mini.xlsx"
    _mini_workbook(mini)
    cli.ejecutar(FaseOptions(source=mini, modo="dry-run"), ["F1"], reports_dir=reports_dir)
    out = capsys.readouterr().out
    # The runner's count line (plan catalogo: N proveedores, N insumos...).
    assert "plan catalogo" in out
    assert "proveedores" in out
    # ASCII-only stdout: no unicode arrows anywhere.
    assert "\u2192" not in out
