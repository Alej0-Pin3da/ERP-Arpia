# Proposal: Product Engineering & Multilevel BOM — Phase 3

## Intent

Phase 3 of the ARPIA roadmap. The data layer already exists (5 models in `backend/app/models/productos.py`, tables created by migration 0001) but there is no API surface and no cost engine: products cannot be managed and their production cost cannot be computed. We deliver the Product/Tipo/Variante CRUD, the recipe management (BOM insumos + combos), and the recursive memoized production-cost engine that Phase 4 will reuse for inventory explosion and margin snapshots — no duplicated logic.

## Scope

### In Scope
- CRUD: `Productos`, `Tipos_Producto`, `Variantes_Producto` (variantes nested under the product).
- Recipes: `BOM_Insumos` (variante-specific, with waste) and `BOM_Productos` (combos) nested under the product.
- Cost engine: recursive, intra-call memoized service + `GET /productos/{id}/costo` (total + 1-level breakdown).
- Tests (strict TDD): service-level against real PostgreSQL, endpoint-level with tokens.

### Out of Scope
- No migration 0003, no conversion-factor column (see decision 2).
- No sales/explosion (Phase 4), no product purchases, no UI, no margin snapshots, no `DetalleVenta` changes.
- No changes to existing models, specs, or archived Phase 2 behavior.

## Capabilities

Contract for sdd-spec. Existing specs: `wac-engine`, `compras-insumos` (unchanged).

### New Capabilities
- `productos`: CRUD for Tipos_Producto, Productos, Variantes_Producto + nested routing.
- `bom`: recipe management — BOM_Insumos (variante_id + porcentaje_desperdicio), BOM_Productos (combos), duplicate-rule validation.
- `costos-produccion`: recursive memoized cost service + cost endpoint (total + 1-level breakdown), cycle detection, Phase 4 reuse contract.

### Modified Capabilities
- None.

## Approach

### Resolved Decisions (7 open questions from explore)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Mutations (Productos/Tipos/Variantes/BOM): `require_admin`; GET: `audited_user` | Masters = admin (matches `insumos.py`/`categorias_insumos.py`); operators keep transactional power (compras = admin\|operador). Clean masters-vs-transactions principle. |
| 2 | `cantidad_requerida` expressed in the insumo's master unit (`unidad_medida`); NO migration 0003 | WAC is single-unit; recipes in master unit keep the engine simple and consistent with Phase 2's stance. A factor column is the documented escape hatch if mixed-unit recipes are ever required. |
| 3 | `porcentaje_desperdicio` = 0–100 percent, validated `ge=0 le=100`; applies ONLY to `BOM_Insumos`; effective qty = `cantidad_requerida × (1 + pct/100)` | Percent matches the operator's mental model; `BOM_Productos` has no waste column (adding it would force migration — not needed for combos). |
| 4 | `requiere_fabricacion=False` OR no BOM rows → total = `costos_operativos_fijos` (breakdown: single line). BOM traversed only when `requiere_fabricacion=True` | No other cost source exists (product purchases out of scope). Explicit, testable rule. |
| 5 | Cost endpoint always returns total + 1-level breakdown (each direct BOM line; sub-product lines carry their full recursive cost) | UI debuggability now; deeper recursion folded into line totals. No query param needed. |
| 6 | Nested: `/productos/{id}/variantes`, `/productos/{id}/bom/insumos`, `/productos/{id}/bom/productos`; flat: `/tipos-producto`, `/productos` (paginated limit/offset), cost at `/productos/{id}/costo` | Children have no standalone meaning; nesting matches existing REST style; top-level lists follow `compras_insumos.py` pagination. |
| 7 | Variante semantics: `variante_id NULL` = base rule applying to ALL variants; `variante_id=X` OVERRIDES it for variant X. Service validates no duplicate NULL `(producto_id, insumo_id)` rows | Postgres `NULL != NULL` defeats the unique constraint — validate in service. Override (not sum) is the intuitive recipe-editor model. |

> These are pragmatic defaults; product-facing ones (roles, waste cap, override semantics, non-fabricated cost rule) are flagged for user confirmation at proposal review.

### Architecture

- Schemas: `backend/app/schemas/producto.py` (Tipo/Producto/Variante Base/Create/Update/Read, `ConfigDict(from_attributes=True)`, Decimal `ge=0/gt=0`), `bom.py` (BomInsumo/BomProducto Create/Update/Read), `costo.py` (CostoProduccionRead: `total` + `lineas[]` 1-level).
- Routers: `tipos_productos.py`, `productos.py` (+ nested variantes), `bom.py` (nested), `costos.py` — registered in `router.py` under `/api/v1`. Errors: 404 "not found", 400 FK inválido, 422 validation, 409 conflicts/cycles.
- Service `backend/app/services/costos.py`: `calcular_costo_produccion(db, producto_id, variante_id=None)` — recursive; intra-call memo dict keyed `(producto_id, variante_id)`; path-stack cycle detection on `producto_id` → 409; reads `Insumo.costo_promedio_actual` + `costos_operativos_fijos`; adds `costos_operativos_fijos` at each manufactured level. Read-only (no FOR UPDATE) but callable from Phase 4 transactions; Decimal `NUMERIC(15,4)`, quantize only at presentation; memoization NEVER across calls (`costo_promedio_actual` changes).
- Tests: `test_productos.py`, `test_bom.py`, `test_costos.py` — duplicate NULL rule, variante override/fallback, waste math, multilevel cost, shared-subproduct memoization (computed once per call), cycle → 409, no-BOM/non-fabricated → fixed cost, auth 401/403.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/api/routes/productos.py` | New | CRUD Producto + nested variantes |
| `backend/app/api/routes/tipos_productos.py` | New | CRUD Tipo_Producto |
| `backend/app/api/routes/bom.py` | New | Nested BOM insumos/productos CRUD |
| `backend/app/api/routes/costos.py` | New | `GET /productos/{id}/costo` |
| `backend/app/api/router.py` | Modified | Register 4 new routers |
| `backend/app/schemas/producto.py`, `bom.py`, `costo.py` | New | Pydantic schemas |
| `backend/app/services/costos.py` | New | Recursive memoized cost engine |
| `backend/tests/test_productos.py`, `test_bom.py`, `test_costos.py` | New | Service + endpoint tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| BOM cycles (A→B→A) crash the engine | Med | Path-stack cycle detection → 409 + dedicated test |
| Duplicate NULL-variant BOM rows | Med | Service validation + test |
| Decimal drift in recursive sums | Low | Decimal + NUMERIC(15,4) everywhere, quantize only at presentation |
| Deep recursion stack overflow | Low | Cycle detection bounds depth; iterative DFS if needed |
| Change exceeds 400-line review budget | High | sdd-tasks must plan chained PRs per deliverable (productos → bom → costos) |

## Rollback Plan

Additive-only change: no migrations, no model edits. Revert by removing the 4 router includes in `router.py` and deleting the new schemas/routers/service/test files. Data created via the new endpoints remains consistent (plain rows; no cross-table invariants beyond FK RESTRICT).

## Dependencies

- Phase 1 models (migration 0001 — tables exist) and Phase 2 WAC (`Insumos.costo_promedio_actual`).

## Success Criteria

- [ ] `pytest backend/tests -q` green (existing 24 + new suites).
- [ ] All CRUD endpoints enforce authz (401/403) and errors (404/400/422/409).
- [ ] Cost engine: multilevel BOM + waste + variante override/fallback + shared subproduct computed once per call + cycle → 409.
- [ ] `GET /productos/{id}/costo` returns total + 1-level breakdown; non-fabricated/no-BOM returns `costos_operativos_fijos`.
