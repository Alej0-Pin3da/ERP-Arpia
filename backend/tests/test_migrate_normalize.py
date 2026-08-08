"""Tests for migrate.normalize (units, decimals, dates, cm2) - PR#1 slice."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from migrate.normalize import (
    ancho_desde_nombre,
    coerce_aware,
    convertir_cantidad,
    es_aware,
    fecha_para_fila,
    normalizar_area_m2,
    normalizar_decimal,
    parsear_cantidad_unidad,
    unidad_canonica,
)


@pytest.mark.parametrize(
    ("celda", "esperado"),
    [
        ("9,5", Decimal("9.5")),
        ("9.5", Decimal("9.5")),
        ("1.234,56", Decimal("1234.56")),
        (95000, Decimal("95000")),
        (295000.0, Decimal("295000")),
        (Decimal("3.5"), Decimal("3.5")),
        ("0", Decimal("0")),
    ],
)
def test_decimal_comma(celda, esperado):
    assert normalizar_decimal(celda) == esperado


@pytest.mark.parametrize(
    "celda",
    ["", "abc", "#DIV/0!", "#REF!", None, True],
)
def test_decimal_no_interpretable(celda):
    # Excel error strings are NOT inferred (EXM-2 error scenario).
    assert normalizar_decimal(celda) is None


def test_parse_cantidad_unidad_mts():
    parsed = parsear_cantidad_unidad("9,5 mts")
    assert parsed is not None
    assert parsed.cantidad == Decimal("9.5")
    assert parsed.unidad == "mts"


def test_parse_cantidad_unidad_cms():
    parsed = parsear_cantidad_unidad("60 cms")
    assert parsed is not None
    assert parsed.cantidad == Decimal("60")
    assert parsed.unidad == "cms"


def test_parse_cantidad_unidad_numero_plano():
    parsed = parsear_cantidad_unidad(78)
    assert parsed is not None
    assert parsed.cantidad == Decimal("78")
    assert parsed.unidad == "un"  # bare number -> unit 'un' (herrajes)


def test_unidad_canonica_sinonimos():
    assert unidad_canonica("mts") == "m"
    assert unidad_canonica("cms") == "cm"
    assert unidad_canonica("CM") == "cm"
    assert unidad_canonica("unidades") == "un"
    assert unidad_canonica("kg") == "kg"


def test_convertir_cantidad_telas_a_m():
    cantidad, unidad = convertir_cantidad(Decimal("9.5"), "mts", "Telas")
    assert unidad == "m"
    assert cantidad == Decimal("9.5")


def test_convertir_cantidad_cms_a_m():
    cantidad, unidad = convertir_cantidad(Decimal("60"), "cms", "Telas")
    assert unidad == "m"
    assert cantidad == Decimal("0.60")


def test_convertir_cantidad_herrajes_un():
    cantidad, unidad = convertir_cantidad(Decimal("78"), "un", "Herrajes")
    assert unidad == "un"
    assert cantidad == Decimal("78")


def test_area_50x280_cm_a_m2():
    assert normalizar_area_m2("50 x 280 cm") == Decimal("1.4")


def test_area_no_aplica():
    assert normalizar_area_m2("10 mts") is None
    assert normalizar_area_m2("") is None


def test_ancho_desde_nombre():
    assert ancho_desde_nombre("Ref 100 24 cm tul bordado") == Decimal("24")


def test_ancho_default_con_warn():
    report = type("R", (), {"warn": lambda self, *a: None})()
    # Sin ancho en el nombre -> default 100cm + WARN (no regex match).
    assert ancho_desde_nombre("Velcro sin medida", report=report) == Decimal("100")


def test_fecha_heredada_mismo_insumo_proveedor():
    cache: dict = {}
    # Fila contigua previa: misma clave (insumo, proveedor) -> hereda.
    fecha_base = datetime(2025, 10, 25, tzinfo=timezone.utc)
    clave = ("Encaje negro", "Kilotelas")
    ultima = {clave: fecha_base}
    assert fecha_para_fila(None, clave, ultima) == fecha_base


def test_fecha_no_heredada_sin_contigua():
    # Sin contigua del mismo (insumo, proveedor) -> None, NUNCA now().
    assert fecha_para_fila(None, ("Velo", "Las 3BBB"), {}) is None

@pytest.mark.parametrize(
    "dt,esperado",
    [
        (datetime(2025, 10, 25), False),
        (datetime(2025, 10, 25, tzinfo=timezone.utc), True),
    ],
)
def test_es_aware(dt, esperado):
    assert es_aware(dt) is esperado


def test_coerce_aware_report():
    dt = datetime(2025, 10, 25)
    out = coerce_aware(dt)
    assert isinstance(out, datetime)
    assert out.tzinfo is not None