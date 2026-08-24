"""fix ventas canal + metodo_pago + seeds

Revision ID: 0010_ventas_canal_pago
Revises: 0009_extend_clientes_crm
Create Date: 2026-08-23

- metodo_pago VARCHAR(50) nullable
- canal_venta VARCHAR(50) + CK 5 values (web|whatsapp|instagram|feria|showroom_pereira)
- legacy canal mapping: Feria Showroom->feria, WhatsApp / DM->whatsapp, Showroom Pereira->showroom_pereira
- maestros_canales_venta + maestros_metodos_pago tables + 5+4 idempotent seeds
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_ventas_canal_pago"
down_revision: str | None = "0009_extend_clientes_crm"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Canonical seeds
CANALES = [
    ("web", "Web"),
    ("whatsapp", "WhatsApp"),
    ("instagram", "Instagram"),
    ("feria", "Feria"),
    ("showroom_pereira", "Showroom Pereira"),
]
METODOS = [
    ("efectivo", "Efectivo"),
    ("transferencia", "Transferencia"),
    ("tarjeta", "Tarjeta"),
    ("contraentrega", "Contraentrega"),
]


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        cols = [c["name"] for c in insp.get_columns(table)]
        return column in cols
    except Exception:
        return False


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table in insp.get_table_names()


def _has_constraint(table: str, name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        for c in insp.get_check_constraints(table):
            if c["name"] == name:
                return True
    except Exception:
        pass
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint WHERE conname = :name AND conrelid = :table::regclass"
            ),
            {"name": name, "table": table},
        ).scalar()
        return res is not None
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Create maestros tables if not exist
    if not _has_table("maestros_canales_venta"):
        op.create_table(
            "maestros_canales_venta",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("codigo", sa.String(length=50), nullable=False, unique=True),
            sa.Column("nombre", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if not _has_table("maestros_metodos_pago"):
        op.create_table(
            "maestros_metodos_pago",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("codigo", sa.String(length=50), nullable=False, unique=True),
            sa.Column("nombre", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # 2) Seeds idempotent — ON CONFLICT DO NOTHING
    for codigo, nombre in CANALES:
        bind.execute(
            sa.text(
                "INSERT INTO maestros_canales_venta (codigo, nombre) VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
            ),
            {"codigo": codigo, "nombre": nombre},
        )

    for codigo, nombre in METODOS:
        bind.execute(
            sa.text(
                "INSERT INTO maestros_metodos_pago (codigo, nombre) VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
            ),
            {"codigo": codigo, "nombre": nombre},
        )

    # 3) Legacy canal mapping before tightening CK
    if _has_column("Ventas", "canal_venta"):
        bind.execute(sa.text("UPDATE \"Ventas\" SET canal_venta = 'feria' WHERE canal_venta = 'Feria Showroom'"))
        bind.execute(sa.text("UPDATE \"Ventas\" SET canal_venta = 'whatsapp' WHERE canal_venta = 'WhatsApp / DM'"))
        bind.execute(sa.text("UPDATE \"Ventas\" SET canal_venta = 'showroom_pereira' WHERE canal_venta = 'Showroom Pereira'"))
        bind.execute(sa.text("UPDATE \"Ventas\" SET canal_venta = 'showroom_pereira' WHERE LOWER(canal_venta) = 'showroom'"))

    # 4) Widen canal_venta to VARCHAR(50) if needed
    if _has_column("Ventas", "canal_venta"):
        try:
            op.alter_column("Ventas", "canal_venta", type_=sa.String(length=50), existing_type=sa.String(length=16), nullable=False)
        except Exception:
            bind.execute(sa.text('ALTER TABLE "Ventas" ALTER COLUMN canal_venta TYPE VARCHAR(50)'))

    # 5) Add metodo_pago column
    if not _has_column("Ventas", "metodo_pago"):
        op.add_column("Ventas", sa.Column("metodo_pago", sa.String(length=50), nullable=True))

    # 6) Recreate CK for canal_venta with 5 values
    if _has_constraint("Ventas", "ck_ventas_canal_venta"):
        try:
            op.drop_constraint("ck_ventas_canal_venta", "Ventas", type_="check")
        except Exception:
            bind.execute(sa.text('ALTER TABLE "Ventas" DROP CONSTRAINT IF EXISTS ck_ventas_canal_venta'))
    op.create_check_constraint(
        "ck_ventas_canal_venta",
        "Ventas",
        "canal_venta IN ('web', 'whatsapp', 'instagram', 'feria', 'showroom_pereira')",
    )


def downgrade() -> None:
    bind = op.get_bind()

    # Drop new CK
    try:
        op.drop_constraint("ck_ventas_canal_venta", "Ventas", type_="check")
    except Exception:
        bind.execute(sa.text('ALTER TABLE "Ventas" DROP CONSTRAINT IF EXISTS ck_ventas_canal_venta'))

    # Restore old CK with 4 values
    op.create_check_constraint(
        "ck_ventas_canal_venta",
        "Ventas",
        "canal_venta IN ('web', 'whatsapp', 'instagram', 'feria')",
    )

    # Remove showroom_pereira rows mapping back to feria before shrinking
    if _has_column("Ventas", "canal_venta"):
        bind.execute(sa.text("UPDATE \"Ventas\" SET canal_venta = 'feria' WHERE canal_venta = 'showroom_pereira'"))
        try:
            op.alter_column("Ventas", "canal_venta", type_=sa.String(length=16), existing_type=sa.String(length=50), nullable=False)
        except Exception:
            bind.execute(sa.text('ALTER TABLE "Ventas" ALTER COLUMN canal_venta TYPE VARCHAR(16)'))

    # Drop metodo_pago
    if _has_column("Ventas", "metodo_pago"):
        op.drop_column("Ventas", "metodo_pago")

    # Delete seeds
    for codigo, _ in CANALES:
        bind.execute(sa.text("DELETE FROM maestros_canales_venta WHERE codigo = :codigo"), {"codigo": codigo})
    for codigo, _ in METODOS:
        bind.execute(sa.text("DELETE FROM maestros_metodos_pago WHERE codigo = :codigo"), {"codigo": codigo})

    if _has_table("maestros_metodos_pago"):
        count = bind.execute(sa.text("SELECT COUNT(*) FROM maestros_metodos_pago")).scalar()
        if count == 0:
            op.drop_table("maestros_metodos_pago")
    if _has_table("maestros_canales_venta"):
        count = bind.execute(sa.text("SELECT COUNT(*) FROM maestros_canales_venta")).scalar()
        if count == 0:
            op.drop_table("maestros_canales_venta")
