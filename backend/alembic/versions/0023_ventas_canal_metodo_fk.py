"""Ventas canal/metodo -> maestros + legacy estado normalization (P1-6).

NOTE on P1-4 (Movimientos.liquidacion_id -> liquidaciones FK): investigated
and found INVIABLE, so no migration for it. settle_liquidacion (the ONLY
writer of that column) stores synthetic per-socio keys "<key10><idx2>"
(12 chars), never the bare LIQ-YYYY-NN codigo — a FK to
liquidaciones(codigo) rejects every settlement insert (proven: broke
test_finanzas.py settle tests). The partial UNIQUE uq_liquidacion stays as
the one-time-settlement guard; reconciliation stays manual via codigo
prefix. No data was harmed: dev had zero non-null values in both columns.

P1-6: Ventas.canal_venta had a 5-value CHECK and metodo_pago was free text,
while maestros_canales_venta / maestros_metodos_pago are independent CRUD —
a channel created in Maestros 422d in Ventas. Investigation (dev DB):
CHECK values == maestros codigo values and all existing Ventas rows already
use canonical values, so FKs are viable (no CHECK replacement by service
validation needed — FK + service validation both).

Steps (backfill/seed FIRST, constraints AFTER — existing sales never break):
0. Legacy Ventas.estado normalization (dev drift): some databases still carry
   the pre-98bda77 domain ('completada'/'anulada') with its legacy CHECK while
   the code writes DocumentState ('confirmed'/...). Map completada->confirmed
   and anulada->cancelled, then swap any legacy CHECK for the document-state
   one. No-op on schemas already migrated.
1. Idempotent seed of the 5 canonical canales + 4 canonical metodos
   (same lists as 0010).
2. Backfill: any distinct Ventas.canal_venta / metodo_pago value missing from
   maestros is inserted as a maestro row (codigo=nombre=value), so no sale
   is ever rewritten and the FKs are always creatable.
3. Drop ck_ventas_canal_venta; create:
   - fk_ventas_canal_codigo: Ventas(canal_venta) -> maestros_canales_venta
     (codigo) ON DELETE RESTRICT ON UPDATE CASCADE (column is NOT NULL).
   - fk_ventas_metodo_codigo: Ventas(metodo_pago) -> maestros_metodos_pago
     (codigo) ON DELETE SET NULL ON UPDATE CASCADE (column is nullable).
   Deleting a referenced canal/metodo is blocked (service maps to 409).

Downgrade: drop the FKs, map non-canonical values back (canal->feria,
metodo->NULL) and recreate the canonical 5-value CHECK; restore the legacy
estado domain + legacy CHECK (mirror of 98bda77 downgrade).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023_ventas_canal_metodo_fk"
down_revision: str | None = "0022_compras_proveedor_fk"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

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
CANAL_CHECK = (
    "canal_venta IN ('web', 'whatsapp', 'instagram', 'feria', 'showroom_pereira')"
)
ESTADO_CHECK = "estado IN ('draft', 'confirmed', 'cancelled', 'reversed')"
LEGACY_ESTADO_CHECK = "estado IN ('completada', 'anulada')"
FK_CANAL = "fk_ventas_canal_codigo"
FK_METODO = "fk_ventas_metodo_codigo"


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    try:
        return table in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    try:
        return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]
    except Exception:
        return False


def _has_constraint(table: str, name: str) -> bool:
    bind = op.get_bind()
    try:
        for c in sa.inspect(bind).get_check_constraints(table):
            if c["name"] == name:
                return True
    except Exception:
        pass
    # Exact relname match — never CAST(:table AS regclass): regclass folds
    # to lowercase and raises on case-sensitive tables ("Ventas", ...),
    # poisoning the whole migration transaction.
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint c JOIN pg_class cl "
                "ON cl.oid = c.conrelid "
                "WHERE c.conname = :name AND cl.relname = :table"
            ),
            {"name": name, "table": table},
        ).scalar()
        return res is not None
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_table("Ventas"):
        return

    # 0) Legacy estado normalization (dev drift) — idempotent. The legacy
    # CHECK must be dropped BEFORE the UPDATEs: it still enforces
    # ('completada','anulada') on drifted databases, so updating first
    # violates it (this is why the drift survived 98bda77).
    if _has_column("Ventas", "estado"):
        bind.execute(sa.text('ALTER TABLE "Ventas" DROP CONSTRAINT IF EXISTS ck_ventas_estado'))
        bind.execute(sa.text("UPDATE \"Ventas\" SET estado = 'confirmed' WHERE estado = 'completada'"))
        bind.execute(sa.text("UPDATE \"Ventas\" SET estado = 'cancelled' WHERE estado = 'anulada'"))
        if not _has_constraint("Ventas", "ck_ventas_estado"):
            op.create_check_constraint("ck_ventas_estado", "Ventas", ESTADO_CHECK)
        bind.execute(sa.text("ALTER TABLE \"Ventas\" ALTER COLUMN estado SET DEFAULT 'confirmed'"))

    # 1) Canonical seeds (idempotent).
    if _has_table("maestros_canales_venta"):
        for codigo, nombre in CANALES:
            bind.execute(
                sa.text(
                    "INSERT INTO maestros_canales_venta (codigo, nombre) "
                    "VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
                ),
                {"codigo": codigo, "nombre": nombre},
            )
    if _has_table("maestros_metodos_pago"):
        for codigo, nombre in METODOS:
            bind.execute(
                sa.text(
                    "INSERT INTO maestros_metodos_pago (codigo, nombre) "
                    "VALUES (:codigo, :nombre) ON CONFLICT (codigo) DO NOTHING"
                ),
                {"codigo": codigo, "nombre": nombre},
            )

    # 2) Backfill custom values into maestros (never rewrite sales).
    if _has_table("maestros_canales_venta") and _has_column("Ventas", "canal_venta"):
        bind.execute(
            sa.text(
                'INSERT INTO maestros_canales_venta (codigo, nombre) '
                'SELECT DISTINCT v.canal_venta, v.canal_venta FROM "Ventas" v '
                "WHERE v.canal_venta IS NOT NULL AND NOT EXISTS "
                "(SELECT 1 FROM maestros_canales_venta m WHERE m.codigo = v.canal_venta) "
                "ON CONFLICT (codigo) DO NOTHING"
            )
        )
    if _has_table("maestros_metodos_pago") and _has_column("Ventas", "metodo_pago"):
        bind.execute(
            sa.text(
                'INSERT INTO maestros_metodos_pago (codigo, nombre) '
                'SELECT DISTINCT v.metodo_pago, v.metodo_pago FROM "Ventas" v '
                "WHERE v.metodo_pago IS NOT NULL AND NOT EXISTS "
                "(SELECT 1 FROM maestros_metodos_pago m WHERE m.codigo = v.metodo_pago) "
                "ON CONFLICT (codigo) DO NOTHING"
            )
        )

    # 3) Replace the canal CHECK with FKs.
    bind.execute(sa.text('ALTER TABLE "Ventas" DROP CONSTRAINT IF EXISTS ck_ventas_canal_venta'))
    if (
        _has_table("maestros_canales_venta")
        and _has_column("Ventas", "canal_venta")
        and not _has_constraint("Ventas", FK_CANAL)
    ):
        op.create_foreign_key(
            FK_CANAL,
            "Ventas",
            "maestros_canales_venta",
            ["canal_venta"],
            ["codigo"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
        )
    if (
        _has_table("maestros_metodos_pago")
        and _has_column("Ventas", "metodo_pago")
        and not _has_constraint("Ventas", FK_METODO)
    ):
        op.create_foreign_key(
            FK_METODO,
            "Ventas",
            "maestros_metodos_pago",
            ["metodo_pago"],
            ["codigo"],
            ondelete="SET NULL",
            onupdate="CASCADE",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_table("Ventas"):
        return
    bind.execute(sa.text(f'ALTER TABLE "Ventas" DROP CONSTRAINT IF EXISTS "{FK_CANAL}"'))
    bind.execute(sa.text(f'ALTER TABLE "Ventas" DROP CONSTRAINT IF EXISTS "{FK_METODO}"'))
    # Map non-canonical values back so the 5-value CHECK is recreatable.
    if _has_column("Ventas", "canal_venta"):
        bind.execute(
            sa.text(
                "UPDATE \"Ventas\" SET canal_venta = 'feria' WHERE canal_venta NOT IN "
                "('web', 'whatsapp', 'instagram', 'feria', 'showroom_pereira')"
            )
        )
        if not _has_constraint("Ventas", "ck_ventas_canal_venta"):
            op.create_check_constraint("ck_ventas_canal_venta", "Ventas", CANAL_CHECK)
    if _has_column("Ventas", "metodo_pago"):
        bind.execute(
            sa.text(
                "UPDATE \"Ventas\" SET metodo_pago = NULL WHERE metodo_pago IS NOT NULL "
                "AND metodo_pago NOT IN ('efectivo', 'transferencia', 'tarjeta', 'contraentrega')"
            )
        )
    # Restore the legacy estado domain (mirror of 98bda77 downgrade).
    if _has_column("Ventas", "estado"):
        bind.execute(sa.text('ALTER TABLE "Ventas" DROP CONSTRAINT IF EXISTS ck_ventas_estado'))
        bind.execute(sa.text("UPDATE \"Ventas\" SET estado = 'completada' WHERE estado = 'confirmed'"))
        bind.execute(
            sa.text(
                "UPDATE \"Ventas\" SET estado = 'anulada' "
                "WHERE estado IN ('cancelled', 'reversed', 'draft')"
            )
        )
        bind.execute(sa.text("ALTER TABLE \"Ventas\" ALTER COLUMN estado SET DEFAULT 'completada'"))
        op.create_check_constraint("ck_ventas_estado", "Ventas", LEGACY_ESTADO_CHECK)
