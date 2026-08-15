"""remove proveedores entity

Revision ID: 0008_remove_proveedores
Revises: 0007_add_indexes_fk_and_filters
Create Date: 2026-08-14 19:40:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_remove_proveedores"
down_revision: str | None = "0007_add_indexes_fk_and_filters"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Business decision (2026-08): the Proveedores entity was removed from the
    # ERP. The workbook no longer has a Proveedores sheet and the business no
    # longer tracks suppliers. Compras_Insumos.proveedor_id was nullable and
    # every historical row is NULL, so dropping it loses no data.
    op.drop_constraint("Compras_Insumos_proveedor_id_fkey", "Compras_Insumos", type_="foreignkey")
    op.drop_index("ix_Compras_Insumos_proveedor_id", table_name="Compras_Insumos")
    op.drop_column("Compras_Insumos", "proveedor_id")
    op.drop_table("Proveedores")


def downgrade() -> None:
    op.create_table(
        "Proveedores",
        op.Column("id", op.Integer(), nullable=False),
        op.Column("nombre", op.String(length=255), nullable=False),
        op.Column("ubicacion", op.String(length=255), nullable=True),
        op.Column("url", op.String(length=500), nullable=True),
        op.Column("contacto", op.String(length=255), nullable=True),
        op.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "Compras_Insumos",
        op.Column("proveedor_id", op.Integer(), nullable=True),
    )
    op.create_index("ix_Compras_Insumos_proveedor_id", "Compras_Insumos", ["proveedor_id"])
    op.create_foreign_key(
        "Compras_Insumos_proveedor_id_fkey",
        "Compras_Insumos",
        "Proveedores",
        ["proveedor_id"],
        ["id"],
        ondelete="SET NULL",
    )
