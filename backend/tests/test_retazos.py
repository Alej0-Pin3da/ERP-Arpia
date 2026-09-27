"""V4 Eje 3.2 foundation: reusable-offcut decision is deterministic.

Pure helpers only (no DB): offcuts above 0.5 m2 re-enter as Retazo
insumos through the existing manual Insumos flow; the rest is waste.
"""

from decimal import Decimal

from app.services.produccion import (
    UMBRAL_RETAZO_M2,
    clasificar_retazo,
    es_retazo_reutilizable,
    estimar_retazos_lote,
)


def test_umbral_es_medio_metro():
    assert UMBRAL_RETAZO_M2 == Decimal("0.5")


def test_borde_no_reingresa():
    assert es_retazo_reutilizable("0.5") is False
    assert es_retazo_reutilizable("0.49") is False
    assert clasificar_retazo("0.5") == "desperdicio"


def test_sobre_umbral_reingresa():
    assert es_retazo_reutilizable("0.51") is True
    assert clasificar_retazo("2") == "retazo"


def test_estimacion_lote_con_ancho():
    res = estimar_retazos_lote("1", "1.5")
    assert res["area_m2"] == Decimal("1.5")
    assert res["reingresable"] is True
    assert res["clasificacion"] == "retazo"


def test_estimacion_sin_sobrante_es_desperdicio():
    res = estimar_retazos_lote("0")
    assert res["area_m2"] == Decimal("0")
    assert res["reingresable"] is False
