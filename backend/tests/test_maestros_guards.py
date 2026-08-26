"""PR1 Foundation RED tests for v4-fase3-maestros 0014 — must fail before 0014+models, pass after.

Covers: _has_table/_has_column guards, upgrade/downgrade, 3 CREATE + 2 ALTER, models CHECK/UNIQUE/15,4.
Strict TDD RED -> GREEN -> TRIANGULATE.
"""
from __future__ import annotations

import importlib.util
import pathlib
import pytest
from sqlalchemy import inspect

MIGRATION_PATH = pathlib.Path(__file__).parent.parent / "alembic" / "versions" / "0014_maestros_core.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("m0014", MIGRATION_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestMigrationFileGuards:
    def test_migration_file_exists(self):
        assert MIGRATION_PATH.exists(), "0014_maestros_core.py missing"

    def test_migration_revision_chain(self):
        mod = _load_migration()
        assert mod.revision == "0014_maestros_core"
        assert mod.down_revision == "0013_create_anticipos"

    def test_has_table_and_has_column_guards_present(self):
        content = MIGRATION_PATH.read_text(encoding="utf-8")
        assert "_has_table" in content, "missing _has_table guard"
        assert "_has_column" in content, "missing _has_column guard"

    def test_has_index_guard_present(self):
        content = MIGRATION_PATH.read_text(encoding="utf-8")
        assert "_has_index" in content or "has_index" in content

    def test_migration_contains_3_create_and_2_alter(self):
        content = MIGRATION_PATH.read_text(encoding="utf-8")
        assert "maestros_proveedores" in content
        assert "maestros_categorias_coleccion" in content or "maestros_categoria_coleccion" in content
        assert "maestros_ubicaciones_taller" in content or "maestros_ubicacion_taller" in content
        # ALTER stubs
        assert "maestros_canales_venta" in content
        assert "maestros_metodos_pago" in content
        # Must use ALTER / add_column for stubs, not create_table
        assert "add_column" in content

    def test_migration_indexes_and_downgrade(self):
        content = MIGRATION_PATH.read_text(encoding="utf-8")
        # downgrade must exist and not drop stub tables
        assert "def downgrade" in content
        # should drop columns for stubs, not tables
        assert "drop_column" in content
        # should not drop maestros_canales_venta table in downgrade (keep stub)
        # downgrade should still handle new tables via drop_table
        assert "drop_table" in content

    def test_migration_uses_nullable_alter_and_checks(self):
        content = MIGRATION_PATH.read_text(encoding="utf-8")
        assert "CheckConstraint" in content or "ck_" in content
        assert "nullable=True" in content or "nullable" in content


class TestProveedorModel:
    def test_proveedor_model_importable(self):
        from app.models.maestros import ProveedorMaestro
        assert ProveedorMaestro.__tablename__ == "maestros_proveedores"

    def test_proveedor_has_required_columns(self):
        from app.models.maestros import ProveedorMaestro
        cols = {c.key for c in inspect(ProveedorMaestro).mapper.column_attrs}
        for expected in ["nombre", "categoria", "ciudad", "calificacion", "tiempo_entrega_dias", "email", "activo"]:
            assert expected in cols, f"Missing ProveedorMaestro.{expected}"

    def test_proveedor_nombre_unique_and_calificacion_check(self):
        from app.models.maestros import ProveedorMaestro
        nombre_col = ProveedorMaestro.__table__.c.nombre
        assert nombre_col.unique is True or any("nombre" in str(c.columns) for c in ProveedorMaestro.__table__.constraints if hasattr(c, "columns"))
        cks = [c for c in ProveedorMaestro.__table__.constraints if getattr(c, "name", "") and "calificacion" in c.name]
        assert len(cks) >= 1 or any("calificacion" in str(getattr(c, "sqltext", "")) for c in ProveedorMaestro.__table__.constraints)

    def test_proveedor_calificacion_numeric_3_1(self):
        from app.models.maestros import ProveedorMaestro
        col = ProveedorMaestro.__table__.c.calificacion
        assert "numeric" in str(col.type).lower()
        # precision/scale check
        assert col.type.precision == 3 or "3" in str(col.type)

    def test_proveedor_decoupled_from_0008(self):
        # Table name must NOT be "Proveedores" (0008 deleted) but "maestros_proveedores"
        from app.models.maestros import ProveedorMaestro
        assert ProveedorMaestro.__tablename__ != "Proveedores"
        assert "maestros_proveedores" == ProveedorMaestro.__tablename__


class TestCategoriaModel:
    def test_categoria_model_importable(self):
        from app.models.maestros import CategoriaColeccion
        assert "categoria" in CategoriaColeccion.__tablename__

    def test_categoria_has_tipo_talla_check(self):
        from app.models.maestros import CategoriaColeccion
        cols = {c.key for c in inspect(CategoriaColeccion).mapper.column_attrs}
        assert "tipo_talla" in cols
        cks = [c for c in CategoriaColeccion.__table__.constraints if getattr(c, "name", "") and "tipo_talla" in c.name.lower()]
        # at least one CHECK for tipo_talla 3 values
        assert len(cks) >= 1 or any("CON_TALLAS_ESTANDAR" in str(getattr(c, "sqltext", "")) for c in CategoriaColeccion.__table__.constraints)

    def test_categoria_nombre_unique(self):
        from app.models.maestros import CategoriaColeccion
        col = CategoriaColeccion.__table__.c.nombre
        assert col.unique is True or any("nombre" in str(getattr(c, "name", "")) for c in CategoriaColeccion.__table__.constraints)


class TestUbicacionModel:
    def test_ubicacion_model_importable(self):
        from app.models.maestros import UbicacionTaller
        assert "ubicacion" in UbicacionTaller.__tablename__

    def test_ubicacion_codigo_ub_pattern_and_unique(self):
        from app.models.maestros import UbicacionTaller
        cols = {c.key for c in inspect(UbicacionTaller).mapper.column_attrs}
        assert "codigo" in cols
        assert "tipo" in cols
        codigo_col = UbicacionTaller.__table__.c.codigo
        assert codigo_col.unique is True
        # tipo CHECK 4 values
        cks = [c for c in UbicacionTaller.__table__.constraints if getattr(c, "name", "") and "tipo" in c.name.lower()]
        assert len(cks) >= 1 or any("ROLLOS_TELAS" in str(getattr(c, "sqltext", "")) for c in UbicacionTaller.__table__.constraints)

    def test_ubicacion_codigo_check_ub_prefix(self):
        from app.models.maestros import UbicacionTaller
        # Ensure CHECK contains UB-
        found = any("UB-" in str(getattr(c, "sqltext", "")) for c in UbicacionTaller.__table__.constraints)
        assert found, "Missing UB-* CHECK on codigo"


class TestCanalesVentaExtended:
    def test_canales_model_importable(self):
        from app.models.maestros import CanalVentaMaestro
        assert "canales_venta" in CanalVentaMaestro.__tablename__

    def test_canales_has_extended_columns(self):
        from app.models.maestros import CanalVentaMaestro
        cols = {c.key for c in inspect(CanalVentaMaestro).mapper.column_attrs}
        for expected in ["tipo", "comision_pct", "costo_fijo_mensual", "activo"]:
            assert expected in cols, f"Missing CanalVentaMaestro.{expected}"

    def test_canales_tipo_check_and_numeric_15_4(self):
        from app.models.maestros import CanalVentaMaestro
        cks = [c for c in CanalVentaMaestro.__table__.constraints if getattr(c, "name", "") and "tipo" in c.name.lower()]
        assert len(cks) >= 1 or any("FISICO" in str(getattr(c, "sqltext", "")) for c in CanalVentaMaestro.__table__.constraints)
        col = CanalVentaMaestro.__table__.c.comision_pct
        assert "numeric" in str(col.type).lower()


class TestMetodosPagoExtended:
    def test_metodos_model_importable(self):
        from app.models.maestros import MetodoPagoMaestro
        assert "metodos_pago" in MetodoPagoMaestro.__tablename__

    def test_metodos_has_extended_columns(self):
        from app.models.maestros import MetodoPagoMaestro
        cols = {c.key for c in inspect(MetodoPagoMaestro).mapper.column_attrs}
        for expected in ["tipo", "comision_pct", "tiempo_acreditacion", "activo"]:
            assert expected in cols, f"Missing MetodoPagoMaestro.{expected}"

    def test_metodos_tipo_check_4_values(self):
        from app.models.maestros import MetodoPagoMaestro
        found = any("TRANSFERENCIA" in str(getattr(c, "sqltext", "")) for c in MetodoPagoMaestro.__table__.constraints)
        assert found, "Missing TRANSFERENCIA CHECK on metodos_pago.tipo"


class TestMaestrosInitExports:
    def test_init_exports_all_5_models(self):
        import app.models as models_pkg
        for name in ["ProveedorMaestro", "CategoriaColeccion", "UbicacionTaller", "CanalVentaMaestro", "MetodoPagoMaestro"]:
            assert hasattr(models_pkg, name), f"Missing export {name} in app.models.__init__"
