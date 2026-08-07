"""Devoluciones engine tests — strict TDD (slice 2, task 2.3).

Exercises registrar_devolucion + listar_devoluciones against the real test
PostgreSQL via SessionLocal and the real sale engine (registrar_venta):
- DEV-1: total cancel restores ALL BOM stock, estado->anulada, reembolso=full;
  already-anulada -> 400; no material PObs -> 400 (nothing committed).
- DEV-2: partial return restores ONLY the returned items' BOM at the sale-time
  price snapshot; qty > sold -> 422.
- DEV-3: atomic all-or-nothing (stock-restore failure / IntegrityError roll
  back everything); double return -> 409; concurrent double-return serializes
  on the Venta FOR UPDATE lock (sequential-equivalent final stock, no double
  restore).
- DEV-4: listar_devoluciones filters by venta_id, paginates, loads items+venta.

Setup mirrors test_inventory.py: uuid4-unique names, direct model setup against
SessionLocal, FK-ordered cleanup.
"""

import threading
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    BomInsumo,
    CategoriaInsumo,
    Cliente,
    Devolucion,
    DetalleVenta,
    Insumo,
    Producto,
    TipoProducto,
    Venta,
)
from app.services.devoluciones import (
    listar_devoluciones,
    registrar_devolucion,
)
from app.services.inventory import registrar_venta


def _unique() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# DB helpers (mirror test_inventory.py)
# ---------------------------------------------------------------------------


def _make_categoria() -> int:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Categoria {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat.id
    finally:
        db.close()


def _make_insumo(categoria_id: int, costo: str = "0", stock: str = "0") -> int:
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


def _make_producto(tipo_producto_id: int) -> int:
    db = SessionLocal()
    try:
        producto = Producto(
            tipo_producto_id=tipo_producto_id,
            nombre=f"Producto {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto.id
    finally:
        db.close()


def _make_linea_insumo(producto_id: int, insumo_id: int, cantidad: str = "1") -> None:
    db = SessionLocal()
    try:
        db.add(
            BomInsumo(
                producto_id=producto_id,
                insumo_id=insumo_id,
                cantidad_requerida=Decimal(cantidad),
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.commit()
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


def _read_stock(insumo_id: int) -> Decimal:
    db = SessionLocal()
    try:
        return db.get(Insumo, insumo_id).stock_actual
    finally:
        db.close()


def _read_venta(venta_id: int):
    db = SessionLocal()
    try:
        venta = db.get(Venta, venta_id)
        return venta, [d for d in venta.detalles]
    finally:
        db.close()


def _count_devoluciones(venta_id: int) -> int:
    db = SessionLocal()
    try:
        return db.query(Devolucion).filter(Devolucion.venta_id == venta_id).count()
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
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.commit()
    finally:
        db.close()


def _cleanup_tipo(tipo_id: int) -> None:
    db = SessionLocal()
    try:
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


def _cleanup_ventas_for_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        ven_ids = select(DetalleVenta.venta_id).where(
            DetalleVenta.producto_id == producto_id
        )
        db.query(Venta).filter(Venta.id.in_(ven_ids)).delete(
            synchronize_session=False
        )
        db.query(DetalleVenta).filter(DetalleVenta.producto_id == producto_id).delete(
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


def _cleanup_devolucion(venta_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(Devolucion).filter(Devolucion.venta_id == venta_id).delete()
        db.commit()
    finally:
        db.close()


def _venta_detalle(
    producto_id: int,
    cantidad: str = "1",
    precio: str = "10",
) -> dict:
    return {
        "producto_id": producto_id,
        "variante_id": None,
        "cantidad": Decimal(cantidad),
        "precio_unitario": Decimal(precio),
    }


# ---------------------------------------------------------------------------
# DEV-1: full cancel restores all stock, anulada/no-PO -> 400
# ---------------------------------------------------------------------------


def test_devolucion_total_cancela_y_restaura_todo_el_stock():
    """Cancel-full: Devolucion tipo='total', reembolso=total, venta anulada,
    every consumed insumo restored in the same commit (DEV-1)."""
    categoria = _make_categoria()
    insumo_id = _make_insumo(categoria, costo="5", stock="10")
    tipo = _make_tipo()
    producto = _make_producto(tipo)
    _make_linea_insumo(producto, insumo_id)
    cliente_id = _make_cliente()
    try:
        db = SessionLocal()
        try:
            venta = registrar_venta(
                db, {"cliente_id": cliente_id, "canal_venta": "web",
                     "descuento_porcentaje": Decimal("0"),
                     "detalles": [_venta_detalle(producto, cantidad="1", precio="10")]}
            )
        finally:
            db.close()
        assert _read_stock(insumo_id) == Decimal("9")

        db = SessionLocal()
        try:
            dev = registrar_devolucion(
                db, user_id=None,
                payload={"venta_id": venta.id, "tipo": "total",
                         "motivo": "cliente final"},
            )
        finally:
            db.close()
        venta_r, _dets = _read_venta(venta.id)
        assert dev.tipo == "total"
        assert dev.monto_reembolsado == Decimal("10.0000")
        assert dev.venta_id == venta.id
        assert venta_r.estado == "anulada"
        assert _read_stock(insumo_id) == Decimal("10")  # fully restored
    finally:
        _cleanup_devolucion(venta.id)
        _cleanup_ventas_for_producto(producto)
        _cleanup_cliente(cliente_id)
        _cleanup_producto(producto)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria)
        _cleanup_tipo(tipo)


def test_registrar_devolucion_total_venta_ya_anulada_400():
    """Ya anulada -> 400 y nada se restaura (DEV-1)."""
    categoria = _make_categoria()
    insumo_id = _make_insumo(categoria, stock="10")
    tipo = _make_tipo()
    producto = _make_producto(tipo)
    _make_linea_insumo(producto, insumo_id)
    try:
        db = SessionLocal()
        try:
            venta = registrar_venta(
                db, {"cliente_id": None, "canal_venta": "web",
                     "descuento_porcentaje": Decimal("0"),
                     "detalles": [_venta_detalle(producto, cantidad="1")]}
            )
        finally:
            db.close()

        db = SessionLocal()
        try:
            registrar_devolucion(db, None, {"venta_id": venta.id, "tipo": "total"})
        finally:
            db.close()

        # reintento sobre la venta ya anulada -> 400 (sin doble restauración)
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                registrar_devolucion(db, None, {"venta_id": venta.id, "tipo": "total"})
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 400
        assert _read_stock(insumo_id) == Decimal("10")
    finally:
        _cleanup_devolucion(venta.id)
        _cleanup_ventas_for_producto(producto)
        _cleanup_producto(producto)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria)
        _cleanup_tipo(tipo)


def test_registrar_devolucion_total_sin_bom_400():
    """Producto sin BOM explotable -> 400 y venta queda 'completada' (no-PO)."""
    categoria = _make_categoria()
    tipo = _make_tipo()
    producto = _make_producto(tipo)  # sin lineas de insumo
    try:
        db = SessionLocal()
        try:
            venta = registrar_venta(
                db, {"cliente_id": None, "canal_venta": "web",
                     "descuento_porcentaje": Decimal("0"),
                     "detalles": [_venta_detalle(producto, cantidad="1", precio="10")]}
            )
        finally:
            db.close()
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                registrar_devolucion(db, None, {"venta_id": venta.id, "tipo": "total"})
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 400
        venta_r, _ = _read_venta(venta.id)
        assert venta_r.estado == "completada"
    finally:
        _cleanup_ventas_for_producto(producto)
        _cleanup_producto(producto)
        _cleanup_tipo(tipo)
        _cleanup_categoria(categoria)


# ---------------------------------------------------------------------------
# DEV-2: partial return, snapshot price, qty>sold -> 422
# ---------------------------------------------------------------------------


def test_registrar_devolucion_parcial_restaura_solo_linea_devuelta():
    """Parcial restaura SOLO el BOM de la línea devuelta; la otra queda (DEV-2)."""
    ctx = _vender_dos_lineas()
    try:
        assert _read_stock(ctx["i1"]) == Decimal("9")
        assert _read_stock(ctx["i2"]) == Decimal("9")
        db = SessionLocal()
        try:
            dev = registrar_devolucion(
                db, None, {"venta_id": ctx["venta"].id, "tipo": "parcial",
                           "items": [{"producto_id": ctx["p1"], "variante_id": None,
                                      "cantidad": Decimal("1")}]}
            )
            dev_id = dev.id
            items = [it for it in dev.items]
        finally:
            db.close()
        assert dev.tipo == "parcial"
        assert dev.monto_reembolsado == Decimal("10.0000")  # 1 x precio 10
        assert _read_stock(ctx["i1"]) == Decimal("10")  # restaurada
        assert _read_stock(ctx["i2"]) == Decimal("9")  # intacta
        assert len(items) == 1
        assert items[0].producto_id == ctx["p1"]
        assert items[0].cantidad == Decimal("1")
        assert items[0].precio_unitario == Decimal("10.0000")
        assert items[0].subtotal == Decimal("10.0000")
        venta_r, _ = _read_venta(ctx["venta"].id)
        assert venta_r.estado == "completada"
        assert dev_id == dev.id
    finally:
        _cleanup_ctx_dos_lineas(ctx)


def test_registrar_devolucion_parcial_usa_precio_snapshot_de_la_venta():
    """El reembolso usa el precio_unitario_aplicado snapshot de la venta, NO el
    precio de una venta posterior del mismo producto (snapshot, DEV-2)."""
    categoria = _make_categoria()
    insumo_id = _make_insumo(categoria, stock="20")
    tipo = _make_tipo()
    producto = _make_producto(tipo)
    _make_linea_insumo(producto, insumo_id)
    try:
        db = SessionLocal()
        try:
            v1 = registrar_venta(
                db, {"cliente_id": None, "canal_venta": "web",
                     "descuento_porcentaje": Decimal("0"),
                     "detalles": [_venta_detalle(producto, cantidad="1", precio="10")]}
            )
        finally:
            db.close()
        # venta posterior del mismo producto a un precio distinto
        db = SessionLocal()
        try:
            registrar_venta(
                db, {"cliente_id": None, "canal_venta": "web",
                     "descuento_porcentaje": Decimal("0"),
                     "detalles": [_venta_detalle(producto, cantidad="1", precio="25")]}
            )
        finally:
            db.close()
        db = SessionLocal()
        try:
            dev = registrar_devolucion(
                db, None, {"venta_id": v1.id, "tipo": "parcial",
                           "items": [{"producto_id": producto, "variante_id": None,
                                      "cantidad": Decimal("1")}]}
            )
            precio_snapshot = dev.items[0].precio_unitario
        finally:
            db.close()
        assert dev.monto_reembolsado == Decimal("10.0000")  # snapshot, NO 25
        assert precio_snapshot == Decimal("10.0000")
    finally:
        _cleanup_devolucion(v1.id)
        _cleanup_ventas_for_producto(producto)
        _cleanup_producto(producto)
        _cleanup_insumo(insumo_id)
        _cleanup_categoria(categoria)
        _cleanup_tipo(tipo)


def test_registrar_devolucion_parcial_cantidad_excede_vendida_422():
    """cantidad > vendida -> 422 y nada se persiste (DEV-2)."""
    ctx = _vender_una_linea(cantidad="5", stock="5")
    try:
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                registrar_devolucion(
                    db, None,
                    {"venta_id": ctx["venta"].id, "tipo": "parcial",
                     "items": [{"producto_id": ctx["producto"], "variante_id": None,
                                "cantidad": Decimal("6")}]},  # vendido 5
                )
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 422
        assert _read_stock(ctx["insumo"]) == Decimal("0")
        assert _count_devoluciones(ctx["venta"].id) == 0
    finally:
        _cleanup_ctx_una_linea(ctx)


# ---------------------------------------------------------------------------
# DEV-3: atomicity, doble-devolucion, concurrencia FOR UPDATE
# ---------------------------------------------------------------------------


def test_registrar_devolucion_doble_devolucion_409():
    """Una devolución por venta: segunda -> 409, sin doble restauración (DEV-3)."""
    ctx = _vender_una_linea(cantidad="1", stock="10")
    try:
        db = SessionLocal()
        try:
            registrar_devolucion(
                db, None, {"venta_id": ctx["venta"].id, "tipo": "parcial",
                           "items": [{"producto_id": ctx["producto"], "variante_id": None,
                                      "cantidad": Decimal("1")}]}
            )
        finally:
            db.close()
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                registrar_devolucion(
                    db, None, {"venta_id": ctx["venta"].id, "tipo": "parcial",
                               "items": [{"producto_id": ctx["producto"], "variante_id": None,
                                          "cantidad": Decimal("1")}]}
                )
        finally:
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        assert _read_stock(ctx["insumo"]) == Decimal("10")  # restaurado UNA vez
        assert _count_devoluciones(ctx["venta"].id) == 1
    finally:
        _cleanup_ctx_una_linea(ctx)


def test_registrar_devolucion_concurrente_for_update_no_doble_restaura():
    """Dos devoluciones concurrentes sobre la misma venta: una gana, otra 409,
    stock restaurado exactamente una vez (FOR UPDATE sobre Venta, DEV-3)."""
    ctx = _vender_una_linea(cantidad="1", stock="10")
    barrier = threading.Barrier(2)
    outcomes: list[HTTPException | None] = [None, None]
    devolute_ok: list[bool] = [False, False]

    def devolucionar(slot: int):
        db = SessionLocal()
        try:
            barrier.wait(timeout=10)
            registrar_devolucion(
                db, None, {"venta_id": ctx["venta"].id, "tipo": "parcial",
                           "items": [{"producto_id": ctx["producto"], "variante_id": None,
                                      "cantidad": Decimal("1")}]}
            )
            devolute_ok[slot] = True
        except HTTPException as exc:
            outcomes[slot] = exc
        finally:
            db.close()

    t1 = threading.Thread(target=devolucionar, args=(0,))
    t2 = threading.Thread(target=devolucionar, args=(1,))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    ok_count = sum(1 for ok in devolute_ok if ok)
    blocked = sum(1 for o in outcomes if o is not None and o.status_code == 409)
    assert ok_count == 1
    assert blocked == 1
    assert _count_devoluciones(ctx["venta"].id) == 1
    assert _read_stock(ctx["insumo"]) == Decimal("10")  # una sola restauración
    _cleanup_ctx_una_linea(ctx)


def test_registrar_devolucion_rollback_si_stock_falla(monkeypatch):
    """Falla en reponer_stock -> todo revierte: sin Devolucion, venta no anulada,
    stock intacto (DEV-3 atomic all-or-nothing)."""
    from app.services import devoluciones as dev_svc

    ctx = _vender_una_linea(cantidad="1", stock="10")
    try:

        def _boom(db, explosiones):
            raise HTTPException(status_code=404, detail="Insumo not found")

        monkeypatch.setattr(dev_svc, "reponer_stock", _boom)
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                registrar_devolucion(db, None, {"venta_id": ctx["venta"].id, "tipo": "total"})
        finally:
            monkeypatch.undo()
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 404
        assert _count_devoluciones(ctx["venta"].id) == 0
        venta_r, _ = _read_venta(ctx["venta"].id)
        assert venta_r.estado == "completada"
        assert _read_stock(ctx["insumo"]) == Decimal("9")
    finally:
        _cleanup_ctx_una_linea(ctx)


def test_registrar_devolucion_integrity_error_409(monkeypatch):
    """Constraint failure en commit -> 409, sin persistir nada (DEV-3)."""
    ctx = _vender_una_linea(cantidad="1", stock="10")
    try:

        def raising_commit(self):
            raise IntegrityError(
                "INSERT INTO Devoluciones ...", {},
                Exception("duplicate key value violates unique constraint"),
            )

        monkeypatch.setattr(Session, "commit", raising_commit)
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as excinfo:
                registrar_devolucion(db, None, {"venta_id": ctx["venta"].id, "tipo": "total"})
        finally:
            monkeypatch.undo()
            db.rollback()
            db.close()
        assert excinfo.value.status_code == 409
        assert _count_devoluciones(ctx["venta"].id) == 0
        assert _read_stock(ctx["insumo"]) == Decimal("9")  # no restaurado
        venta_r, _ = _read_venta(ctx["venta"].id)
        assert venta_r.estado == "completada"
    finally:
        _cleanup_ctx_una_linea(ctx)


# ---------------------------------------------------------------------------
# DEV-4: listar
# ---------------------------------------------------------------------------


def test_listar_devoluciones_filtra_por_venta_y_pagina():
    """listar_devoluciones filtra por venta_id, carga items+venta, limita (DEV-4)."""
    categoria = _make_categoria()
    i1 = _make_insumo(categoria, stock="30")
    tipo = _make_tipo()
    p1 = _make_producto(tipo)
    _make_linea_insumo(p1, i1)
    try:
        db = SessionLocal()
        try:
            v1 = registrar_venta(db, {"cliente_id": None, "canal_venta": "web",
                                      "descuento_porcentaje": Decimal("0"),
                                      "detalles": [_venta_detalle(p1, cantidad="1")]})
            v1_id = v1.id
        finally:
            db.close()
        db = SessionLocal()
        try:
            v2 = registrar_venta(db, {"cliente_id": None, "canal_venta": "web",
                                      "descuento_porcentaje": Decimal("0"),
                                      "detalles": [_venta_detalle(p1, cantidad="2")]})
            v2_id = v2.id
        finally:
            db.close()
        for venta_id in (v1_id, v2_id):
            db = SessionLocal()
            try:
                registrar_devolucion(db, None, {"venta_id": venta_id, "tipo": "parcial",
                                               "items": [{"producto_id": p1,
                                                          "variante_id": None,
                                                          "cantidad": Decimal("1")}]})
            finally:
                db.close()
        db = SessionLocal()
        try:
            solo_v2 = listar_devoluciones(db, venta_id=v2_id)
            assert len(solo_v2) == 1
            assert solo_v2[0].venta_id == v2_id
            assert solo_v2[0].venta.id == v2_id  # venta reference cargada
            assert len(solo_v2[0].items) == 1  # items cargados
            paginado = listar_devoluciones(db, limit=1)
            assert len(paginado) == 1
        finally:
            db.close()
    finally:
        _cleanup_devolucion(v1_id)
        _cleanup_devolucion(v2_id)
        _cleanup_ventas_for_producto(p1)
        _cleanup_producto(p1)
        _cleanup_insumo(i1)
        _cleanup_categoria(categoria)
        _cleanup_tipo(tipo)


# ---------------------------------------------------------------------------
# helpers (shared)
# ---------------------------------------------------------------------------


def _vender_una_linea(cantidad: str, stock: str) -> dict:
    """Venta de un producto con un insumo -> context dict."""
    categoria = _make_categoria()
    insumo = _make_insumo(categoria, costo="5", stock=stock)
    tipo = _make_tipo()
    producto = _make_producto(tipo)
    _make_linea_insumo(producto, insumo, cantidad="1")
    db = SessionLocal()
    try:
        venta = registrar_venta(
            db, {"cliente_id": None, "canal_venta": "web",
                 "descuento_porcentaje": Decimal("0"),
                 "detalles": [_venta_detalle(producto, cantidad=cantidad, precio="10")]}
        )
    finally:
        db.close()
    return {
        "categoria": categoria,
        "insumo": insumo,
        "tipo": tipo,
        "producto": producto,
        "venta": venta,
    }


def _cleanup_ctx_una_linea(ctx: dict) -> None:
    _cleanup_devolucion(ctx["venta"].id)
    _cleanup_ventas_for_producto(ctx["producto"])
    _cleanup_producto(ctx["producto"])
    _cleanup_insumo(ctx["insumo"])
    _cleanup_categoria(ctx["categoria"])
    _cleanup_tipo(ctx["tipo"])


def _vender_dos_lineas() -> dict:
    """Venta de dos productos (precios 10 y 20), cada uno con su insumo."""
    categoria = _make_categoria()
    i1 = _make_insumo(categoria, costo="5", stock="10")
    i2 = _make_insumo(categoria, costo="5", stock="10")
    tipo = _make_tipo()
    p1 = _make_producto(tipo)
    p2 = _make_producto(tipo)
    _make_linea_insumo(p1, i1, cantidad="1")
    _make_linea_insumo(p2, i2, cantidad="1")
    db = SessionLocal()
    try:
        venta = registrar_venta(
            db, {"cliente_id": None, "canal_venta": "web",
                 "descuento_porcentaje": Decimal("0"),
                 "detalles": [_venta_detalle(p1, cantidad="1", precio="10"),
                              _venta_detalle(p2, cantidad="1", precio="20")]}
        )
    finally:
        db.close()
    return {"categoria": categoria, "i1": i1, "i2": i2, "tipo": tipo,
            "p1": p1, "p2": p2, "venta": venta}


def _cleanup_ctx_dos_lineas(ctx: dict) -> None:
    _cleanup_devolucion(ctx["venta"].id)
    _cleanup_ventas_for_producto(ctx["p1"])
    _cleanup_ventas_for_producto(ctx["p2"])
    _cleanup_producto(ctx["p1"])
    _cleanup_producto(ctx["p2"])
    _cleanup_insumo(ctx["i1"])
    _cleanup_insumo(ctx["i2"])
    _cleanup_categoria(ctx["categoria"])
    _cleanup_tipo(ctx["tipo"])