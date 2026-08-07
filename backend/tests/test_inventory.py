"""Inventory engine tests — strict TDD (PR 2 slice, tasks 2.1-2.11).

Exercises the inventory spec scenarios DRIVEN strictly by tests:
- explosion_materiales: single-level+waste, multilevel combo flatten, variant
  override vs base, missing-variant guard (400), cycle (409), read-only
  (no locks/commits, callable inside a FOR UPDATE txn).
- descontar_stock: FOR UPDATE, insufficient stock -> 409 with zero partial.
- registrar_venta: single commit, cost snapshot, atomic all-or-nothing across
  multiple lines, IntegrityError -> 409, concurrent serialization.

Uses the _unique() uuid4 helper, direct model setup against the real test
PostgreSQL via SessionLocal, and FK-ordered cleanup (ventas -> BOM -> variantes
-> productos -> insumos -> categorias -> tipos). Concurrency uses per-thread
SessionLocal + threading.Barrier + before_cursor_execute write counters.
"""

import threading
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models import (
    BomInsumo,
    BomProducto,
    CategoriaInsumo,
    Cliente,
    DetalleVenta,
    Insumo,
    Producto,
    TipoProducto,
    VarianteProducto,
    Venta,
)
from app.services.inventory import (
    descontar_stock,
    explosion_materiales,
    registrar_venta,
    reponer_stock,
)


def _unique() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# DB helpers (direct model setup with unique names; FK-ordered cleanup)
# ---------------------------------------------------------------------------


def _make_categoria() -> int:
    db = SessionLocal()
    try:
        categoria = CategoriaInsumo(nombre=f"Categoria {_unique()}")
        db.add(categoria)
        db.commit()
        db.refresh(categoria)
        return categoria.id
    finally:
        db.close()


def _make_insumo(
    categoria_id: int, costo: str = "0", stock: str = "0"
) -> int:
    db = SessionLocal()
    try:
        insumo = Insumo(
            categoria_id=categoria_id,
            nombre=f"Insumo {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal(stock),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal(costo),
        )
        db.add(insumo)
        db.commit()
        db.refresh(insumo)
        return insumo.id
    finally:
        db.close()


def _make_tipo() -> int:
    db = SessionLocal()
    try:
        tipo = TipoProducto(nombre=f"Tipo {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        return tipo.id
    finally:
        db.close()


def _make_producto(tipo_producto_id: int, fijos: str = "0") -> int:
    db = SessionLocal()
    try:
        producto = Producto(
            tipo_producto_id=tipo_producto_id,
            nombre=f"Producto {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal(fijos),
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto.id
    finally:
        db.close()


def _make_variante(producto_id: int) -> int:
    db = SessionLocal()
    try:
        variante = VarianteProducto(
            producto_id=producto_id, nombre_variante=f"Variante {_unique()}"
        )
        db.add(variante)
        db.commit()
        db.refresh(variante)
        return variante.id
    finally:
        db.close()


def _make_linea_insumo(
    producto_id: int,
    insumo_id: int,
    variante_id: int | None = None,
    cantidad: str = "1",
    desperdicio: str = "0",
) -> None:
    db = SessionLocal()
    try:
        db.add(
            BomInsumo(
                producto_id=producto_id,
                insumo_id=insumo_id,
                variante_id=variante_id,
                cantidad_requerida=Decimal(cantidad),
                porcentaje_desperdicio=Decimal(desperdicio),
            )
        )
        db.commit()
    finally:
        db.close()


def _make_linea_producto(combo_id: int, incluido_id: int, cantidad: str = "1") -> None:
    db = SessionLocal()
    try:
        db.add(
            BomProducto(
                combo_id=combo_id,
                producto_incluido_id=incluido_id,
                cantidad=Decimal(cantidad),
            )
        )
        db.commit()
    finally:
        db.close()


def _cleanup_insumo(insumo_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.insumo_id == insumo_id).delete()
        db.query(Insumo).filter(Insumo.id == insumo_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(BomInsumo).filter(BomInsumo.producto_id == producto_id).delete()
        db.query(BomProducto).filter(
            (BomProducto.combo_id == producto_id)
            | (BomProducto.producto_incluido_id == producto_id)
        ).delete(synchronize_session=False)
        db.query(VarianteProducto).filter(
            VarianteProducto.producto_id == producto_id
        ).delete()
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_tipo(tipo_id: int) -> None:
    db = SessionLocal()
    try:
        producto_ids = db.query(Producto.id).filter(Producto.tipo_producto_id == tipo_id)
        db.query(BomInsumo).filter(BomInsumo.producto_id.in_(producto_ids)).delete(
            synchronize_session=False
        )
        db.query(BomProducto).filter(
            (BomProducto.combo_id.in_(producto_ids))
            | (BomProducto.producto_incluido_id.in_(producto_ids))
        ).delete(synchronize_session=False)
        db.query(VarianteProducto).filter(
            VarianteProducto.producto_id.in_(producto_ids)
        ).delete(synchronize_session=False)
        db.query(Producto).filter(Producto.tipo_producto_id == tipo_id).delete(
            synchronize_session=False
        )
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_categoria(categoria_id: int) -> None:
    db = SessionLocal()
    try:
        insumo_ids = db.query(Insumo.id).filter(Insumo.categoria_id == categoria_id)
        db.query(BomInsumo).filter(BomInsumo.insumo_id.in_(insumo_ids)).delete(
            synchronize_session=False
        )
        db.query(Insumo).filter(Insumo.categoria_id == categoria_id).delete(
            synchronize_session=False
        )
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == categoria_id).delete()
        db.commit()
    finally:
        db.close()


def _read_stock(insumo_id: int) -> Decimal:
    db = SessionLocal()
    try:
        return db.get(Insumo, insumo_id).stock_actual
    finally:
        db.close()


def _make_cliente() -> int:
    db = SessionLocal()
    try:
        cliente = Cliente(nombre=f"Cliente {_unique()}")
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente.id
    finally:
        db.close()


def _cleanup_ventas_for_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = select(DetalleVenta.venta_id).where(
            DetalleVenta.producto_id == producto_id
        )
        db.query(Venta).filter(Venta.id.in_(ven_ids)).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def _cleanup_cliente(cliente_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(Cliente).filter(Cliente.id == cliente_id).delete()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2.1 explosion_materiales: single-level + waste
# ---------------------------------------------------------------------------


def test_explosion_single_level_insumo_waste():
    """Insumo qty 10, waste 20%, sale of 1 -> 12.0000 deducted (2.1)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id)
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="10", desperdicio="20")
    try:
        db = SessionLocal()
        try:
            result = explosion_materiales(db, producto_id, None, Decimal("1"))
        finally:
            db.close()
        assert result[insumo_id] == Decimal("12.0000")
        # triangulation: sale of 2 -> 24.0000 exercises the multiplier path
        db = SessionLocal()
        try:
            result2 = explosion_materiales(db, producto_id, None, Decimal("2"))
        finally:
            db.close()
        assert result2[insumo_id] == Decimal("24.0000")
    finally:
        _cleanup_producto(producto_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# 2.2 explosion_materiales: multilevel combo flatten
# ---------------------------------------------------------------------------


def test_explosion_multilevel_combo_flattens_to_child_insumo():
    """A -> B(combo qty 2) -> insumo(5): selling 1 A deducts 10, NOT B (2.2)."""
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id)
    b_id = _make_producto(tipo_id)
    _make_linea_producto(a_id, b_id, cantidad="2")
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id)
    _make_linea_insumo(b_id, insumo_id, cantidad="5")
    try:
        db = SessionLocal()
        try:
            result = explosion_materiales(db, a_id, None, Decimal("1"))
        finally:
            db.close()
        assert result[insumo_id] == Decimal("10.0000")  # 2 x 5
        assert b_id not in result  # child product itself is excluded
        assert len(result) == 1
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# 2.3 explosion_materiales: variant override vs base + missing-variant guard
# ---------------------------------------------------------------------------


def test_explosion_variant_overrides_base_not_sum():
    """Variant qty 2 vs base qty 1 -> 2.0000, base NOT summed (2.3)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id)
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    variante_id = _make_variante(producto_id)
    _make_linea_insumo(producto_id, insumo_id, variante_id=None, cantidad="1")
    _make_linea_insumo(producto_id, insumo_id, variante_id=variante_id, cantidad="2")
    try:
        db = SessionLocal()
        try:
            result = explosion_materiales(db, producto_id, variante_id, Decimal("1"))
        finally:
            db.close()
        assert result[insumo_id] == Decimal("2.0000")  # override, NOT 1 and NOT 3
    finally:
        _cleanup_producto(producto_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


def test_explosion_variant_product_without_variante_raises_400():
    """Product with variants sold without a variante_id -> 400 guard (2.3)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id)
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_variante(producto_id)
    _make_linea_insumo(producto_id, insumo_id, variante_id=None, cantidad="1")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                explosion_materiales(db, producto_id, None, Decimal("1"))
        finally:
            db.close()
        assert excinfo.value.status_code == 400
    finally:
        _cleanup_producto(producto_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# 2.4 explosion_materiales: cycle abort + read-only
# ---------------------------------------------------------------------------


def test_explosion_cycle_aborts_409():
    """A -> B -> A aborts with 409 and NO result (2.4)."""
    tipo_id = _make_tipo()
    a_id = _make_producto(tipo_id)
    b_id = _make_producto(tipo_id)
    _make_linea_producto(a_id, b_id, cantidad="1")
    _make_linea_producto(b_id, a_id, cantidad="1")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                explosion_materiales(db, a_id, None, Decimal("1"))
        finally:
            db.close()
        assert excinfo.value.status_code == 409
    finally:
        _cleanup_producto(a_id)
        _cleanup_producto(b_id)
        _cleanup_tipo(tipo_id)


def test_explosion_is_read_only_no_writes():
    """Explosion fires only SELECTs — no INSERT/UPDATE/DELETE/commit (2.4)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id)
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="1")
    holder = {"writes": 0}

    def _before(conn, cursor, statement, parameters, context, executemany):
        head = statement.lstrip()[:10].upper()
        if head.startswith(("INSERT", "UPDATE", "DELETE", "COMMIT", "ROLLBACK")):
            holder["writes"] += 1

    try:
        db = SessionLocal()
        event.listen(engine, "before_cursor_execute", _before)
        try:
            result = explosion_materiales(db, producto_id, None, Decimal("1"))
        finally:
            event.remove(engine, "before_cursor_execute", _before)
            db.close()
        assert result[insumo_id] == Decimal("1.0000")
        assert holder["writes"] == 0  # read-only traversal, no DB writes
    finally:
        _cleanup_producto(producto_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


def test_explosion_missing_producto_raises_404():
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as excinfo:
            explosion_materiales(db, 99999999, None, Decimal("1"))
    finally:
        db.close()
    assert excinfo.value.status_code == 404


# ---------------------------------------------------------------------------
# 2.7 descontar_stock: insufficient -> 409, no partial subtraction
# ---------------------------------------------------------------------------


def test_descontar_stock_insufficient_raises_409_no_change():
    """Demand 6 > stock 4 -> 409; stock untouched (2.7)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, stock="4")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                descontar_stock(db, {insumo_id: Decimal("6")})
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        assert _read_stock(insumo_id) == Decimal("4")
    finally:
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)


def test_descontar_stock_multiple_insumos_second_short_no_partial():
    """X OK, Y short -> raise before persisting; X NOT subtracted (2.7)."""
    categoria_id = _make_categoria()
    x_id = _make_insumo(categoria_id, stock="5")
    y_id = _make_insumo(categoria_id, stock="2")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                descontar_stock(db, {x_id: Decimal("1"), y_id: Decimal("3")})
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        assert _read_stock(x_id) == Decimal("5")  # not partially subtracted
    finally:
        _cleanup_insumo(x_id)
        _cleanup_insumo(y_id)
        _cleanup_categoria(categoria_id)


def test_descontar_stock_sufficient_subtracts():
    """Demand <= stock -> lock, subtract, and persist the update (2.8)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, stock="10")
    try:
        db = SessionLocal()
        try:
            descontar_stock(db, {insumo_id: Decimal("3")})
            db.commit()
        finally:
            db.close()
        assert _read_stock(insumo_id) == Decimal("7")
    finally:
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)


def test_registrar_venta_two_lines_second_short_rolls_back_all():
    """Two lines consume the same insumo; total demand exceeds stock -> 409 and
    NOTHING is subtracted or persisted (spec 'one line fails, none booked')."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="5", stock="5")
    tipo_id = _make_tipo()
    p1 = _make_producto(tipo_id)
    p2 = _make_producto(tipo_id)
    _make_linea_insumo(p1, insumo_id, cantidad="1")
    _make_linea_insumo(p2, insumo_id, cantidad="1")  # same insumo, shared demand
    payload = {
        "cliente_id": None,
        "canal_venta": "web",
        "descuento_porcentaje": Decimal("0"),
        "detalles": [
            {"producto_id": p1, "variante_id": None, "cantidad": Decimal("3"), "precio_unitario": Decimal("10")},
            {"producto_id": p2, "variante_id": None, "cantidad": Decimal("3"), "precio_unitario": Decimal("10")},
        ],
    }
    try:
        db = SessionLocal()
        try:
            ventas_before = db.query(Venta).count()
            with pytest.raises(HTTPException) as excinfo:
                registrar_venta(db, payload)
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        assert _read_stock(insumo_id) == Decimal("5")  # demand 6 > 5 -> untouched
        db = SessionLocal()
        try:
            assert db.query(Venta).count() == ventas_before  # no sale row persisted
        finally:
            db.close()
    finally:
        _cleanup_producto(p1)
        _cleanup_producto(p2)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# 2.9 registrar_venta: cost snapshot, single atomic commit
# ---------------------------------------------------------------------------


def _venta_payload(
    producto_id: int,
    cantidad: str = "1",
    variante_id: int | None = None,
    cliente_id: int | None = None,
) -> dict:
    return {
        "cliente_id": cliente_id,
        "canal_venta": "web",
        "descuento_porcentaje": Decimal("0"),
        "detalles": [
            {
                "producto_id": producto_id,
                "variante_id": variante_id,
                "cantidad": Decimal(cantidad),
                "precio_unitario": Decimal("10"),
            }
        ],
    }


def _read_venta(venta_id: int) -> tuple[Venta, list[DetalleVenta]]:
    db = SessionLocal()
    try:
        venta = db.get(Venta, venta_id)
        # eager-load child details before the session closes
        return venta, [d for d in venta.detalles]
    finally:
        db.close()


def test_registrar_venta_cost_snapshot_and_stock():
    """Cost snapshot = insumo.costo_promedio_actual (4-dec); stock deducted in
    the same single commit (2.9)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="5.1234", stock="10")
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="1", desperdicio="0")
    cliente_id = _make_cliente()
    try:
        db = SessionLocal()
        try:
            venta = registrar_venta(
                db, _venta_payload(producto_id, cantidad="1", cliente_id=cliente_id)
            )
        finally:
            db.close()
        venta, detalles = _read_venta(venta.id)
        assert detalles[0].costo_unitario_aplicado == Decimal("5.1234")
        assert detalles[0].cantidad == Decimal("1")
        assert venta.total_venta == Decimal("10.0000")  # 1 x 10, no descuento
        assert _read_stock(insumo_id) == Decimal("9")  # 1 unit deducted
    finally:
        _cleanup_ventas_for_producto(producto_id)
        _cleanup_cliente(cliente_id)
        _cleanup_producto(producto_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


def test_registrar_venta_commit_integrity_error_returns_409(monkeypatch):
    """A DB constraint failure at the single commit -> 409, nothing persisted (2.9)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="5", stock="10")
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="1")

    def raising_commit(self):
        raise IntegrityError(
            "INSERT INTO Ventas ...",
            {},
            Exception("duplicate key value violates unique constraint"),
        )

    try:
        db = SessionLocal()
        try:
            monkeypatch.setattr(Session, "commit", raising_commit)
            with pytest.raises(HTTPException) as excinfo:
                registrar_venta(db, _venta_payload(producto_id, cantidad="1"))
        finally:
            monkeypatch.undo()
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        # All-or-nothing: no stock change, no sale row persisted.
        assert _read_stock(insumo_id) == Decimal("10")
    finally:
        _cleanup_producto(producto_id)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)
        _cleanup_tipo(tipo_id)


# ---------------------------------------------------------------------------
# reponer_stock: inverse restock engine (S2.2)
# ---------------------------------------------------------------------------


def test_reponer_stock_adds_stock():
    """reponer_stock increments stock_actual by the explosion qty (S2.2)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, stock="10")
    try:
        db = SessionLocal()
        try:
            reponer_stock(db, {insumo_id: Decimal("3")})
            db.commit()
        finally:
            db.close()
        assert _read_stock(insumo_id) == Decimal("13")
    finally:
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)


def test_reponer_stock_multiple_insumos_increments_all():
    """Two insumos in one call -> BOTH incremented (triangulation, S2.2)."""
    categoria_id = _make_categoria()
    x_id = _make_insumo(categoria_id, stock="5")
    y_id = _make_insumo(categoria_id, stock="2")
    try:
        db = SessionLocal()
        try:
            reponer_stock(db, {x_id: Decimal("1"), y_id: Decimal("4")})
            db.commit()
        finally:
            db.close()
        assert _read_stock(x_id) == Decimal("6")
        assert _read_stock(y_id) == Decimal("6")
    finally:
        _cleanup_insumo(x_id)
        _cleanup_insumo(y_id)
        _cleanup_categoria(categoria_id)


def test_reponer_stock_unknown_insumo_raises_404():
    """Unknown insumo_id -> 404, mirrors descontar_stock (S2.2)."""
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as excinfo:
            reponer_stock(db, {99999999: Decimal("1")})
    finally:
        db.rollback()
        db.close()
    assert excinfo.value.status_code == 404


def test_reponer_stock_no_internal_commit():
    """Caller owns the txn: without commit a fresh session still sees the
    pre-call stock value (S2.2 mirrors descontar_stock's no-commit rule)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, stock="10")
    try:
        db = SessionLocal()
        try:
            reponer_stock(db, {insumo_id: Decimal("3")})
        finally:
            db.rollback()
            db.close()
        assert _read_stock(insumo_id) == Decimal("10")  # nothing persisted
    finally:
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria_id)


def test_reponer_stock_concurrent_restocks_serialize_no_lost_update():
    """Two parallel restocks of +2 on the same insumo -> final stock 14
    (10+2+2). Without FOR UPDATE + populate_existing both threads would read
    the stale 10 and both write 12 (lost update) (S2.2 FOR-UPDATE concurrency)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, stock="10")
    barrier = threading.Barrier(2)
    errors: list[Exception | None] = [None, None]

    def restock(slot: int):
        db = SessionLocal()
        try:
            barrier.wait(timeout=10)
            reponer_stock(db, {insumo_id: Decimal("2")})
            db.commit()
        except Exception as exc:  # noqa: BLE001
            errors[slot] = exc
        finally:
            db.close()

    t1 = threading.Thread(target=restock, args=(0,))
    t2 = threading.Thread(target=restock, args=(1,))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    assert errors[0] is None, f"Thread 1 failed: {errors[0]}"
    assert errors[1] is None, f"Thread 2 failed: {errors[1]}"
    assert _read_stock(insumo_id) == Decimal("14")
    _cleanup_insumo(insumo_id)
    _cleanup_categoria(categoria_id)


# ---------------------------------------------------------------------------
# 2.10 registrar_venta: concurrent sales serialize on the insumo row lock
# ---------------------------------------------------------------------------


def test_registrar_venta_concurrent_sales_serialize():
    """Stock 5, two parallel sales of 3 -> one succeeds, one 409, final stock 2 (2)."""
    categoria_id = _make_categoria()
    insumo_id = _make_insumo(categoria_id, costo="5", stock="5")
    tipo_id = _make_tipo()
    producto_id = _make_producto(tipo_id)
    _make_linea_insumo(producto_id, insumo_id, cantidad="1")
    barrier = threading.Barrier(2)
    outcomes: list[HTTPException | None] = [None, None]
    created: list[int | None] = [None, None]

    def sell(slot: int):
        db = SessionLocal()
        try:
            barrier.wait(timeout=10)
            venta = registrar_venta(db, _venta_payload(producto_id, cantidad="3"))
            created[slot] = venta.id
        except HTTPException as exc:  # expected: one serialized sale -> 409
            outcomes[slot] = exc
        finally:
            db.close()

    t1 = threading.Thread(target=sell, args=(0,))
    t2 = threading.Thread(target=sell, args=(1,))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    ok_count = sum(1 for v in created if v is not None)
    blocked_count = sum(1 for o in outcomes if o is not None and o.status_code == 409)
    assert ok_count == 1
    assert blocked_count == 1
    # Stock 5 minus the one serialized sale of 3 = 2 (the loser saw 2 < 3 -> 409)
    assert _read_stock(insumo_id) == Decimal("2")

    # clean up the created sale so FK cleanup on the producto can proceed
    _cleanup_ventas_for_producto(producto_id)
    _cleanup_producto(producto_id)
    _cleanup_insumo(insumo_id)
    _cleanup_categoria(categoria_id)
    _cleanup_tipo(tipo_id)