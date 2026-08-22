"""compras-wac-ux: add proveedor_id, factura, costo_unitario_aplicado + index

Revision ID: 20260821_wac
Revises: 98bda77bcd4d
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_wac"
down_revision: str | None = "98bda77bcd4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    indexes = [i["name"] for i in insp.get_indexes(table)]
    return index_name in indexes


def upgrade() -> None:
    # proveedor_id: re-add as nullable without FK (Proveedores was removed in 0008)
    if not _has_column("Compras_Insumos", "proveedor_id"):
        op.add_column(
            "Compras_Insumos",
            sa.Column("proveedor_id", sa.Integer(), nullable=True),
        )
    if not _has_index("Compras_Insumos", "ix_Compras_Insumos_proveedor_id"):
        op.create_index(
            "ix_Compras_Insumos_proveedor_id",
            "Compras_Insumos",
            ["proveedor_id"],
            unique=False,
        )

    if not _has_column("Compras_Insumos", "factura"):
        op.add_column(
            "Compras_Insumos",
            sa.Column("factura", sa.String(length=100), nullable=True),
        )

    if not _has_column("Compras_Insumos", "costo_unitario_aplicado"):
        op.add_column(
            "Compras_Insumos",
            sa.Column("costo_unitario_aplicado", sa.Numeric(precision=15, scale=4), nullable=True),
        )

    # fecha_compra index already exists since 0007 but ensure idempotent
    if not _has_index("Compras_Insumos", "ix_Compras_Insumos_fecha_compra"):
        op.create_index(
            "ix_Compras_Insumos_fecha_compra",
            "Compras_Insumos",
            ["fecha_compra"],
            unique=False,
        )

    # Backfill: existing rows get NULL (already nullable), no data migration needed.
    # costo_unitario_aplicado stays NULL for historical rows; new rows will populate
    # via WAC service from the computed nuevo_costo.


def downgrade() -> None:
    if _has_index("Compras_Insumos", "ix_Compras_Insumos_fecha_compra"):
        # Only drop if this migration created it and no earlier migration needed it;
        # 0007 also created this index, so downgrade is safe to keep or drop.
        # We drop only if column set was created here; keep idempotent guard.
        try:
            op.drop_index("ix_Compras_Insumos_fecha_compra", table_name="Compras_Insumos")
        except Exception:
            pass

    if _has_column("Compras_Insumos", "costo_unitario_aplicado"):
        op.drop_column("Compras_Insumos", "costo_unitario_aplicado")

    if _has_column("Compras_Insumos", "factura"):
        op.drop_column("Compras_Insumos", "factura")

    if _has_index("Compras_Insumos", "ix_Compras_Insumos_proveedor_id"):
        try:
            op.drop_index("ix_Compras_Insumos_proveedor_id", table_name="Compras_Insumos")
        except Exception:
            pass
    if _has_column("Compras_Insumos", "proveedor_id"):
        op.drop_column("Compras_Insumos", "proveedor_id")
