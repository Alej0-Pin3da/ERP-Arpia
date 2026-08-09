"""Finanzas engine tests — strict TDD (slice 2, task 2.4).

Exercises the finanzas service against the real test PostgreSQL:
- FIN-1: MovimientoFinanciero create / list(activo) / soft delete; one-time
  proportional settlement (liquidacion_id) -> per-socio Retiro rows, replay
  with the same id -> 409.
- FIN-2: SociosConfiguracion sum-to-100 boundary (exact 100 passes on create;
  99/101 rejected on create; never exceed 100 on update), interim rebalance
  below 100 allowed on update/delete while another socio completes, and delete
  blocked with 409 when the socio already has payouts (Movimientos).

Setup mirrors the other engine test files: uuid4-unique names, direct model
setup against SessionLocal, FK-ordered cleanup (movimientos before socios).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.db.session import SessionLocal
from app.models import MovimientoFinanciero, SociosConfiguracion
from app.services.finanzas import (
    actualizar_movimiento,
    actualizar_socio_configuracion,
    crear_movimiento,
    crear_socio_configuracion,
    eliminar_movimiento,
    eliminar_socio_configuracion,
    settle_liquidacion,
    listar_movimientos,
)


def _unique() -> str:
    return uuid.uuid4().hex[:12]


@pytest.fixture(scope="module", autouse=True)
def _finanzas_tablas_limpias():
    """The sum-to-100 invariant is global, so the shared test DB must start the
    module with no partner rows or movements (any leftover from a failed run
    would break the boundary assertions deterministically)."""
    db = SessionLocal()
    try:
        db.query(MovimientoFinanciero).delete()
        db.query(SociosConfiguracion).delete()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _movimiento_payload(
    tipo: str = "Gasto",
    descripcion: str | None = None,
    monto: str = "10",
    socio_id: int | None = None,
) -> dict:
    return {
        "tipo": tipo,
        "descripcion": descripcion or f"Movimiento {_unique()}",
        "monto": Decimal(monto),
        "socio_id": socio_id,
    }


def _socios_60_40() -> tuple[int, int]:
    """Two socios totalling exactly 100 via the service (interim update first)."""
    db = SessionLocal()
    try:
        a_id = crear_socio_configuracion(db, f"Socio A {_unique()}", Decimal("100")).id
        actualizar_socio_configuracion(db, a_id, Decimal("60"))
        b_id = crear_socio_configuracion(db, f"Socio B {_unique()}", Decimal("40")).id
        return a_id, b_id
    finally:
        db.close()


def _cleanup_movimientos(mov_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        db.query(MovimientoFinanciero).filter(
            MovimientoFinanciero.id.in_(mov_ids)
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _cleanup_movimientos_por_liquidacion(liquidacion_key: str) -> None:
    db = SessionLocal()
    try:
        db.query(MovimientoFinanciero).filter(
            MovimientoFinanciero.liquidacion_id.like(f"{liquidacion_key[:10]}%")
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _cleanup_socios(socio_ids: list[int]) -> None:
    db = SessionLocal()
    try:
        db.query(SociosConfiguracion).filter(
            SociosConfiguracion.id.in_(socio_ids)
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# FIN-1: MovimientoFinanciero CRUD
# ---------------------------------------------------------------------------


def test_crear_movimiento_persiste_con_monto_decimal():
    """POST válido -> fila persistida, monto como Decimal, estado 'activo'."""
    db = SessionLocal()
    try:
        mov = crear_movimiento(db, _movimiento_payload(monto="123.4500"))
        mov_id = mov.id
    finally:
        db.close()
    assert mov.tipo == "Gasto"
    assert mov.monto == Decimal("123.4500")
    assert mov.estado == "activo"
    assert mov.socio_id is None
    _cleanup_movimientos([mov_id])


def test_crear_movimiento_socio_inexistente_400():
    """socio_id que no existe -> 400 y nada se persiste."""
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as excinfo:
            crear_movimiento(db, _movimiento_payload(socio_id=99999999))
    finally:
        db.rollback()
        db.close()
    assert excinfo.value.status_code == 400


def test_listar_movimientos_filtra_por_estado_activo():
    """list_movimientos devuelve solo los 'activo'; los eliminados no salen."""
    db = SessionLocal()
    try:
        m1 = crear_movimiento(db, _movimiento_payload())
        m2 = crear_movimiento(db, _movimiento_payload(tipo="Inversion"))
        eliminar_movimiento(db, m1.id)
        activos = listar_movimientos(db)
        ids = [m.id for m in activos]
        assert m1.id not in ids  # soft-deleted
        assert m2.id in ids
        _cleanup_movimientos([m1.id, m2.id])
    finally:
        db.close()


def test_eliminar_movimiento_soft_delete_y_404():
    """Eliminar marca estado='inactivo' (soft); id inexistente -> 404."""
    db = SessionLocal()
    try:
        mov = crear_movimiento(db, _movimiento_payload())
        eliminado = eliminar_movimiento(db, mov.id)
        assert eliminado.estado == "inactivo"
        with pytest.raises(HTTPException) as excinfo:
            eliminar_movimiento(db, 99999999)
        assert excinfo.value.status_code == 404
        _cleanup_movimientos([mov.id])
    finally:
        db.close()


def test_settle_liquidacion_reparto_proporcional():
    """Settle 1000 con socios 60/40 -> dos Retiro (600 y 400) con ids derivados
    de la MISMA clave de liquidación (FIN-1 one-time settlement)."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            movs = settle_liquidacion(db, Decimal("1000"), notas="Utilidades Q1")
            key = movs[0].liquidacion_id[:10]
        finally:
            db.close()
        assert len(movs) == 2
        assert all(m.tipo == "Retiro" for m in movs)
        assert all(m.estado == "activo" for m in movs)
        # misma clave de liquidación, ids por fila únicos (uq_liquidacion)
        assert all(m.liquidacion_id[:10] == key for m in movs)
        assert len({m.liquidacion_id for m in movs}) == 2
        por_socio = {m.socio_id: m.monto for m in movs}
        assert por_socio[a_id] == Decimal("600.0000")  # 1000 * 60 / 100
        assert por_socio[b_id] == Decimal("400.0000")  # 1000 * 40 / 100
        assert sum(por_socio.values()) == Decimal("1000.0000")
        _cleanup_movimientos_por_liquidacion(key)
    finally:
        _cleanup_socios([a_id, b_id])


def test_settle_liquidacion_replay_mismo_id_409():
    """Misma clave de liquidación reutilizada -> 409 y sin filas duplicadas."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            movs = settle_liquidacion(db, Decimal("500"), liquidacion_id="LIQ-AB12CD")
        finally:
            db.close()
        assert all(m.liquidacion_id.startswith("LIQ-AB12CD") for m in movs)
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                settle_liquidacion(db, Decimal("500"), liquidacion_id="LIQ-AB12CD")
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        db = SessionLocal()
        try:
            count = (
                db.query(MovimientoFinanciero)
                .filter(MovimientoFinanciero.liquidacion_id.like("LIQ-AB12CD%"))
                .count()
            )
        finally:
            db.close()
        assert count == 2  # no duplicadas
        _cleanup_movimientos_por_liquidacion("LIQ-AB12CD")
    finally:
        _cleanup_socios([a_id, b_id])


# ---------------------------------------------------------------------------
# FIN-2: SociosConfiguracion — sum-to-100 boundary
# ---------------------------------------------------------------------------


def test_socio_crear_suma_exacta_100_pasa():
    """Primer socio con 100 -> persiste (boundary exact)."""
    db = SessionLocal()
    try:
        s_id = crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("100")).id
    finally:
        db.close()
    db = SessionLocal()
    try:
        row = db.get(SociosConfiguracion, s_id)
        assert row is not None
        assert row.porcentaje_participacion == Decimal("100")
    finally:
        db.close()
    _cleanup_socios([s_id])


def test_socio_crear_suma_99_422():
    """Crear socio dejando la suma global en 99 -> 422 y sin fila (boundary)."""
    db = SessionLocal()
    try:
        a_id = crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("100")).id
        actualizar_socio_configuracion(db, a_id, Decimal("60"))  # interim < 100 ok
        with pytest.raises(HTTPException) as excinfo:
            crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("39"))
    finally:
        db.rollback()
        db.close()
    assert excinfo.value.status_code == 422
    _cleanup_socios([a_id])


def test_socio_crear_suma_101_422():
    """Crear socio dejando la suma global en 101 -> 422 y sin fila (boundary)."""
    db = SessionLocal()
    try:
        a_id = crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("100")).id
        actualizar_socio_configuracion(db, a_id, Decimal("60"))  # interim < 100 ok
        with pytest.raises(HTTPException) as excinfo:
            crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("41"))
    finally:
        db.rollback()
        db.close()
    assert excinfo.value.status_code == 422
    _cleanup_socios([a_id])


def test_socio_actualizar_no_excede_100_pero_permite_interino():
    """Update que supera 100 -> 422; update interino < 100 permitido (rebalse)."""
    db = SessionLocal()
    try:
        a_id = crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("100")).id
        actualizar_socio_configuracion(db, a_id, Decimal("60"))
        b_id = crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("40")).id
        # B al 41 -> 101 -> 422
        with pytest.raises(HTTPException) as excinfo:
            actualizar_socio_configuracion(db, b_id, Decimal("41"))
        assert excinfo.value.status_code == 422
        # B al 30 -> 90 -> interino permitido (otro socio completará)
        actualizar_socio_configuracion(db, b_id, Decimal("30"))
        _cleanup_socios([a_id, b_id])
    finally:
        db.close()


def test_socio_rebalanceo_interino_ciclo_completo():
    """Ciclo: 100 -> update 60 (interino) -> crear 40 (suma 100) -> eliminar
    (vuelve a 60) -> update 100 (suma 100): todo permitido (FIN-2)."""
    db = SessionLocal()
    try:
        a_id = crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("100")).id
        actualizar_socio_configuracion(db, a_id, Decimal("60"))  # interino < 100
        b_id = crear_socio_configuracion(db, f"Socio {_unique()}", Decimal("40")).id
        eliminar_socio_configuracion(db, b_id)  # sin movimientos -> permitido
        actualizar_socio_configuracion(db, a_id, Decimal("100"))  # suma 100 de nuevo
        _cleanup_socios([a_id])
    finally:
        db.close()


def test_socio_eliminar_bloqueado_con_movimiento_409():
    """Socio con payout (Movimiento) -> DELETE 409 (FIN-2)."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            crear_movimiento(
                db, _movimiento_payload(tipo="Retiro", monto="50", socio_id=a_id)
            )
        finally:
            db.close()
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                eliminar_socio_configuracion(db, a_id)
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        db = SessionLocal()
        try:
            mov_ids = [
                m.id
                for m in db.query(MovimientoFinanciero)
                .filter(MovimientoFinanciero.socio_id == a_id)
                .all()
            ]
        finally:
            db.close()
        _cleanup_movimientos(mov_ids)
    finally:
        _cleanup_socios([a_id, b_id])


def test_socio_eliminar_sin_movimientos_ok():
    """Socio sin Movimientos -> DELETE procede (FIN-2)."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            eliminar_socio_configuracion(db, b_id)
        finally:
            db.close()
        db = SessionLocal()
        try:
            assert db.get(SociosConfiguracion, b_id) is None
        finally:
            db.close()
    finally:
        _cleanup_socios([a_id])


# ---------------------------------------------------------------------------
# FIN-1: actualizar_movimiento (T3 — PATCH /finanzas/movimientos/{id})
# ---------------------------------------------------------------------------


def test_actualizar_movimiento_aplica_campos_parciales():
    """PATCH parcial aplica SOLO los campos enviados (fecha/tipo/descripcion/
    monto/socio_id) y deja el resto intacto (FIN-1 PATCH)."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            mov = crear_movimiento(db, _movimiento_payload(tipo="Gasto", monto="10"))
            mov_id = mov.id
        finally:
            db.close()
        db = SessionLocal()
        try:
            actualizado = actualizar_movimiento(
                db,
                mov_id,
                {"descripcion": "Nueva descripcion", "monto": Decimal("25.50"), "socio_id": a_id},
            )
        finally:
            db.close()
        assert actualizado.descripcion == "Nueva descripcion"
        assert actualizado.monto == Decimal("25.5000")
        assert actualizado.socio_id == a_id
        assert actualizado.tipo == "Gasto"  # no enviado -> intacto
        assert actualizado.estado == "activo"
        _cleanup_movimientos([mov_id])
    finally:
        _cleanup_socios([a_id, b_id])


def test_actualizar_movimiento_cambia_fecha_y_tipo():
    """fecha y tipo son editables en un movimiento normal (FIN-1)."""
    db = SessionLocal()
    try:
        mov = crear_movimiento(db, _movimiento_payload(tipo="Gasto"))
        mov_id = mov.id
    finally:
        db.close()
    nueva_fecha = datetime(2026, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
    db = SessionLocal()
    try:
        actualizado = actualizar_movimiento(
            db, mov_id, {"fecha": nueva_fecha, "tipo": "Retiro"}
        )
    finally:
        db.close()
    assert actualizado.fecha.replace(tzinfo=None) == nueva_fecha.replace(tzinfo=None)
    assert actualizado.tipo == "Retiro"
    _cleanup_movimientos([mov_id])


def test_actualizar_movimiento_payload_vacio_ok():
    """Payload vacío -> 200 sin cambios (no-op aceptado, FIN-1)."""
    db = SessionLocal()
    try:
        mov = crear_movimiento(db, _movimiento_payload())
        mov_id = mov.id
        original = (mov.tipo, mov.descripcion, mov.monto, mov.socio_id)
    finally:
        db.close()
    db = SessionLocal()
    try:
        actualizado = actualizar_movimiento(db, mov_id, {})
    finally:
        db.close()
    assert (actualizado.tipo, actualizado.descripcion, actualizado.monto, actualizado.socio_id) == original
    _cleanup_movimientos([mov_id])


def test_actualizar_movimiento_404_inexistente():
    """id inexistente -> 404 (FIN-1)."""
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as excinfo:
            actualizar_movimiento(db, 99999999, {"descripcion": "x"})
    finally:
        db.rollback()
        db.close()
    assert excinfo.value.status_code == 404


def test_actualizar_movimiento_404_inactivo():
    """Soft-deleted (estado='inactivo') -> 404 (FIN-1)."""
    db = SessionLocal()
    try:
        mov = crear_movimiento(db, _movimiento_payload())
        mov_id = mov.id
        eliminar_movimiento(db, mov_id)
    finally:
        db.close()
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as excinfo:
            actualizar_movimiento(db, mov_id, {"descripcion": "x"})
    finally:
        db.rollback()
        db.close()
    assert excinfo.value.status_code == 404
    _cleanup_movimientos([mov_id])


def test_actualizar_movimiento_socio_inexistente_400():
    """socio_id que no existe -> 400 y nada se persiste (FIN-1)."""
    db = SessionLocal()
    try:
        mov = crear_movimiento(db, _movimiento_payload())
        mov_id = mov.id
    finally:
        db.close()
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as excinfo:
            actualizar_movimiento(db, mov_id, {"socio_id": 99999999})
    finally:
        db.rollback()
        db.close()
    assert excinfo.value.status_code == 400
    _cleanup_movimientos([mov_id])


def test_actualizar_movimiento_liquidacion_monto_422():
    """Fila de liquidación (liquidacion_id NOT NULL) + monto -> 422 y sin
    persistencia (FIN-2 server-side guard)."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            movs = settle_liquidacion(db, Decimal("1000"), liquidacion_id="LIQ-UPD01")
            mov_id = movs[0].id
            monto_original = movs[0].monto
            key = movs[0].liquidacion_id[:10]
        finally:
            db.close()
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                actualizar_movimiento(db, mov_id, {"monto": Decimal("9999")})
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 422
        db = SessionLocal()
        try:
            row = db.get(MovimientoFinanciero, mov_id)
            assert row.monto == monto_original  # sin cambios
        finally:
            db.close()
        _cleanup_movimientos_por_liquidacion(key)
    finally:
        _cleanup_socios([a_id, b_id])


def test_actualizar_movimiento_liquidacion_socio_422():
    """Fila de liquidación + socio_id -> 422 (FIN-2 server-side guard)."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            movs = settle_liquidacion(db, Decimal("1000"), liquidacion_id="LIQ-UPD02")
            mov_id = movs[0].id
            socio_original = movs[0].socio_id
            key = movs[0].liquidacion_id[:10]
        finally:
            db.close()
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                actualizar_movimiento(db, mov_id, {"socio_id": a_id})
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 422
        db = SessionLocal()
        try:
            row = db.get(MovimientoFinanciero, mov_id)
            assert row.socio_id == socio_original  # sin cambios
        finally:
            db.close()
        _cleanup_movimientos_por_liquidacion(key)
    finally:
        _cleanup_socios([a_id, b_id])


def test_actualizar_movimiento_liquidacion_descripcion_ok():
    """Fila de liquidación + solo descripcion -> 200; monto y liquidacion_id
    intactos (FIN-2: fecha/descripcion/tipo SÍ editables)."""
    a_id, b_id = _socios_60_40()
    try:
        db = SessionLocal()
        try:
            movs = settle_liquidacion(db, Decimal("1000"), liquidacion_id="LIQ-UPD03")
            mov_id = movs[0].id
            monto_original = movs[0].monto
            key = movs[0].liquidacion_id[:10]
        finally:
            db.close()
        db = SessionLocal()
        try:
            actualizado = actualizar_movimiento(
                db, mov_id, {"descripcion": "Nota corregida"}
            )
        finally:
            db.close()
        assert actualizado.descripcion == "Nota corregida"
        assert actualizado.monto == monto_original
        assert actualizado.liquidacion_id is not None
        _cleanup_movimientos_por_liquidacion(key)
    finally:
        _cleanup_socios([a_id, b_id])
