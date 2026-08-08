"""Tests for migrate.loaders - bounded per-sheet reading (PR#1 slice)."""

from pathlib import Path

import openpyxl
import pytest

from migrate.loaders import (
    HojaInexistenteError,
    LibroMigracion,
    SHEET_BOUNDS,
)


def _crear_libro(path: Path) -> None:
    """Mini ARPIA-like workbook: VENTAS + Proveedores-like inflated sheet."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "VENTAS"
    # Header row (R1) + 3 real rows (R2..R4) + junk M37 loose cell.
    ws.append(["Producto", "G", "H", "M", "P"])
    ws.append(["SET AELO", 80000, 38805, None, "celes"])
    ws.append(["TOTEBAG", 45000, 25765.09524, None, "Camila"])
    ws.append(["", 95000, 29826, None, "Olga"])
    ws["M37"] = 65618.01429  # loose junk cell (as in real VENTAS)
    # Proveedores: header + 4 real rows, then formatted rows up to 1001.
    prov = wb.create_sheet("Proveedores")
    prov.append(["TIPO", "URL", "Precio Unidad", "Ubicacion", "Contactado"])
    for nombre in ["Bexxhamel", "JM Confecciones", "SEHA Text", "ZureTex"]:
        prov.append(["Camisetas", nombre, 11500, "Cali", "SI"])
    wb.save(path)


@pytest.fixture
def mini_libro(tmp_path) -> Path:
    path = tmp_path / "mini.xlsx"
    _crear_libro(path)
    return path


def test_lee_rango_acotado_ventas(mini_libro):
    with LibroMigracion(mini_libro) as libro:
        lect = libro.leer_hoja("VENTAS")
        # 3 filas reales (la 4ta fila del fixture no tiene producto, igual cuenta
        # como fila leida porque el loader acota por rango, no por semantica).
        assert len(lect.filas) >= 3


def test_rango_acotado_no_lee_fuera_del_rango(mini_libro):
    with LibroMigracion(mini_libro) as libro:
        lect = libro.leer_hoja("VENTAS")
        # Rango acotado 2..17: 3 filas reales; las vacias R5..R17 se descartan
        # (13); la celda suelta M37 queda fuera del rango y nunca es dato.
        assert len(lect.filas) == 3
        assert lect.descartadas == 13
        assert not any("M37" in fila for fila in lect.filas)


def test_proveedores_matriz_inflada_acotada(mini_libro):
    with LibroMigracion(mini_libro) as libro:
        lect = libro.leer_hoja("Proveedores")
        # Aunque openpyxl reporta max_row=1001, los bounds acotan a R2..R5.
        assert len(lect.filas) == 4
        assert lect.descartadas == 0


def test_hoja_inexistente_error_claro(mini_libro):
    with LibroMigracion(mini_libro) as libro:
        with pytest.raises(HojaInexistenteError) as exc:
            libro.leer_hoja("NO EXISTE")
        assert "NO EXISTE" in str(exc.value)
        assert "mini.xlsx" in str(exc.value)


def test_m37_suelta_reportada(mini_libro):
    from migrate.report import Report

    report = Report(fase="test", modo="dry-run")
    with LibroMigracion(mini_libro) as libro:
        libro.leer_hoja("VENTAS", report=report)
    warns = [e for e in report.entradas if e.nivel == "WARN" and e.hoja == "VENTAS"]
    assert any(e.celda == "M37" for e in warns)


def test_todas_las_hojas_registradas():
    # El libro real tiene 24 hojas; el spec de bounds debe cubrirlas todas.
    from openpyxl import load_workbook as lw

    real = Path(r"C:\wamp64\www\ERP-Arpia\ARPIA.xlsx")
    if not real.exists():
        pytest.skip("ARPIA.xlsx no disponible")
    wb = lw(real, read_only=True, data_only=True)
    faltantes = [s for s in wb.sheetnames if s not in SHEET_BOUNDS]
    wb.close()
    assert faltantes == [], f"hojas sin bounds: {faltantes}"