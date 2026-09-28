"""Total-time fallback in the cost engine.

``tiempo_confeccion_min`` (the single total, e.g. 120 validated from the
auditor) must drive labor when no per-phase breakdown exists. Per-phase
times keep precedence; with neither, the legacy manual fallback applies.
"""

import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import (
    CategoriaInsumo,
    Insumo,
    Producto,
    TipoProducto,
)
from app.services.costos import calcular_costo_produccion


def _unique() -> str:
    return uuid.uuid4().hex[:8]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _setup(tiempo_total: int | None = None, fases: dict | None = None):
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre=f"Cat TTotal {_unique()}")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        tipo = TipoProducto(nombre=f"Tipo TTotal {_unique()}")
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
        prod = Producto(
            tipo_producto_id=tipo.id,
            nombre=f"Producto TTotal {_unique()}",
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
            mano_obra=Decimal("0"),
            cif_energia=Decimal("0"),
            tiempo_confeccion_min=tiempo_total,
            **(fases or {}),
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        return cat.id, tipo.id, prod.id
    finally:
        db.close()


def _cleanup(producto_id: int, tipo_id: int, cat_id: int) -> None:
    db = SessionLocal()
    try:
        db.query(Producto).filter(Producto.id == producto_id).delete()
        db.query(TipoProducto).filter(TipoProducto.id == tipo_id).delete()
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == cat_id).delete()
        db.commit()
    finally:
        db.close()


def _tasas_actuales(client, headers) -> dict:
    return client.get("/api/v1/maestros/parametros-costeo", headers=headers).json()


def _fijar_tasas(client, headers, mano: str, energia: str) -> None:
    resp = client.patch(
        "/api/v1/maestros/parametros-costeo",
        json={"costo_minuto_costura": mano, "costo_minuto_energia": energia},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


def test_tiempo_total_mueve_costo(client, admin_token):
    """120 min totales x $100/min = $12.000 de mano (sin fases)."""
    cat_id, tipo_id, producto_id = _setup(tiempo_total=120)
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        _fijar_tasas(client, headers, "100", "10")
        db = SessionLocal()
        try:
            assert calcular_costo_produccion(db, producto_id) == Decimal("12000")
        finally:
            db.close()
        resp = client.get(f"/api/v1/productos/{producto_id}/costo", headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert Decimal(str(body["total"])) == Decimal("12000")
        lineas = body["lineas"]
        mano = [l for l in lineas if l["tipo"] == "mano_obra"]
        assert len(mano) == 1
        assert Decimal(str(mano[0]["cantidad"])) == Decimal("120")
        # Energía sin desglose de costura: 0 honesto, sin línea.
        assert all(l["tipo"] != "cif_energia" for l in lineas)
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )
        _cleanup(producto_id, tipo_id, cat_id)


def test_fases_mandan_sobre_total(client, admin_token):
    """Con desglose por fases, el total se ignora (precedencia intacta)."""
    cat_id, tipo_id, producto_id = _setup(
        tiempo_total=120, fases={"tiempo_corte_min": 10, "tiempo_costura_min": 20}
    )
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        _fijar_tasas(client, headers, "100", "10")
        db = SessionLocal()
        try:
            # 30 min x 100 = 3000 mano + 20 min costura x 10 = 200 energía
            # (fases, no los 12000 del total).
            assert calcular_costo_produccion(db, producto_id) == Decimal("3200")
        finally:
            db.close()
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )
        _cleanup(producto_id, tipo_id, cat_id)


def test_sin_tiempos_cae_a_legacy(client, admin_token):
    """Sin fases ni total: el fallback manual manda (0 aquí)."""
    cat_id, tipo_id, producto_id = _setup()
    headers = _auth(admin_token)
    prev = _tasas_actuales(client, headers)
    try:
        _fijar_tasas(client, headers, "100", "10")
        db = SessionLocal()
        try:
            assert calcular_costo_produccion(db, producto_id) == Decimal("0")
        finally:
            db.close()
    finally:
        _fijar_tasas(
            client, headers, str(prev["costo_minuto_costura"]), str(prev["costo_minuto_energia"])
        )
        _cleanup(producto_id, tipo_id, cat_id)
