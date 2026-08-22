"""add indexes on foreign keys and filter columns

Revision ID: 0007_add_indexes_fk_and_filters
Revises: 27d5c5b6fd80
Create Date: 2026-08-13 20:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_add_indexes_fk_and_filters"
down_revision: str | None = "27d5c5b6fd80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Ventas
    op.create_index("ix_Ventas_fecha", "Ventas", ["fecha"], unique=False)
    op.create_index("ix_Ventas_cliente_id", "Ventas", ["cliente_id"], unique=False)
    op.create_index("ix_Ventas_canal_venta", "Ventas", ["canal_venta"], unique=False)
    op.create_index("ix_Ventas_estado", "Ventas", ["estado"], unique=False)

    # Detalle_Ventas
    op.create_index("ix_Detalle_Ventas_venta_id", "Detalle_Ventas", ["venta_id"], unique=False)
    op.create_index(
        "ix_Detalle_Ventas_producto_id", "Detalle_Ventas", ["producto_id"], unique=False
    )
    op.create_index(
        "ix_Detalle_Ventas_variante_id", "Detalle_Ventas", ["variante_id"], unique=False
    )

    # Devoluciones & Items
    op.create_index("ix_Devoluciones_venta_id", "Devoluciones", ["venta_id"], unique=False)
    op.create_index("ix_Devoluciones_usuario_id", "Devoluciones", ["usuario_id"], unique=False)
    op.create_index(
        "ix_Items_Devolucion_devolucion_id", "Items_Devolucion", ["devolucion_id"], unique=False
    )
    op.create_index(
        "ix_Items_Devolucion_producto_id", "Items_Devolucion", ["producto_id"], unique=False
    )
    op.create_index(
        "ix_Items_Devolucion_variante_id", "Items_Devolucion", ["variante_id"], unique=False
    )

    # Insumos & Compras
    op.create_index("ix_Insumos_categoria_id", "Insumos", ["categoria_id"], unique=False)
    op.create_index("ix_Compras_Insumos_insumo_id", "Compras_Insumos", ["insumo_id"], unique=False)
    op.create_index(
        "ix_Compras_Insumos_proveedor_id", "Compras_Insumos", ["proveedor_id"], unique=False
    )
    op.create_index(
        "ix_Compras_Insumos_fecha_compra", "Compras_Insumos", ["fecha_compra"], unique=False
    )

    # Productos, Variantes & BOM
    op.create_index(
        "ix_Productos_tipo_producto_id", "Productos", ["tipo_producto_id"], unique=False
    )
    op.create_index(
        "ix_Variantes_Producto_producto_id", "Variantes_Producto", ["producto_id"], unique=False
    )
    op.create_index("ix_BOM_Insumos_producto_id", "BOM_Insumos", ["producto_id"], unique=False)
    op.create_index("ix_BOM_Insumos_insumo_id", "BOM_Insumos", ["insumo_id"], unique=False)
    op.create_index("ix_BOM_Productos_combo_id", "BOM_Productos", ["combo_id"], unique=False)
    op.create_index(
        "ix_BOM_Productos_producto_incluido_id",
        "BOM_Productos",
        ["producto_incluido_id"],
        unique=False,
    )


def downgrade() -> None:
    # BOM & Productos
    op.drop_index("ix_BOM_Productos_producto_incluido_id", table_name="BOM_Productos")
    op.drop_index("ix_BOM_Productos_combo_id", table_name="BOM_Productos")
    op.drop_index("ix_BOM_Insumos_insumo_id", table_name="BOM_Insumos")
    op.drop_index("ix_BOM_Insumos_producto_id", table_name="BOM_Insumos")
    op.drop_index("ix_Variantes_Producto_producto_id", table_name="Variantes_Producto")
    op.drop_index("ix_Productos_tipo_producto_id", table_name="Productos")

    # Compras & Insumos
    op.drop_index("ix_Compras_Insumos_fecha_compra", table_name="Compras_Insumos")
    op.drop_index("ix_Compras_Insumos_proveedor_id", table_name="Compras_Insumos")
    op.drop_index("ix_Compras_Insumos_insumo_id", table_name="Compras_Insumos")
    op.drop_index("ix_Insumos_categoria_id", table_name="Insumos")

    # Items & Devoluciones
    op.drop_index("ix_Items_Devolucion_variante_id", table_name="Items_Devolucion")
    op.drop_index("ix_Items_Devolucion_producto_id", table_name="Items_Devolucion")
    op.drop_index("ix_Items_Devolucion_devolucion_id", table_name="Items_Devolucion")
    op.drop_index("ix_Devoluciones_usuario_id", table_name="Devoluciones")
    op.drop_index("ix_Devoluciones_venta_id", table_name="Devoluciones")

    # Detalle & Ventas
    op.drop_index("ix_Detalle_Ventas_variante_id", table_name="Detalle_Ventas")
    op.drop_index("ix_Detalle_Ventas_producto_id", table_name="Detalle_Ventas")
    op.drop_index("ix_Detalle_Ventas_venta_id", table_name="Detalle_Ventas")
    op.drop_index("ix_Ventas_estado", table_name="Ventas")
    op.drop_index("ix_Ventas_canal_venta", table_name="Ventas")
    op.drop_index("ix_Ventas_cliente_id", table_name="Ventas")
    op.drop_index("ix_Ventas_fecha", table_name="Ventas")
