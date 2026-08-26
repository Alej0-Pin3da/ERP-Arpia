"""Finanzas v4 service tests — strict TDD (PR2, task 2.3 RED).

Exercises the new/extended service functions against the real test PostgreSQL:
- SOC-2: sum-to-100 over activo=true INCLUDING the fondo row (40+30+30=100 ok;
  pushing Margarita to 35 -> 105 -> 422); second active fondo rejected (422).
- LIQ-3: payload-as-source drift>5% vs sum of Movimientos_Financieros for the
  period -> warning included but STILL persisted (no hard reject).
- LIQ-1/LIQ-2: real liquidacion header+distribution creation with generated
  codigo LIQ-YYYY-NN, FSM BORRADOR->APROBADA->PAGADA, and the state machine.

These tests reference new service functions and new fields that do NOT exist
yet in ``app.services.finanzas``, so they fail (RED) until task 2.4 (GREEN).
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.db.session import SessionLocal
from app.models import Anticipo, Liquidacion, MovimientoFinanciero, SociosConfiguracion
from app.services.finanzas import (
    crear_anticipo,
    crear_liquidacion,
    crear_socia_configuracion,
    transicionar_liquidacion,
)


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _cleanup_socios(socio_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        db.query(SociosConfiguracion).filter(SociosConfiguracion.id.in_(socio_ids)).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def _crear_socia(db, nombre: str, porcentaje: str, *, es_fondo=False, activo=True) -> int:
    """Direct row insert bypassing the service so the sum-to-100 invariant is
    built up deliberately (avoids the create-exact-100 boundary of FIN-2)."""
    socia = SociosConfiguracion(
        nombre=nombre,
        porcentaje_participacion=Decimal(porcentaje),
        es_fondo_taller=es_fondo,
        activo=activo,
    )
    db.add(socia)
    db.flush()
    return socia.id


def _montar_socias_40_30_30() -> list[int]:
    """Fondo 40 + Margarita 30 + Valqui 30 (all activo) = 100 (direct inserts)."""
    db = SessionLocal()
    ids = []
    try:
        ids.append(_crear_socia(db, f"Fondo {_unique()}", "40", es_fondo=True))
        ids.append(_crear_socia(db, f"Margarita {_unique()}", "30"))
        ids.append(_crear_socia(db, f"Valqui {_unique()}", "30"))
        db.commit()
    finally:
        db.close()
    return ids


@pytest.fixture(scope="module", autouse=True)
def _v4_tablas_limpias():
    db = SessionLocal()
    try:
        db.query(Anticipo).delete()
        db.query(Liquidacion).delete()
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
    finally:
        db.close()


def _liquidacion_payload(repartible="60000", neta="100000", ventas="150000", **over) -> dict:
    payload = {
        "periodo": f"2026-{_unique()[:2]}",
        "fecha_cierre": date(2026, 7, 31),
        "total_ventas_brutas": Decimal(ventas),
        "costo_taller_insumos": Decimal("30000"),
        "gastos_operativos": Decimal("20000"),
        "utilidad_neta_total": Decimal(neta),
        "fondo_reinversion_monto": Decimal("40000"),
        "utilidad_repartible": Decimal(repartible),
        "observaciones": None,
    }
    payload.update(over)
    return payload


def _limpiar_liquidaciones() -> None:
    db = SessionLocal()
    try:
        db.query(Anticipo).delete()
        db.query(Liquidacion).delete()
        db.query(MovimientoFinanciero).delete()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# SOC-2: sum-to-100 includes the fondo row
# ---------------------------------------------------------------------------


def test_socia_actualizar_no_supera_100_incluye_fondo_422():
    """Con activos Fondo40+Margarita30+Valqui30 (sum 100), subir Margarita a 35
    -> 105 -> 422; el fondo cuenta en la suma (SOC-2)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                # service-level partial update of Margarita (id 2) to 35
                from app.services.finanzas import actualizar_socia_configuracion

                actualizar_socia_configuracion(db, ids[1], {"porcentaje_participacion": Decimal("35")})
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 422
        assert "105" in excinfo.value.detail
    finally:
        _cleanup_socios(ids)


def test_socia_segundo_fondo_rechazado_422():
    """Un fondo activo ya existe -> crear otro es_fondo_taller=True -> 422 (SOC-2)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            from app.services.finanzas import crear_socia_configuracion

            with pytest.raises(HTTPException) as excinfo:
                crear_socia_configuracion(
                    db,
                    nombre=f"Fondo2 {_unique()}",
                    porcentaje=Decimal("10"),
                    es_fondo_taller=True,
                    activo=True,
                )
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 422
        assert "fondo" in excinfo.value.detail.lower()
    finally:
        _cleanup_socios(ids)


def test_socia_inactiva_excluida_de_la_suma():
    """Una socia activo=False no cuenta en la suma; crear un activo que la deja
    en 100 -> ok (SOC-2/SOC-3)."""
    ids = _montar_socias_40_30_30()  # 100 activos
    nueva_id = None
    try:
        db = SessionLocal()
        try:
            from app.services.finanzas import actualizar_socia_configuracion

            actualizar_socia_configuracion(db, ids[0], {"activo": False})
            # suma activa ahora = 30+30 = 60; nuevo socio de 40 la deja en 100
            nueva = crear_socia_configuracion(db, nombre=f"Nueva {_unique()}", porcentaje=Decimal("40"))
            nueva_id = nueva.id
            db.commit()
        finally:
            db.close()
        assert nueva_id is not None
        db = SessionLocal()
        try:
            row = db.get(SociosConfiguracion, nueva_id)
            assert row is not None
            assert row.porcentaje_participacion == Decimal("40")
        finally:
            db.close()
        _cleanup_socios([nueva_id])
    finally:
        _cleanup_socios(ids)


# ---------------------------------------------------------------------------
# LIQ-3: drift>5% warning persists
# ---------------------------------------------------------------------------


def test_liquidacion_drift_mayor_5_porciento_persiste_con_warning():
    """Movimientos suman 100000 pero el payload declara 120000 (>5%) -> el
    servicio PERSISTE 120000 e incluye warning 'drift' (LIQ-3, sin hard reject)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            # benchmark: sumar movimientos del periodo -> 100000
            for monto in ("40000", "60000"):
                db.add(
                    MovimientoFinanciero(
                        tipo="Gasto",
                        descripcion=f"mov {_unique()}",
                        monto=Decimal(monto),
                        estado="confirmed",
                    )
                )
            db.commit()
        finally:
            db.close()

        db = SessionLocal()
        try:
            # payload internamente consistente: 170000-30000-20000 = 120000,
            # pero la suma de movimientos del periodo es 100000 (>5% drift).
            liq, warnings = crear_liquidacion(
                db, _liquidacion_payload(neta="120000", ventas="170000")
            )
            db.commit()
            neta = liq.utilidad_neta_total
            warnings_list = list(warnings)
        finally:
            db.close()

        assert neta == Decimal("120000.00")
        assert any("drift" in w.lower() and "5" in w for w in warnings_list)
        _limpiar_liquidaciones()
    finally:
        _cleanup_socios(ids)


def test_liquidacion_sin_drift_no_warning():
    """Payload coincide con la suma de movimientos -> sin warning (LIQ-3)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            for monto in ("40000", "60000"):
                db.add(
                    MovimientoFinanciero(
                        tipo="Gasto",
                        descripcion=f"mov {_unique()}",
                        monto=Decimal(monto),
                        estado="confirmed",
                    )
                )
            db.commit()
        finally:
            db.close()

        db = SessionLocal()
        try:
            liq, warnings = crear_liquidacion(db, _liquidacion_payload(neta="100000"))
            db.commit()
            neta = liq.utilidad_neta_total
            warnings_list = list(warnings)
        finally:
            db.close()

        assert neta == Decimal("100000.00")
        assert not any("drift" in w.lower() for w in warnings_list)
        _limpiar_liquidaciones()
    finally:
        _cleanup_socios(ids)


# ---------------------------------------------------------------------------
# LIQ-1/LIQ-2: real liquidacion + FSM
# ---------------------------------------------------------------------------


def test_crear_liquidacion_genera_codigo_y_distribucion():
    """Crear liquidacion -> header con codigo LIQ-2026-NN y 3 filas de
    distribucion 40000/30000/30000 (LIQ-1)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            liq, warnings = crear_liquidacion(db, _liquidacion_payload(repartible="100000"))
            db.commit()
            codigo = liq.codigo
            n_rows = len(liq.distribucion)
            montos = sorted([Decimal(d.monto_bruto) for d in liq.distribucion])
        finally:
            db.close()
        assert codigo.startswith("LIQ-2026-")
        assert len(codigo.split("-")[-1]) == 2
        assert n_rows == 3
        assert montos == [Decimal("30000"), Decimal("30000"), Decimal("40000")]
        _limpiar_liquidaciones()
    finally:
        _cleanup_socios(ids)


def test_transicionar_liquidacion_fsm_ok_y_terminal():
    """BORRADOR->APROBADA->PAGADA -> 200; PAGADA (terminal) rechaza -> 422 (LIQ-2)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            liq, _ = crear_liquidacion(db, _liquidacion_payload())
            db.commit()
            liq_id = liq.id
        finally:
            db.close()
        db = SessionLocal()
        try:
            transicionar_liquidacion(db, liq_id, "APROBADA")
            db.commit()
        finally:
            db.close()
        db = SessionLocal()
        try:
            transicionar_liquidacion(db, liq_id, "PAGADA")
            db.commit()
        finally:
            db.close()
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                transicionar_liquidacion(db, liq_id, "BORRADOR")
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 422
        _limpiar_liquidaciones()
    finally:
        _cleanup_socios(ids)


def test_transicionar_liquidacion_saltar_estado_422():
    """BORRADOR->PAGADA directo -> 422 (LIQ-2 skip)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            liq, _ = crear_liquidacion(db, _liquidacion_payload())
            db.commit()
            liq_id = liq.id
        finally:
            db.close()
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                transicionar_liquidacion(db, liq_id, "PAGADA")
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 422
        _limpiar_liquidaciones()
    finally:
        _cleanup_socios(ids)


# ---------------------------------------------------------------------------
# ANT-1: anticipo create
# ---------------------------------------------------------------------------


def test_crear_anticipo_persiste():
    """Anticipo válido -> persiste con estado PENDIENTE_DESCUENTO (ANT-1)."""
    ids = _montar_socias_40_30_30()
    try:
        db = SessionLocal()
        try:
            a = crear_anticipo(
                db,
                socia_id=ids[1],
                monto=Decimal("50000"),
                fecha=date(2026, 7, 10),
            )
            db.commit()
            a_id = a.id
            a_estado = a.estado
            a_socia = a.socia_id
        finally:
            db.close()
        db = SessionLocal()
        try:
            row = db.get(Anticipo, a_id)
            assert row is not None
            assert row.estado == "PENDIENTE_DESCUENTO"
            assert row.socia_id == ids[1]
            assert a_estado == "PENDIENTE_DESCUENTO"
            assert a_socia == ids[1]
        finally:
            db.close()
        db = SessionLocal()
        try:
            db.query(Anticipo).filter(Anticipo.id == a_id).delete()
            db.commit()
        finally:
            db.close()
    finally:
        _cleanup_socios(ids)
