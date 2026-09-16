"""Venta schema finitude guards — pure unit tests (no DB).

DetalleVentaCreate/VentaCreate reject non-finite Decimals (NaN/Infinity)
at the API boundary (mirrors compra_insumo.py::_check_finite). The sale
routes build the service payload via ``payload.model_dump()``, so this one
schema gate covers both registrar_venta and actualizar_venta — no
duplicated service-layer check.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.venta import DetalleVentaCreate, VentaCreate

NO_FINITOS = [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")]


@pytest.mark.parametrize("malo", NO_FINITOS)
def test_detalle_cantidad_no_finita_rechazada(malo):
    with pytest.raises(ValidationError):
        DetalleVentaCreate(
            producto_id=1, cantidad=malo, precio_unitario=Decimal("10")
        )


@pytest.mark.parametrize("malo", NO_FINITOS)
def test_detalle_precio_no_finito_rechazado(malo):
    with pytest.raises(ValidationError):
        DetalleVentaCreate(
            producto_id=1, cantidad=Decimal("1"), precio_unitario=malo
        )


@pytest.mark.parametrize("malo", NO_FINITOS)
def test_venta_descuento_no_finito_rechazado(malo):
    with pytest.raises(ValidationError):
        VentaCreate(
            canal_venta="web",
            descuento_porcentaje=malo,
            detalles=[
                DetalleVentaCreate(
                    producto_id=1,
                    cantidad=Decimal("1"),
                    precio_unitario=Decimal("10"),
                )
            ],
        )


def test_venta_valores_finitos_aceptados():
    venta = VentaCreate(
        canal_venta="web",
        descuento_porcentaje=Decimal("10"),
        detalles=[
            DetalleVentaCreate(
                producto_id=1,
                cantidad=Decimal("2"),
                precio_unitario=Decimal("15.5"),
            )
        ],
    )
    assert venta.detalles[0].cantidad == Decimal("2")
