"""WAC cost engine tests — strict TDD (slice 1).

Exercises the engine contract from the wac-engine spec:
atomic commit, all-or-nothing rollback, weighted-average formula scenarios,
row locking concurrency (parallel serialization + no lost update), and precision.

The service is exercised directly against the real test PostgreSQL (per-thread
SessionLocal for concurrency), matching the design's service-level test strategy.
"""

import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import CategoriaInsumo, CompraInsumo, Insumo, Proveedor
from app.services.wac import registrar_compra


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def proveedor_id_fixture():
    db = SessionLocal()
    try:
        proveedor = Proveedor(nombre="Proveedor WAC de Pruebas")
        db.add(proveedor)
        db.commit()
        db.refresh(proveedor)
        yield proveedor.id
    finally:
        db.close()


def _cleanup_insumo(insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(CompraInsumo).filter(CompraInsumo.insumo_id == insumo_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.commit()
    finally:
        db.close()


def _make_insumo(
    categoria_id: int,
    stock: str | int | Decimal = "0",
    costo: str | int | Decimal = "0",
) -> int:
    db = SessionLocal()
    try:
        insumo = Insumo(
            categoria_id=categoria_id,
            nombre=f"Insumo WAC {id(object())}",
            unidad_medida="metro",
            stock_actual=Decimal(str(stock)),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal(str(costo)),
        )
        db.add(insumo)
        db.commit()
        db.refresh(insumo)
        return insumo.id
    finally:
        db.close()


def _read_inventory(insumo_id: int) -> tuple[Decimal, Decimal]:
    db = SessionLocal()
    try:
        insumo = db.get(Insumo, insumo_id)
        assert insumo is not None, "Insumo no encontrado"
        return insumo.stock_actual, insumo.costo_promedio_actual
    finally:
        db.close()


def _purchase_count(insumo_id: int) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(CompraInsumo).filter(CompraInsumo.insumo_id == insumo_id).count()
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Requirement: Atomic WAC in the purchase transaction
# ---------------------------------------------------------------------------


def test_purchase_atomic_write_commits_stock_and_cost(categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            compra = registrar_compra(
                db,
                insumo_id=insumo_id,
                proveedor_id=None,
                cantidad="10",
                precio_unitario="9",
            )
        finally:
            db.close()

        stock, costo = _read_inventory(insumo_id)
        assert compra.insumo_id == insumo_id
        assert compra.cantidad_comprada == Decimal("10")
        assert compra.precio_unitario_compra == Decimal("9")
        assert stock == Decimal("20")
        assert costo == Decimal("7")
    finally:
        _cleanup_insumo(insumo_id)


def test_rollback_on_error_leaves_unmodified(categoria_fixture):
    """A rejected purchase (proveedor inexistente -> 400) writes nothing."""
    insumo_id = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as exc_info:
                registrar_compra(
                    db,
                    insumo_id=insumo_id,
                    proveedor_id=99999999,
                    cantidad="10",
                    precio_unitario="9",
                )
        finally:
            db.close()
        assert exc_info.value.status_code == 400
        stock, costo = _read_inventory(insumo_id)
        assert stock == Decimal("10")
        assert costo == Decimal("5")
        assert _purchase_count(insumo_id) == 0
    finally:
        _cleanup_insumo(insumo_id)


def test_purchase_with_valid_proveedor_commits(categoria_fixture, proveedor_id_fixture):
    ins = _make_insumo(categoria_fixture["id"], stock="0", costo="0")
    try:
        db = SessionLocal()
        try:
            compra = registrar_compra(
                db,
                insumo_id=ins,
                proveedor_id=proveedor_id_fixture,
                cantidad="10",
                precio_unitario="9",
            )
        finally:
            db.close()
        assert compra.proveedor_id == proveedor_id_fixture
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("10")
        assert costo == Decimal("9")
    finally:
        _cleanup_insumo(ins)


# ---------------------------------------------------------------------------
# Requirement: Weighted-average cost formula
# ---------------------------------------------------------------------------


def test_wac_equal_prices_keeps_cost_stable(categoria_fixture):
    insumo_id = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            registrar_compra(
                db, insumo_id=insumo_id, proveedor_id=None, cantidad="10", precio_unitario="5"
            )
        finally:
            db.close()
        stock, costo = _read_inventory(insumo_id)
        assert stock == Decimal("20")
        assert costo == Decimal("5")
    finally:
        _cleanup_insumo(insumo_id)


def test_wac_price_fluctuation_moves_average(categoria_fixture):
    ins = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            registrar_compra(
                db, insumo_id=ins, proveedor_id=None, cantidad="10", precio_unitario="9"
            )
        finally:
            db.close()
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("20")
        assert costo == Decimal("7")
    finally:
        _cleanup_insumo(ins)


def test_wac_higher_priced_lot_raises_cost(categoria_fixture):
    ins = _make_insumo(categoria_fixture["id"], stock="100", costo="5")
    try:
        db = SessionLocal()
        try:
            registrar_compra(
                db, insumo_id=ins, proveedor_id=None, cantidad="50", precio_unitario="8"
            )
        finally:
            db.close()
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("150")
        assert costo == Decimal("6")
    finally:
        _cleanup_insumo(ins)


def test_wac_zero_stock_yields_unit_price(categoria_fixture):
    ins = _make_insumo(categoria_fixture["id"], stock="0", costo="0")
    try:
        db = SessionLocal()
        try:
            registrar_compra(
                db, insumo_id=ins, proveedor_id=None, cantidad="20", precio_unitario="7"
            )
        finally:
            db.close()
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("20")
        assert costo == Decimal("7")
    finally:
        _cleanup_insumo(ins)


# ---------------------------------------------------------------------------
# Requirement: Edge cases and precision
# ---------------------------------------------------------------------------


def test_wac_precision_no_engine_rounding(categoria_fixture):
    # (10 * 3 + 3 * 4) / (10 + 3) = 42 / 13 = 3.2307692307... -> NUMERIC(15,4) a 3.2308
    ins = _make_insumo(categoria_fixture["id"], stock="10", costo="3")
    try:
        db = SessionLocal()
        try:
            registrar_compra(
                db, insumo_id=ins, proveedor_id=None, cantidad="3", precio_unitario="4"
            )
        finally:
            db.close()
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("13")
        assert costo == Decimal("3.2308")
    finally:
        _cleanup_insumo(ins)


def test_integrity_error_maps_to_409(categoria_fixture, monkeypatch):
    """A DB constraint failure at commit surfaces as 409, not a 500 leak."""
    ins = _make_insumo(categoria_fixture["id"], stock="10", costo="5")

    # Shadow commit so the engine's single commit raises IntegrityError.
    def raising_commit(self):
        raise IntegrityError(
            "INSERT INTO Compras_Insumos ...",
            {},
            Exception("duplicate key value violates unique constraint"),
        )

    try:
        db = SessionLocal()
        try:
            monkeypatch.setattr(Session, "commit", raising_commit)
            with pytest.raises(HTTPException) as exc_info:
                registrar_compra(
                    db,
                    insumo_id=ins,
                    proveedor_id=None,
                    cantidad="10",
                    precio_unitario="9",
                )
        finally:
            monkeypatch.undo()
            db.rollback()
            db.close()
        assert exc_info.value.status_code == 409
        # All-or-nothing: nothing was persisted.
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("10")
        assert costo == Decimal("5")
        assert _purchase_count(ins) == 0
    finally:
        _cleanup_insumo(ins)


def test_nonexistent_insumo_returns_404(categoria_fixture):
    db = SessionLocal()
    with pytest.raises(HTTPException) as exc_info:
        try:
            registrar_compra(
                db, insumo_id=99999999, proveedor_id=None, cantidad="10", precio_unitario="9"
            )
        finally:
            db.close()
    assert exc_info.value.status_code == 404


def test_nonexistent_proveedor_returns_400(categoria_fixture):
    ins = _make_insumo(categoria_fixture["id"], stock="0", costo="0")
    try:
        db = SessionLocal()
        with pytest.raises(HTTPException) as exc_info:
            try:
                registrar_compra(
                    db, insumo_id=ins, proveedor_id=99999999, cantidad="10", precio_unitario="9"
                )
            finally:
                db.close()
        assert exc_info.value.status_code == 400
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("0")
        assert costo == Decimal("0")
    finally:
        _cleanup_insumo(ins)


# ---------------------------------------------------------------------------
# Requirement: Row locking for concurrency
# ---------------------------------------------------------------------------


def test_concurrent_purchases_same_insumo(categoria_fixture):
    """Two simultaneous purchases of one insumo serialize; no lost update."""
    ins = _make_insumo(categoria_fixture["id"], stock="0", costo="0")
    barrier = threading.Barrier(2)

    results: list[Exception | None] = [None, None]

    def purchase(insumo_id: int, cantidad: str, precio: str, slot: int):
        db = SessionLocal()
        try:
            barrier.wait(timeout=10)
            registrar_compra(
                db, insumo_id=insumo_id, proveedor_id=None, cantidad=cantidad, precio_unitario=precio
            )
        except Exception as exc:  # noqa: BLE001
            results[slot] = exc
        finally:
            db.close()

    t1 = threading.Thread(target=purchase, args=(ins, "10", "5", 0))
    t2 = threading.Thread(target=purchase, args=(ins, "10", "9", 1))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    assert results[0] is None, f"Thread 1 failed: {results[0]}"
    assert results[1] is None, f"Thread 2 failed: {results[1]}"

    # Serialized order (buy lot @5 first, then lot @9):
    #   after t1: stock 10, cost 5.0000
    #   after t2: (10*5 + 10*9) / 20 = 7.0000, stock 20
    stock, costo = _read_inventory(ins)
    assert stock == Decimal("20")
    assert costo == Decimal("7")
    assert _purchase_count(ins) == 2
    _cleanup_insumo(ins)


def test_different_insumos_run_in_parallel(categoria_fixture):
    ins_a = _make_insumo(categoria_fixture["id"], stock="5", costo="5")
    ins_b = _make_insumo(categoria_fixture["id"], stock="5", costo="5")
    barrier = threading.Barrier(2)

    def purchase(insumo_id: int, slot: int):
        db = SessionLocal()
        try:
            barrier.wait(timeout=10)
            registrar_compra(
                db, insumo_id=insumo_id, proveedor_id=None, cantidad="10", precio_unitario="9"
            )
        except Exception as exc:  # noqa: BLE001
            results[slot] = exc
        finally:
            db.close()

    results: list[Exception | None] = [None, None]
    t1 = threading.Thread(target=purchase, args=(ins_a, 0))
    t2 = threading.Thread(target=purchase, args=(ins_b, 1))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    assert results[0] is None, f"Thread 1 failed: {results[0]}"
    assert results[1] is None, f"Thread 2 failed: {results[1]}"
    # Both should have committed independently. Different insumos -> no blocking.
    stock_a, cost_a = _read_inventory(ins_a)
    stock_b, cost_b = _read_inventory(ins_b)
    assert stock_a == Decimal("15")
    assert stock_b == Decimal("15")
    # (5*5 + 10*9) / 15 = 115/15 = 7.6667
    assert cost_a == Decimal("7.6667") and cost_b == Decimal("7.6667")
    _cleanup_insumo(ins_a)
    _cleanup_insumo(ins_b)


# ---------------------------------------------------------------------------
# Requirement: fecha_compra opcional + commit controlado (migracion slice 2)
# ---------------------------------------------------------------------------


def _read_compra_fecha(compra_id: int) -> datetime | None:
    db = SessionLocal()
    try:
        compra = db.get(CompraInsumo, compra_id)
        return compra.fecha_compra if compra else None
    finally:
        db.close()


def test_compra_fecha_explicita_persistida(categoria_fixture):
    """fecha_compra aware explícita -> se persiste esa fecha (TIMESTAMPTZ)."""
    ins = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            fecha = datetime(2025, 10, 25, 14, 30, 0, tzinfo=timezone.utc)
            compra = registrar_compra(
                db,
                insumo_id=ins,
                proveedor_id=None,
                cantidad="10",
                precio_unitario="9",
                fecha_compra=fecha,
            )
        finally:
            db.close()
        persistida = _read_compra_fecha(compra.id)
        assert persistida is not None
        assert persistida.astimezone(timezone.utc) == fecha
        # La fecha NO participa en la formula WAC: stock/costo identicos.
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("20")
        assert costo == Decimal("7")
    finally:
        _cleanup_insumo(ins)


def test_compra_fecha_none_usa_server_default(categoria_fixture):
    """fecha_compra=None (omision) -> server_default now(), comportamiento intacto."""
    ins = _make_insumo(categoria_fixture["id"], stock="0", costo="0")
    try:
        antes = datetime.now(timezone.utc)
        db = SessionLocal()
        try:
            compra = registrar_compra(
                db,
                insumo_id=ins,
                proveedor_id=None,
                cantidad="10",
                precio_unitario="9",
                fecha_compra=None,
            )
        finally:
            db.close()
        despues = datetime.now(timezone.utc) + timedelta(seconds=5)
        persistida = _read_compra_fecha(compra.id)
        assert persistida is not None
        assert persistida.astimezone(timezone.utc) >= antes.astimezone(timezone.utc)
        assert persistida.astimezone(timezone.utc) <= despues.astimezone(timezone.utc)
    finally:
        _cleanup_insumo(ins)


def test_compra_fecha_naive_rechazada(categoria_fixture):
    """fecha_compra naive (sin zona) -> TypeError claro; nada se persiste."""
    ins = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(TypeError, match="aware"):
                registrar_compra(
                    db,
                    insumo_id=ins,
                    proveedor_id=None,
                    cantidad="10",
                    precio_unitario="9",
                    fecha_compra=datetime(2025, 10, 25, 14, 30, 0),  # naive
                )
        finally:
            db.close()
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("10")
        assert costo == Decimal("5")
        assert _purchase_count(ins) == 0
    finally:
        _cleanup_insumo(ins)


def test_commit_false_rollback_deja_sin_efecto(categoria_fixture):
    """commit=False -> el service NO commitea; rollback del caller anula todo."""
    ins = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            registrar_compra(
                db,
                insumo_id=ins,
                proveedor_id=None,
                cantidad="10",
                precio_unitario="9",
                fecha_compra=datetime(2025, 10, 25, tzinfo=timezone.utc),
                commit=False,
            )
        finally:
            db.rollback()
            db.close()
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("10")
        assert costo == Decimal("5")
        assert _purchase_count(ins) == 0
    finally:
        _cleanup_insumo(ins)


def test_commit_false_transaccion_controlada_por_caller(categoria_fixture):
    """commit=False -> el caller decide: con commit() posterior SI persiste."""
    ins = _make_insumo(categoria_fixture["id"], stock="10", costo="5")
    try:
        db = SessionLocal()
        try:
            compra = registrar_compra(
                db,
                insumo_id=ins,
                proveedor_id=None,
                cantidad="10",
                precio_unitario="9",
                fecha_compra=datetime(2025, 10, 25, tzinfo=timezone.utc),
                commit=False,
            )
            db.commit()
            db.refresh(compra)
        finally:
            db.close()
        stock, costo = _read_inventory(ins)
        assert stock == Decimal("20")
        assert costo == Decimal("7")
        assert _purchase_count(ins) == 1
        persistida = _read_compra_fecha(compra.id)
        assert persistida is not None
        assert persistida.astimezone(timezone.utc) == datetime(
            2025, 10, 25, tzinfo=timezone.utc
        )
    finally:
        _cleanup_insumo(ins)