"""Purge ghost Insumos from unreal 'INVENTARIO OCT25' sheet (owner-confirmed).

Ghost signature: Insumos.nombre LIKE '*%' (8 rows: 2 argollas + 3 ochos +
3 gancho-G). Source data is not real: F1 catalog.py read OCT25 columns B/F
verbatim and F4 stock.py set snapshot stock, while F2 purchases.py only reads
VALQUI/MARGARA so costo stayed 0.

Safe order (RESTRICT FKs are the safety net):
  Phase 1 (BOM_Insumos): verified 0 ghost lines before upgrade; upgrade
    aborts if any exist (delete them via DELETE /productos/{id}/bom/insumos/{linea_id}).
  Phase 2 (this migration): COPY ghost Compras_Insumos rows (2) into a backup
    table, then DELETE them. No API DELETE exists for compras (POST+GET only).
  Phase 3 (after this migration): DELETE each ghost insumo via admin
    DELETE /insumos/{id} (bare delete; RESTRICT blocks orphans).

Rollback: downgrade re-inserts the compras rows from the backup table.
Backup tables are kept (audit trail, never dropped).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0029_purge_ghost_oct25"
down_revision: str | None = "0028_backfill_provenance"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

BACKUP_COMPRAS = "backup_compras_ghost_oct25"
BACKUP_INSUMOS = "backup_insumos_ghost_oct25"
# '*' is a literal in LIKE (only % and _ are wildcards).
GHOST_PREDICATE = """"Insumos".nombre LIKE '*%'"""


def _count(sql: str) -> int:
    return int(op.get_bind().execute(sa.text(sql)).scalar() or 0)


def upgrade() -> None:
    bom_lines = _count(
        f'''SELECT count(*) FROM "BOM_Insumos" bi
            JOIN "Insumos" ON "Insumos".id = bi.insumo_id
            WHERE {GHOST_PREDICATE}'''
    )
    if bom_lines:
        raise RuntimeError(
            f"Refusing purge: {bom_lines} BOM_Insumos lines still reference ghost "
            "insumos; delete them via DELETE /productos/{id}/bom/insumos/{linea_id} first."
        )
    op.execute(sa.text(f'DROP TABLE IF EXISTS "{BACKUP_COMPRAS}"'))
    op.execute(
        sa.text(
            f'''CREATE TABLE "{BACKUP_COMPRAS}" AS
                SELECT ci.* FROM "Compras_Insumos" ci
                JOIN "Insumos" ON "Insumos".id = ci.insumo_id
                WHERE {GHOST_PREDICATE}'''
        )
    )
    op.execute(sa.text(f'DROP TABLE IF EXISTS "{BACKUP_INSUMOS}"'))
    op.execute(
        sa.text(
            f'''CREATE TABLE "{BACKUP_INSUMOS}" AS
                SELECT * FROM "Insumos" WHERE nombre LIKE '*%' '''
        )
    )
    backed_compras = _count(f'SELECT count(*) FROM "{BACKUP_COMPRAS}"')
    live_compras = _count(
        f'''SELECT count(*) FROM "Compras_Insumos" ci
            JOIN "Insumos" ON "Insumos".id = ci.insumo_id
            WHERE {GHOST_PREDICATE}'''
    )
    if backed_compras != live_compras:
        raise RuntimeError(
            f"Backup mismatch: backed {backed_compras} vs live {live_compras} ghost compras."
        )
    op.execute(
        sa.text(
            f'''DELETE FROM "Compras_Insumos" ci
                USING "Insumos"
                WHERE ci.insumo_id = "Insumos".id AND {GHOST_PREDICATE}'''
        )
    )
    remaining = _count(
        f'''SELECT count(*) FROM "Compras_Insumos" ci
            JOIN "Insumos" ON "Insumos".id = ci.insumo_id
            WHERE {GHOST_PREDICATE}'''
    )
    if remaining:
        raise RuntimeError(f"Purge incomplete: {remaining} ghost compras remain.")


def downgrade() -> None:
    op.execute(
        sa.text(
            f'''INSERT INTO "Compras_Insumos"
                SELECT * FROM "{BACKUP_COMPRAS}"
                ON CONFLICT DO NOTHING'''
        )
    )
