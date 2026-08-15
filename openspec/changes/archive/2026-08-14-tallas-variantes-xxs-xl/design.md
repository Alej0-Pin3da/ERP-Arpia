# Design: Tallas de variantes (XXS–XL)

## Technical Approach

Data-catalog + migration-wiring + frontend hardening, no schema change (no Alembic). F1 seeds 30 variants and the missing Set Celeno product through the existing `upsert_producto`; F5 gains an omit+report path for size-less rows of sized products (before the `explosion_materiales` root guard) and one-direction NULL-matching idempotency; F7 mirrors both; VentasForm requires a variant on any line whose product has variants. Implements MIG-1..MIG-5 (migracion-catalogos spec) and VV-1..VV-4 (ventas-variantes spec).

Verified against code: `ProductoPlan` already carries `variantes`; `upsert_producto` already accepts `precio_sugerido` — the missing piece is `aplicar_plan` never forwarding it (spec-agent WARNING). `_productos_del_plan` (validate.py:209) derives products from BOM+ventas only, so Set Celeno would be invisible to N7a — it MUST include `plan.catalogo.productos` or N7a reports 13/13 (MIG-5 breach).

## Architecture Decisions

| # | Decision | Options considered | Choice & rationale |
|---|----------|-------------------|--------------------|
| D1 | Price plumbing: add `precio_sugerido: Decimal \| None = None` to frozen `ProductoPlan`; `plan_catalogo` maps `precio_venta_sugerido` from the entry; `aplicar_plan` forwards it to `upsert_producto`. `upsert_producto` sets `precio_venta_sugerido` on create AND refreshes it on the existing-product path **only when `precio_sugerido is not None`** (idempotent re-run, catalog is source of truth; existing callers pass None → unchanged). | (a) leave `upsert_producto` create-only; (b) new standalone Set Celeno upsert call. | (a) would not self-heal a wrong price on re-run; (b) bypasses the plan (dry-run/`aplicar_plan` divergence). D1 keeps one code path. |
| D2 | F5 omit predicate (MIG-3), evaluated in the **step-1 resolution loop** of `aplicar_ventas` (sales.py:457-473) right after `variante_id = _variante_por_nombre(...)`, before `esperadas[...] += 1` / `resueltas.append(...)`: `variante_id is None AND producto.variantes (non-empty) AND tipo != "Combo"` → `res["omitidas"] += 1`, `report.warn(...)`, `continue`. | (a) omit at explosion time; (b) invent default variant. | (a) would still raise `DomainValidationError` from `inventory.py:61-62`; (b) forbidden by VTA-4/EXM-2. Omitting in step 1 keeps omitted lines out of `esperadas`/`resueltas`, so they never explode and never count as ya_presentes. Explicit combo check: combos have no variants anyway, but the check future-proofs and documents intent (combo rows carry sizes in B..F that resolve None). |
| D3 | F5 idempotency (MIG-4): `_contar_existentes` (sales.py:346-368) — when the plan line resolves a variant, the SQL matches `variante_id == X OR variante_id IS NULL`; when it resolves None, only `variante_id IS NULL` (one-direction). Shared pure predicate `variante_coincide(plan, db)` exported from sales.py, used by N7g too so F5/F7 never drift. | (a) backfill UPDATE of existing rows; (b) delete+reinsert. | (a)/(b) rejected in proposal Decision 4 (self-contained, no row-identity loss). NULL-matching keeps the 21 historical NULL rows valid forever; the `esperadas` Counter semantics stay "insert only missing rows" (NULL row counts as one of the expected). Documented conservative edge: two plan lines with same (fecha,producto,precio) but different variants NULL-match the same NULL rows → over-count skips one insert on re-run; not present in the 21-row data. |
| D4 | N7g omit-awareness + NULL-matching (MIG-5): **do NOT filter the 2 omitted lines from `plan_ventas`** — they stay with None-variant keys. DB rows keyed with the normalized variant name-or-None; comparison uses `variante_coincide` per key. | (a) remove omitted lines from plan counts ("gone from plan"); (b) plain equality only. | (a) is the false-positive trap the spec-agent WARNING flags: DB rows exist (NULL) while plan count → 0 → `1 > 0` → false "venta duplicada". (b) leaves variant NULL-matching out → re-run state (21 NULL rows vs variant plan keys) still clean by luck, but the semantic is incomplete. D4 keeps plan raw + one-direction NULL-matching → both the 19+2 fresh state and the 21-NULL re-run state validate clean. Also fixes a latent bug: DB variant keys were raw ("S") vs plan keys normalized ("s") → never matched; normalize the DB side. |
| D5 | N7a productos 14/14 (MIG-5): `_productos_del_plan` (validate.py:209-213) adds `{normalizar_nombre(p.nombre) for p in plan.catalogo.productos}` to the BOM∪ventas union. | keep BOM∪ventas + special-case Set Celeno. | The "productos" domain IS the catalog; the plan's `CatalogPlan` is the authoritative universe (F1 = catalog). Special-casing one product is arbitrary. Cost: mini-workbook N7a tests under-seed (1 product) → `_preparar_entorno` must seed the full catalog and module cleanup must remove it before `TipoProducto` cleanup (FK). |
| D6 | Frontend required-variant (VV-1..VV-4): pure helpers `requiereVariante(row, variantes)` and `detallesSinVariante(detalles, cache)` in `utils/ventas.ts`; `VentasForm.submit()` awaits in-flight loads (idempotent, cached) then blocks with `ElMessage.warning` and no emit when any sized row lacks a variant; the select is `:disabled` when `variantesDe(row).length === 0`. | validate only in backend (400 guard). | Backend 400 exists but UX must block client-side before payload (VV-1). Awaiting loads closes the race where submit fires before `loadVariantesFor` resolves (cache miss → select briefly disabled). Same path covers create AND edit mode (prefill feeds `detalles`; a sized detail prefilled with `variante_id: null` is blocked until a variant is chosen). |

## Data Flow

```
F1 catalog            F5 sales                            F7 validate
PRODUCTOS_CATALOGO     VENTAS CSV (21 rows)                plan_para_validacion
  +variantes tuples     plan_ventas -> VentasPlan           + plan.catalogo (14 productos)
  +Set Celeno@75000     aplicar_ventas:                     checks_n7:
  │                      1) resuelve ids ── omit?──▶ warn  N7a productos 14/14
  │                      2) _contar_existentes              N7g plan raw + variante_coincide
  │                         (NULL-match, 1-direction)       (NULL rows matchean; omitidos no
  │                      3) inserta faltantes + explosion      se filtran del plan)
  │                      4) destock batch                  N7b..N7f sin cambio
  ▼
Variante_Producto      Detalle_Ventas (19-21 filas)
(precio_venta NULL)
```

MIG-3 report entry (goes to JSON trace AND `Migracion_Omisiones` via `omisiones.py`, which persists WARN/ERROR):
`report.warn(venta.hoja, venta.fila, COL_PRODUCTO, f"{venta.producto_nombre}: sin talla fecha {venta.fecha.date()} qty {venta.cantidad} -> omitida (MIG-3: producto con variantes, fila sin talla)")`. The 2 known rows are identified **generically** by the predicate — no hardcoding: SET OCIPETE 28/3 and BLUSA ARPIA MANGA LARGA 5/8 are the only plan lines that match (sized product, no size cell, not combo).

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/migrate/catalog.py` | Modify | `PRODUCTOS_CATALOGO`: `variantes=("XXS","XS","S","M","L","XL")` on Set Aelo, Set Ocipete, Blusa Manga Larga, Blusa Manga Corta; NEW entry `{"nombre":"Set Celeno","tipo":"Set","precio_venta_sugerido":75000,"variantes":(6 tallas)}` (count 13→14). `ProductoPlan` += `precio_sugerido: Decimal\|None = None`. `plan_catalogo` maps it. `aplicar_plan` forwards `precio_sugerido` + reports it. `upsert_producto`: refresh price on existing product when `precio_sugerido is not None`. |
| `backend/migrate/sales.py` | Modify | `or_` import. `variante_coincide(plan, db)` pure helper (exported). Omit predicate + report in `aplicar_ventas` step 1. `_contar_existentes` NULL-matching branch. |
| `backend/migrate/validate.py` | Modify | `_productos_del_plan` += catalog products. `_n7g_idempotencia` ventas section: normalize DB variant names; compare per key with `variante_coincide`; keep omitted lines in plan (docstring the why). |
| `frontend/src/utils/ventas.ts` | Modify | Add `requiereVariante(row, variantes): boolean` and `detallesSinVariante(detalles, variantesPorProducto): VentasFormDetalle[]` (exported). |
| `frontend/src/components/ventas/VentasForm.vue` | Modify | Variante select `:disabled="variantesDe(row).length === 0"`; `submit()` awaits loads, then blocks on `detallesSinVariante` with warning (no emit). Works in create + edit mode. |
| `backend/tests/test_migrate_catalog.py` | Modify | 13→14 aware (existing `len(PRODUCTOS_CATALOGO)` asserts auto-adapt); new variant/price tests. |
| `backend/tests/test_migrate_sales.py` | Modify | New omit + NULL-matching idempotency tests (fixture row: sized product without size). |
| `backend/tests/test_migrate_validate.py` | Modify | `_preparar_entorno` seeds full catalog; cleanup removes the 14 canonical products before tipos; N7a/N7g variant tests. |
| `frontend/tests/unit/ventas.spec.ts` | Modify | `requiereVariante` / `detallesSinVariante` cases. |
| `frontend/tests/component/ventas-form.spec.ts` | Modify | VV-1..VV-3 submit-block/emit cases incl. edit mode. |

## Interfaces / Contracts

```python
# catalog.py — plan carries the price (frozen dataclass, default keeps old callers compiling)
@dataclass(frozen=True)
class ProductoPlan:
    nombre: str
    tipo: str
    variantes: tuple[str, ...] = ()
    precio_sugerido: Decimal | None = None

# sales.py — single source of truth for the NULL-matching semantic (MIG-4 + MIG-5)
def variante_coincide(plan: int | str | None, db: int | str | None) -> bool:
    """One-direction: a plan line resolving a variant matches an existing NULL
    row; a NULL plan line matches only NULL rows."""
    if plan is None:
        return db is None
    return db is None or db == plan

# sales.py — _contar_existentes, variante branch (plan_id = resolved variant id)
if variante_id is None:
    stmt = stmt.where(DetalleVenta.variante_id.is_(None))
else:
    stmt = stmt.where(or_(DetalleVenta.variante_id == variante_id,
                          DetalleVenta.variante_id.is_(None)))

# sales.py — omit hook inside the step-1 resolution loop (after variante_id resolved)
if (
    variante_id is None
    and producto.variantes
    and not (producto.tipo_producto is not None and producto.tipo_producto.nombre == "Combo")
):
    res["omitidas"] += 1
    if report:
        report.warn(venta.hoja, venta.fila, COL_PRODUCTO,
            f"{venta.producto_nombre}: sin talla fecha {venta.fecha.date()} "
            f"qty {venta.cantidad} -> omitida (MIG-3: producto con variantes, fila sin talla)")
    continue  # nunca entra a esperadas/resueltas -> nunca explota

# validate.py — N7g ventas comparison (per plan key)
# db rows fetched as (fecha, producto, vid, cantidad, precio); variantes map = normalized
variantes = {vid: clave_normalizada(n) for vid, n in db.query(VarianteProducto.id, VarianteProducto.nombre_variante).all()}
# plan key: (fecha.date(), clave_normalizada(producto), variante_norm|None, cantidad, _moneda(precio))
# DB side keyed by the SAME shape; counts via: variante_coincide(plan_variante, db_variante)
def _cuenta_db_para(plan_clave, prefix_counts): ...  # exact when plan None; exact+NULL when set
# omitted lines are NOT removed from plan_ventas (they carry None variant -> match NULL rows 1:1)

# frontend/src/utils/ventas.ts
export function requiereVariante(row: VentasFormDetalle, variantes: VarianteProductoRead[]): boolean {
  return row.producto_id !== null && variantes.length > 0
}
export function detallesSinVariante(
  detalles: VentasFormDetalle[],
  variantesPorProducto: Record<number, VarianteProductoRead[]>,
): VentasFormDetalle[] {
  return detalles.filter((d) =>
    d.producto_id !== null &&
    d.variante_id === null &&
    (variantesPorProducto[d.producto_id] ?? []).length > 0,
  )
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Backend unit/DB | MIG-1: 30 variants, `precio_venta` NULL, dedup on re-run, non-sized products get 0 | `test_migrate_catalog.py`: plan from REAL xlsx asserts 5 sized × 6 = 30; `upsert_producto` twice with duplicates → 6 rows; Corset Garras/combos → 0. |
| Backend unit/DB | MIG-2: Set Celeno @75000, count 13→14, re-run price stable | New: plan asserts 14 products + Set Celeno price; `aplicar_plan` → DB `precio_venta_sugerido == 75000`; re-apply keeps it. |
| Backend integration | MIG-3: size-less sized row omitted + reported; no invented variant; combo with sizes NOT omitted | `test_migrate_sales.py`: new mini row `P_SET` without size → `res["omitidas"] == 1`, other row inserted, 0 detalle for omitted, no explosion; re-run idempotent. Existing combo test (no-size combo row) must stay green. |
| Backend integration | MIG-4: NULL row matches variant plan key; NULL plan matches only NULL DB | Re-run with manually inserted NULL-variant detail → 0 new inserts; combo (None) does not match a variant DB row. |
| Backend integration | MIG-5: N7a productos 14/14; N7g clean with omitted rows present in DB + variant NULL-matching | `test_migrate_validate.py`: seed full catalog; assert N7a pieza "productos 14/14"; DB with 2 NULL size-less rows + variant rows → N7g OK; plan variant key vs NULL DB row → OK. |
| Frontend unit | VV-1/VV-2/VV-4 predicates | `ventas.spec.ts`: `requiereVariante` (no product → false; 0 variants → false; ≥1 → true); `detallesSinVariante` (sized missing → returned; sized chosen → not; variant-less → not). |
| Frontend component | VV-1..VV-3 submit-block + emit; edit mode | `ventas-form.spec.ts`: sized product no variant → warning + no emit; sized + variant → emit with `variante_id`; variant-less → emit without; empty line select disabled; edit prefill sized-with-null-variant blocked until chosen. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. Data migration + Vue form hardening only.

## Migration / Rollout

No schema migration (no Alembic). Data-only, ordered: F1 (seed variants + Set Celeno) → F5 (omit 2 + idempotent re-run) → F7. Rollback (per proposal): delete Set Celeno + its variants (no FK refs yet), re-run F1 to re-seed, omit+report is policy not persistence — a failed run rolls back per-`session_scope` (EXM-4). Frontend ships independently; backend 400 guard remains the safety net if the client blocks wrongly.

## Open Questions

- None blocking. Note: N7a "productos" esperados broadening is a semantic widening of the check (catalog universe), chosen deliberately for MIG-5 — mini-workbook N7a tests must be updated in the SAME change as `_productos_del_plan` (D5) or they break.
