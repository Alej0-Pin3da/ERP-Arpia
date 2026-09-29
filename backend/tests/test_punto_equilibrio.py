"""Termómetro Operativo del Mes tests.

Service-level with an explicit `ahora` pinned to empty far-future months,
so every case is isolated from suite order and from real workshop data.
Plus one thin API wiring test (auth, route, JSON shape).

Money math under test: S=1000, C=400, fijos=1200 -> MC 60.0%, meta 2000.00,
avance 50.0%, faltante 1000.00.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.db.session import SessionLocal
from app.models import (
    CategoriaInsumo,
    DetalleVenta,
    Devolucion,
    DevolucionItem,
    Insumo,
    ParametrosCosteo,
    Producto,
    TipoProducto,
    Venta,
)
from app.services.punto_equilibrio import calcular_termometro

BOG = ZoneInfo("America/Bogota")


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _setup_producto() -> tuple[int, int]:
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat Termo {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        ins = Insumo(
            categoria_id=cat.id,
            nombre=f"Tela Termo {_unique()}",
            unidad_medida="metro",
            stock_actual=Decimal("100"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("5"),
        )
        db.add(ins)
        db.commit()
        db.refresh(ins)
        tipo = TipoProducto(nombre=f"Tipo Termo {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        prod = Producto(
            tipo_producto_id=tipo.id,
            nombre=f"Producto Termo {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
            stock_actual=Decimal("10000"),
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        return tipo.id, prod.id
    finally:
        db.close()


def _set_fijos(valor: str) -> str | None:
    """Set singleton fijos, returning the previous raw value (None = row created)."""
    db = SessionLocal()
    try:
        row = db.get(ParametrosCosteo, 1)
        if row is None:
            row = ParametrosCosteo(id=1)
            db.add(row)
            db.commit()
            db.refresh(row)
            old = None
        else:
            old = str(row.costos_fijos_mensuales)
        row.costos_fijos_mensuales = Decimal(valor)
        db.commit()
        return old
    finally:
        db.close()


def _restore_fijos(old: str | None) -> None:
    db = SessionLocal()
    try:
        if old is None:
            db.query(ParametrosCosteo).filter(ParametrosCosteo.id == 1).delete()
        else:
            row = db.get(ParametrosCosteo, 1)
            if row is not None:
                row.costos_fijos_mensuales = Decimal(old)
        db.commit()
    finally:
        db.close()


def _vender(
    producto_id: int,
    fecha: datetime,
    total: str,
    costo_u: str,
    cantidad: str = "1",
    estado: str = "confirmed",
) -> int:
    db = SessionLocal()
    try:
        v = Venta(
            fecha=fecha,
            estado=estado,
            total_venta=Decimal(total),
            canal_venta="feria",
            descuento_porcentaje=Decimal("0"),
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        db.add(
            DetalleVenta(
                venta_id=v.id,
                producto_id=producto_id,
                variante_id=None,
                cantidad=Decimal(cantidad),
                precio_unitario_aplicado=Decimal(total),
                costo_unitario_aplicado=Decimal(costo_u),
            )
        )
        db.commit()
        return v.id
    finally:
        db.close()


def _devolver(venta_id: int, producto_id: int, fecha: datetime, monto: str, cantidad: str, precio: str) -> int:
    db = SessionLocal()
    try:
        d = Devolucion(
            venta_id=venta_id,
            fecha=fecha,
            motivo="test",
            monto_reembolsado=Decimal(monto),
            tipo="parcial",
            estado="confirmed",
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        db.add(
            DevolucionItem(
                devolucion_id=d.id,
                producto_id=producto_id,
                variante_id=None,
                cantidad=Decimal(cantidad),
                precio_unitario=Decimal(precio),
                subtotal=Decimal(cantidad) * Decimal(precio),
            )
        )
        db.commit()
        return d.id
    finally:
        db.close()


def _cleanup(venta_ids: list[int | None], producto_id: int, tipo_id: int) -> None:
    venta_ids = [v for v in venta_ids if v is not None]
    db = SessionLocal()
    try:
        dev_ids = [r[0] for r in db.query(Devolucion.id).filter(Devolucion.venta_id.in_(venta_ids)).all()] if venta_ids else []
        if dev_ids:
            db.query(DevolucionItem).filter(DevolucionItem.devolucion_id.in_(dev_ids)).delete(synchronize_session=False)
            db.query(Devolucion).filter(Devolucion.id.in_(dev_ids)).delete(synchronize_session=False)
        if venta_ids:
            db.query(DetalleVenta).filter(DetalleVenta.venta_id.in_(venta_ids)).delete(synchronize_session=False)
            db.query(Venta).filter(Venta.id.in_(venta_ids)).delete(synchronize_session=False)
        ins_ids = [r[0] for r in db.query(Insumo.id).filter(Insumo.nombre.like("Tela Termo%")).all()]
        cat_ids = [r[0] for r in db.query(CategoriaInsumo.id).filter(CategoriaInsumo.nombre.like("Cat Termo%")).all()]
        db.query(Producto).filter(Producto.id == producto_id).delete(synchronize_session=False)
        if ins_ids:
            db.query(Insumo).filter(Insumo.id.in_(ins_ids)).delete(synchronize_session=False)
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete(synchronize_session=False)
        if cat_ids:
            db.query(CategoriaInsumo).filter(CategoriaInsumo.id.in_(cat_ids)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _termometro(ahora: datetime):
    db = SessionLocal()
    try:
        return calcular_termometro(db, ahora)
    finally:
        db.close()


def test_en_camino_matematica_exacta():
    tipo_id, prod_id = _setup_producto()
    old = _set_fijos("1200")
    vid: int | None = None
    try:
        vid = _vender(prod_id, datetime(2099, 1, 10, 10, 0, tzinfo=BOG), "1000", "400")
        r = _termometro(datetime(2099, 1, 20, 12, 0, tzinfo=BOG))
        assert r.estado == "en_camino"
        assert r.periodo == "2099-01"
        assert r.ventas_netas == Decimal("1000")
        assert r.costos_netos == Decimal("400")
        assert r.margen_pct == Decimal("60.0")
        assert r.costos_fijos == Decimal("1200")
        assert r.meta_ventas == Decimal("2000.00")
        assert r.avance_pct == Decimal("50.0")
        assert r.faltante == Decimal("1000.00")
        assert r.utilidad_extra is None
        assert r.n_ventas == 1 and r.n_devoluciones == 0
    finally:
        _restore_fijos(old)
        _cleanup([vid], prod_id, tipo_id)


def test_superada_muestra_utilidad_extra():
    tipo_id, prod_id = _setup_producto()
    old = _set_fijos("300")
    vid: int | None = None
    try:
        vid = _vender(prod_id, datetime(2099, 2, 5, 10, 0, tzinfo=BOG), "1000", "400")
        r = _termometro(datetime(2099, 2, 20, 12, 0, tzinfo=BOG))
        assert r.estado == "superada"
        assert r.meta_ventas == Decimal("500.00")
        assert r.utilidad_extra == Decimal("500.00")
        assert r.faltante is None
    finally:
        _restore_fijos(old)
        _cleanup([vid], prod_id, tipo_id)


def test_alerta_con_margen_negativo_sin_meta():
    tipo_id, prod_id = _setup_producto()
    old = _set_fijos("1200")
    vid: int | None = None
    try:
        vid = _vender(prod_id, datetime(2099, 3, 5, 10, 0, tzinfo=BOG), "100", "400")
        r = _termometro(datetime(2099, 3, 20, 12, 0, tzinfo=BOG))
        assert r.estado == "alerta"
        assert r.margen_pct < 0
        assert r.meta_ventas is None
    finally:
        _restore_fijos(old)
        _cleanup([vid], prod_id, tipo_id)


def test_sin_datos_mes_vacio():
    r = _termometro(datetime(2099, 4, 20, 12, 0, tzinfo=BOG))
    assert r.estado == "sin_datos"
    assert r.meta_ventas is None


def test_sin_configurar_con_fijos_en_cero():
    tipo_id, prod_id = _setup_producto()
    old = _set_fijos("0")
    vid: int | None = None
    try:
        vid = _vender(prod_id, datetime(2099, 5, 5, 10, 0, tzinfo=BOG), "1000", "400")
        r = _termometro(datetime(2099, 5, 20, 12, 0, tzinfo=BOG))
        assert r.estado == "sin_configurar"
        assert r.meta_ventas is None
    finally:
        _restore_fijos(old)
        _cleanup([vid], prod_id, tipo_id)


def test_devolucion_netea_ingreso_y_costo():
    tipo_id, prod_id = _setup_producto()
    old = _set_fijos("1200")
    vid: int | None = None
    try:
        vid = _vender(prod_id, datetime(2099, 6, 5, 10, 0, tzinfo=BOG), "1000", "400")
        _devolver(vid, prod_id, datetime(2099, 6, 6, 10, 0, tzinfo=BOG), "400", "1", "400")
        r = _termometro(datetime(2099, 6, 20, 12, 0, tzinfo=BOG))
        assert r.n_devoluciones == 1
        assert r.ventas_netas == Decimal("600")
        assert r.costos_netos == Decimal("0")
        assert r.margen_pct == Decimal("100.0")
    finally:
        _restore_fijos(old)
        _cleanup([vid], prod_id, tipo_id)


def test_draft_no_cuenta_y_bogota_no_utc():
    tipo_id, prod_id = _setup_producto()
    old = _set_fijos("100")
    vid_draft: int | None = None
    vid_borde: int | None = None
    try:
        vid_draft = _vender(
            prod_id, datetime(2099, 7, 5, 10, 0, tzinfo=BOG), "1000", "400", estado="draft"
        )
        # 31-ene 20:00 Bogota = 01-feb 01:00 UTC: en Bogota es enero, no febrero.
        vid_borde = _vender(prod_id, datetime(2099, 1, 31, 20, 0, tzinfo=BOG), "500", "100")
        r = _termometro(datetime(2099, 2, 15, 12, 0, tzinfo=BOG))
        assert r.n_ventas == 0
        assert r.estado == "sin_datos"
    finally:
        _restore_fijos(old)
        _cleanup([vid_draft, vid_borde], prod_id, tipo_id)


def test_api_responde_estructura(client, admin_token):
    resp = client.get(
        "/api/v1/finanzas/punto-equilibrio",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["estado"] in {"sin_datos", "sin_configurar", "alerta", "en_camino", "superada"}
    assert len(body["periodo"]) == 7 and body["periodo"][4] == "-"
    for k in ("ventas_netas", "costos_netos", "margen_pct", "costos_fijos"):
        Decimal(str(body[k]))
