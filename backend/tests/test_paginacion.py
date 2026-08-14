"""Shared pagination helper tests — strict TDD (ui-mantenimiento PR1, T1).

Verifies the ``paginar`` contract (design D1/D2): the returned ``total`` is
the count of the FULL filtered set (limit/offset ignored) and the rows honor
limit/offset. Runs against the real test PostgreSQL through SessionLocal
mirroring the endpoint suites' direct-model setup.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import CategoriaInsumo, Insumo
from app.services.paginacion import paginar


@pytest.fixture(scope="module")
def _categoria():
    db = SessionLocal()
    try:
        cat = CategoriaInsumo(nombre="Paginacion Test Cat")
        db.add(cat)
        db.commit()
        db.refresh(cat)
        yield cat
    finally:
        db.close()


@pytest.fixture(scope="module")
def _insumos(_categoria):
    db = SessionLocal()
    try:
        ids = []
        for i in range(5):
            ins = Insumo(
                categoria_id=_categoria.id,
                nombre=f"Insumo Pag {i}",
                unidad_medida="metro",
                stock_actual=Decimal("0"),
                stock_minimo=Decimal("0"),
                costo_promedio_actual=Decimal("0"),
            )
            db.add(ins)
            db.commit()
            db.refresh(ins)
            ids.append(ins.id)
        yield ids
    finally:
        db.query(Insumo).filter(Insumo.categoria_id == _categoria.id).delete()
        db.query(CategoriaInsumo).filter(CategoriaInsumo.id == _categoria.id).delete()
        db.commit()
        db.close()


def test_paginar_devuelve_total_completo_y_filas_acotadas(_categoria, _insumos):
    """total == full filtered count (5); rows honor limit (2) and offset (0)."""
    db = SessionLocal()
    try:
        stmt = select(Insumo).where(Insumo.categoria_id == _categoria.id).order_by(Insumo.id)
        rows, total = paginar(db, stmt, limit=2, offset=0)
        assert total == 5
        assert len(rows) == 2
        assert [r.id for r in rows] == sorted(_insumos)[:2]
    finally:
        db.close()


def test_paginar_offset_fuera_de_rango_total_intacto(_categoria, _insumos):
    """offset beyond the filtered set -> empty rows, total still 5 (no 404)."""
    db = SessionLocal()
    try:
        stmt = select(Insumo).where(Insumo.categoria_id == _categoria.id).order_by(Insumo.id)
        rows, total = paginar(db, stmt, limit=50, offset=200)
        assert rows == []
        assert total == 5
    finally:
        db.close()


def test_paginar_total_del_conjunto_filtrado(_categoria, _insumos):
    """Filters applied BEFORE count: q='Insumo Pag 1' -> total == 1."""
    db = SessionLocal()
    try:
        stmt = (
            select(Insumo)
            .where(Insumo.categoria_id == _categoria.id)
            .where(Insumo.nombre.ilike("%Pag 1%"))
            .order_by(Insumo.id)
        )
        rows, total = paginar(db, stmt, limit=50, offset=0)
        assert total == 1
        assert [r.nombre for r in rows] == ["Insumo Pag 1"]
    finally:
        db.close()


def test_paginar_conjunto_vacio():
    """No matching rows -> ([], 0), production code still ran the count."""
    db = SessionLocal()
    try:
        stmt = select(Insumo).where(Insumo.id == 99999999)
        rows, total = paginar(db, stmt, limit=50, offset=0)
        assert rows == []
        assert total == 0
    finally:
        db.close()
