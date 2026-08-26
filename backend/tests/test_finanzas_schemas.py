"""Finanzas v4 schema tests — strict TDD (PR2, task 2.1 RED).

Pure Pydantic validation (no DB): verifies the extended socia profile and the
new liquidacion/anticipo schemas reject invalid input at the schema layer —
invalid email, non-Literal tipo_cuenta, non-positive anticipo monto, out-of-range
rol length, and non-Literal state-transition payloads.

These tests reference new schema classes/fields that do NOT exist yet in
``app.schemas.finanzas``, so they fail on import (RED) until task 2.2 (GREEN)
adds them.
"""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.finanzas import (
    AnticipoCreate,
    AnticipoEstadoUpdate,
    LiquidacionCreate,
    LiquidacionEstadoUpdate,
    SocioConfiguracionCreate,
    SocioConfiguracionUpdate,
)


def _liquidacion_payload(**overrides) -> dict:
    payload = {
        "periodo": "2026-07",
        "fecha_cierre": date(2026, 7, 31),
        "total_ventas_brutas": Decimal("150000"),
        "costo_taller_insumos": Decimal("30000"),
        "gastos_operativos": Decimal("20000"),
        "utilidad_neta_total": Decimal("100000"),
        "fondo_reinversion_monto": Decimal("40000"),
        "utilidad_repartible": Decimal("60000"),
        "observaciones": None,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# SOC-2: Socia field validation (email, tipo_cuenta, rol length, defaults)
# ---------------------------------------------------------------------------


def test_socia_minimal_create_aplica_defaults():
    """POST /finanzas/socios con solo nombre+porcentaje -> defaults de las 10
    columnas nuevas (es_fondo_taller False, activo True, resto None) (SOC-1/SOC-2)."""
    payload = SocioConfiguracionCreate(nombre="Margarita", porcentaje_participacion=Decimal("30"))
    assert payload.es_fondo_taller is False
    assert payload.activo is True
    assert payload.email is None
    assert payload.tipo_cuenta is None
    assert payload.rol is None


def test_socia_email_valido_aceptado():
    """email RFC-5321 válido -> no lanza (SOC-2)."""
    payload = SocioConfiguracionCreate(
        nombre="Margarita",
        porcentaje_participacion=Decimal("30"),
        email="margarita@arpia.com",
    )
    assert payload.email == "margarita@arpia.com"


def test_socia_email_invalido_rechazado():
    """email 'not-an-email' -> ValidationError (SOC-2: RFC 5321 basic check)."""
    with pytest.raises(ValidationError):
        SocioConfiguracionCreate(
            nombre="Margarita",
            porcentaje_participacion=Decimal("30"),
            email="not-an-email",
        )


def test_socia_tipo_cuenta_literal_valido():
    """tipo_cuenta AHORROS (dentro del Literal) -> aceptado (SOC-2 SHOULD)."""
    payload = SocioConfiguracionCreate(
        nombre="Margarita",
        porcentaje_participacion=Decimal("30"),
        tipo_cuenta="AHORROS",
    )
    assert payload.tipo_cuenta == "AHORROS"


@pytest.mark.parametrize("tipo", ["INVERSION", "CREDITO", "ahorros", "SAVINGS"])
def test_socia_tipo_cuenta_invalido_rechazado(tipo):
    """tipo_cuenta fuera de {AHORROS, CORRIENTE, OTRA} -> ValidationError (SOC-2)."""
    with pytest.raises(ValidationError):
        SocioConfiguracionCreate(
            nombre="Margarita",
            porcentaje_participacion=Decimal("30"),
            tipo_cuenta=tipo,
        )


def test_socia_rol_muy_largo_rechazado():
    """rol > 50 chars -> ValidationError (SOC-2 max 50)."""
    with pytest.raises(ValidationError):
        SocioConfiguracionCreate(
            nombre="Margarita",
            porcentaje_participacion=Decimal("30"),
            rol="x" * 51,
        )


def test_socia_rol_limite_50_aceptado():
    """rol de exactamente 50 chars -> aceptado (boundary SOC-2)."""
    payload = SocioConfiguracionCreate(
        nombre="Margarita",
        porcentaje_participacion=Decimal("30"),
        rol="r" * 50,
    )
    assert len(payload.rol) == 50


def test_socia_porcentaje_no_positivo_rechazado():
    """porcentaje_participacion <= 0 -> ValidationError (schema gt=0)."""
    with pytest.raises(ValidationError):
        SocioConfiguracionCreate(nombre="M", porcentaje_participacion=Decimal("0"))
    with pytest.raises(ValidationError):
        SocioConfiguracionCreate(nombre="M", porcentaje_participacion=Decimal("-5"))


def test_socia_update_campos_opcionales():
    """SociaUpdate acepta cada campo nuevo de forma independiente (SOC-1 PATCH)."""
    up = SocioConfiguracionUpdate(email="m@arpia.com", tipo_cuenta="CORRIENTE")
    assert up.email == "m@arpia.com"
    assert up.tipo_cuenta == "CORRIENTE"
    # campos no enviados quedan None para aplicar solo lo enviado
    assert up.porcentaje_participacion is None


def test_socia_update_email_invalido_rechazado():
    """SociaUpdate con email inválido -> ValidationError (SOC-2)."""
    with pytest.raises(ValidationError):
        SocioConfiguracionUpdate(email="nope")


# ---------------------------------------------------------------------------
# ANT-1: Anticipo monto > 0
# ---------------------------------------------------------------------------


def test_anticipo_monto_positivo_aceptado():
    """anticipo monto > 0 -> aceptado (ANT-1)."""
    payload = AnticipoCreate(
        socia_id=2,
        monto=Decimal("50000"),
        fecha=date(2026, 7, 10),
    )
    assert payload.monto == Decimal("50000")
    assert payload.socia_id == 2


@pytest.mark.parametrize("monto", ["0", "-100"])
def test_anticipo_monto_no_positivo_rechazado(monto):
    """anticipo monto 0 o -100 -> ValidationError (ANT-1 -> 422)."""
    with pytest.raises(ValidationError):
        AnticipoCreate(socia_id=2, monto=Decimal(monto))


def test_anticipo_estado_invalido_rechazado():
    """AnticipoEstadoUpdate con estado fuera del Literal -> ValidationError (ANT-2)."""
    with pytest.raises(ValidationError):
        AnticipoEstadoUpdate(estado="CANCELADO")


def test_anticipo_estado_valido_aceptado():
    """AnticipoEstadoUpdate con estado válido -> aceptado (ANT-2)."""
    payload = AnticipoEstadoUpdate(estado="ANULADO")
    assert payload.estado == "ANULADO"


# ---------------------------------------------------------------------------
# LIQ-1/LIQ-2: Liquidacion totals + estado Literal
# ---------------------------------------------------------------------------


def test_liquidacion_create_totals_aceptado():
    """LiquidacionCreate con los 6 totals -> aceptado (LIQ-1)."""
    payload = LiquidacionCreate(**_liquidacion_payload())
    assert payload.utilidad_neta_total == Decimal("100000")
    assert payload.utilidad_repartible == Decimal("60000")


def test_liquidacion_estado_invalido_rechazado():
    """LiquidacionEstadoUpdate con estado no-Literal -> ValidationError (LIQ-2)."""
    with pytest.raises(ValidationError):
        LiquidacionEstadoUpdate(estado="CANCELADA")


def test_liquidacion_estado_valido_aceptado():
    """LiquidacionEstadoUpdate con APROBADA -> aceptado (LIQ-2)."""
    payload = LiquidacionEstadoUpdate(estado="APROBADA")
    assert payload.estado == "APROBADA"
