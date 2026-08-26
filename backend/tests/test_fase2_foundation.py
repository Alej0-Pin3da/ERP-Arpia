"""PR1 Foundation RED tests for v4-fase2 — must fail before 0011-0013 + model extension, pass after."""
from __future__ import annotations

import importlib
import pathlib

import pytest
from sqlalchemy import inspect

# --- Model existence ---

def test_socios_has_10_extended_columns():
    from app.models.finanzas import SociosConfiguracion
    cols = {c.key for c in inspect(SociosConfiguracion).mapper.column_attrs}
    expected = {
        "rol",
        "banco",
        "es_fondo_taller",
        "telefono",
        "email",
        "tipo_cuenta",
        "numero_cuenta",
        "titular_cuenta",
        "activo",
        "notas",
    }
    missing = expected - cols
    assert not missing, f"Missing Socios columns: {missing}"


def test_socios_indices_exist():
    from app.models.finanzas import SociosConfiguracion
    idx_names = {idx.name for idx in SociosConfiguracion.__table__.indexes}
    assert "ix_socios_rol" in idx_names, f"Missing ix_socios_rol in {idx_names}"
    assert "ix_socios_activo" in idx_names, f"Missing ix_socios_activo in {idx_names}"


def test_socios_activo_and_fondo_defaults():
    from app.models.finanzas import SociosConfiguracion
    activo_col = SociosConfiguracion.__table__.c.activo
    fondo_col = SociosConfiguracion.__table__.c.es_fondo_taller
    # Check server_default or default present
    assert activo_col.default is not None or activo_col.server_default is not None
    assert fondo_col.default is not None or fondo_col.server_default is not None


def test_liquidacion_enums_exist():
    from app.models.finanzas import AnticipoEstado, DistribucionEstado, LiquidacionEstado
    assert LiquidacionEstado.BORRADOR.value == "BORRADOR"
    assert LiquidacionEstado.APROBADA.value == "APROBADA"
    assert LiquidacionEstado.PAGADA.value == "PAGADA"
    assert DistribucionEstado.PENDIENTE.value == "PENDIENTE"
    assert AnticipoEstado.PENDIENTE_DESCUENTO.value == "PENDIENTE_DESCUENTO"


def test_liquidacion_model_exists():
    from app.models.finanzas import Liquidacion
    cols = {c.key for c in inspect(Liquidacion).mapper.column_attrs}
    for expected in ["codigo", "periodo", "fecha_cierre", "total_ventas_brutas", "estado", "creado_en"]:
        assert expected in cols, f"Missing Liquidacion.{expected}"
    # codigo unique
    codigo_col = Liquidacion.__table__.c.codigo
    assert codigo_col.unique is True or any(
        c.name == "uq_liquidaciones_codigo" or "codigo" in str(c.columns) for c in Liquidacion.__table__.constraints if hasattr(c, "columns")
    )
    # CHECK estado
    cks = [c for c in Liquidacion.__table__.constraints if getattr(c, "name", "") == "ck_liquidaciones_estado"]
    assert len(cks) == 1, "Missing ck_liquidaciones_estado"


def test_liquidacion_distribucion_model_exists():
    from app.models.finanzas import LiquidacionDistribucion
    cols = {c.key for c in inspect(LiquidacionDistribucion).mapper.column_attrs}
    for expected in ["liquidacion_id", "socia_id", "monto_bruto", "deduccion_anticipos", "monto_neto", "estado_pago"]:
        assert expected in cols, f"Missing LiquidacionDistribucion.{expected}"
    # Unique pair
    uqs = [c for c in LiquidacionDistribucion.__table__.constraints if getattr(c, "name", "") == "uq_distribucion_liquidacion_socia"]
    assert len(uqs) == 1, "Missing unique liquidacion_id+socia_id"
    # CK estado_pago
    cks = [c for c in LiquidacionDistribucion.__table__.constraints if getattr(c, "name", "") == "ck_distribucion_estado_pago"]
    assert len(cks) == 1


def test_anticipo_model_exists():
    from app.models.finanzas import Anticipo
    cols = {c.key for c in inspect(Anticipo).mapper.column_attrs}
    for expected in ["socia_id", "monto", "fecha", "estado", "liquidacion_id", "concepto", "creado_en"]:
        assert expected in cols, f"Missing Anticipo.{expected}"
    # FK socia_id not nullable CASCADE
    socia_col = Anticipo.__table__.c.socia_id
    assert socia_col.nullable is False
    # partial unique index name check
    idx_names = {idx.name for idx in Anticipo.__table__.indexes}
    assert "ix_anticipos_socia_fecha" in idx_names
    # Check for partial unique on antig
    partial_found = any("ix_anticipos_socia_liquidacion" in (idx.name or "") for idx in Anticipo.__table__.indexes)
    assert partial_found or any("partial" in str(idx.dialect_options).lower() for idx in Anticipo.__table__.indexes), "Missing partial unique index for double-discount guard"


def test_migration_files_exist():
    base = pathlib.Path(__file__).parent.parent / "alembic" / "versions"
    assert (base / "0011_extend_socios_configuracion.py").exists(), "0011 missing"
    assert (base / "0012_create_liquidaciones.py").exists(), "0012 missing"
    assert (base / "0013_create_anticipos.py").exists(), "0013 missing"


def test_migration_revision_chain():
    import importlib.util
    base = pathlib.Path(__file__).parent.parent / "alembic" / "versions"
    specs = {}
    for fname in ["0011_extend_socios_configuracion.py", "0012_create_liquidaciones.py", "0013_create_anticipos.py"]:
        p = base / fname
        if not p.exists():
            pytest.fail(f"Migration file {fname} not found — cannot check chain")
        spec = importlib.util.spec_from_file_location(fname.replace(".py",""), p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        specs[fname] = mod
    assert specs["0011_extend_socios_configuracion.py"].revision == "0011_extend_socios_configuracion"
    assert specs["0011_extend_socios_configuracion.py"].down_revision == "0010_ventas_canal_pago"
    assert specs["0012_create_liquidaciones.py"].down_revision == "0011_extend_socios_configuracion"
    assert specs["0013_create_anticipos.py"].down_revision == "0012_create_liquidaciones"
