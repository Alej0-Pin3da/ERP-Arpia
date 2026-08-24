"""PR1 DB foundation RED tests — must fail before implementation, pass after."""
from __future__ import annotations

import pytest
from sqlalchemy import inspect

from app.models.clientes import Cliente
from app.models.ventas import Venta
from app.schemas.cliente import ClienteCreate, ClienteRead, ClienteUpdate
from app.schemas.venta import VentaCreate, VentaRead


class TestClienteModelCRM:
    def test_cliente_has_10_crm_columns(self):
        cols = {c.key for c in inspect(Cliente).mapper.column_attrs}
        expected = {
            "ciudad",
            "direccion",
            "tipo",
            "talla_habitual",
            "talla_superior",
            "talla_inferior",
            "categoria_preferida",
            "tipo_producto_frecuente",
            "notas",
            "medidas",
        }
        missing = expected - cols
        assert not missing, f"Missing Cliente columns: {missing}"

    def test_cliente_medidas_is_jsonb_dict(self):
        # medidas should be JSONB; check type affinity
        col = Cliente.__table__.c.medidas
        assert "json" in str(col.type).lower()

    def test_cliente_indices_exist(self):
        idx_names = {idx.name for idx in Cliente.__table__.indexes}
        assert "ix_clientes_tipo" in idx_names
        assert "ix_clientes_ciudad" in idx_names


class TestVentaModelChannelPayment:
    def test_venta_has_metodo_pago(self):
        cols = {c.key for c in inspect(Venta).mapper.column_attrs}
        assert "metodo_pago" in cols

    def test_venta_canal_venta_is_varchar_50(self):
        col = Venta.__table__.c.canal_venta
        assert col.type.length == 50

    def test_venta_canal_ck_includes_showroom_pereira(self):
        # Locate CK constraint
        cks = [c for c in Venta.__table__.constraints if c.name == "ck_ventas_canal_venta"]
        assert len(cks) == 1
        sql = str(list(cks)[0].sqltext)
        assert "showroom_pereira" in sql
        assert "web" in sql


class TestSchemasValidation:
    def test_cliente_create_accepts_crm_fields_and_medidas_dict(self):
        obj = ClienteCreate(
            nombre="Test",
            ciudad="Pereira",
            direccion="Calle 1",
            tipo="mayorista",
            talla_habitual="M",
            talla_superior="L",
            talla_inferior="32",
            categoria_preferida="jeans",
            tipo_producto_frecuente="pantalon",
            notas="nota",
            medidas={"busto": 88, "cintura": 70},
        )
        assert obj.medidas == {"busto": 88, "cintura": 70}

    def test_cliente_medidas_non_dict_rejected(self):
        with pytest.raises(Exception):
            ClienteCreate(nombre="Test", medidas="88-90")  # type: ignore

    def test_cliente_medidas_none_allowed(self):
        obj = ClienteCreate(nombre="Test", medidas=None)
        assert obj.medidas is None

    def test_venta_create_accepts_showroom_pereira_and_metodo(self):
        obj = VentaCreate(
            canal_venta="showroom_pereira",
            metodo_pago="transferencia",
            detalles=[{"producto_id": 1, "cantidad": "1", "precio_unitario": "10"}],
        )
        assert obj.canal_venta == "showroom_pereira"
        assert obj.metodo_pago == "transferencia"

    def test_venta_create_rejects_invalid_canal(self):
        with pytest.raises(Exception):
            VentaCreate(
                canal_venta="telefono",  # type: ignore
                detalles=[{"producto_id": 1, "cantidad": "1", "precio_unitario": "10"}],
            )

    def test_venta_create_rejects_invalid_metodo(self):
        with pytest.raises(Exception):
            VentaCreate(
                canal_venta="web",
                metodo_pago="cripto",  # type: ignore
                detalles=[{"producto_id": 1, "cantidad": "1", "precio_unitario": "10"}],
            )

    def test_venta_create_null_metodo_allowed(self):
        obj = VentaCreate(
            canal_venta="web",
            detalles=[{"producto_id": 1, "cantidad": "1", "precio_unitario": "10"}],
        )
        assert obj.metodo_pago is None
        obj2 = VentaCreate(
            canal_venta="web",
            metodo_pago=None,
            detalles=[{"producto_id": 1, "cantidad": "1", "precio_unitario": "10"}],
        )
        assert obj2.metodo_pago is None

    def test_venta_read_includes_metodo_pago(self):
        fields = set(VentaRead.model_fields.keys())
        assert "metodo_pago" in fields
        assert "canal_venta" in fields

    def test_cliente_read_includes_crm_fields(self):
        fields = set(ClienteRead.model_fields.keys())
        for f in ["ciudad", "direccion", "tipo", "medidas", "notas"]:
            assert f in fields
