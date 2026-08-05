# Proposal: WAC — Cost Engine & Purchase Registration

## Intent

Phase 2. `Insumos.costo_promedio_actual` exists but nothing updates it: there is no purchase registration endpoint, so inventory cost is stale and Phase 4's `costo_unitario_aplicado` snapshots lack a trustworthy source. We deliver the first write path over `Insumos.stock_actual` / `costo_promedio_actual`, atomic and race-safe.

## Scope

### In Scope
- `POST /api/v1/compras-insumos`: register a `CompraInsumo` (proveedor optional, validated if present).
- WAC engine: same-transaction update of `stock_actual += cantidad` and `costo_promedio_actual` via the WAC formula, with `SELECT ... FOR UPDATE` on the insumo row.
- `GET /api/v1/compras-insumos`: paginated list, optional `insumo_id` filter.
- Tests (strict TDD first): WAC response to price fluctuations; concurrent purchases.

### Out of Scope / Non-Goals
- No sale/explosion (Phase 4), BOM cost (Phase 3), returns, `stock_minimo` report (Phase 5), UI.
- No edits to existing models, README, `.env`, migrations.

## Capabilities

Contract with sdd-spec. `openspec/specs/` is empty — all capabilities new.

### New Capabilities
- `compras-insumos`: register and list insumo purchase records.
- `wac-engine`: weighted-average cost recomputation on purchase, transactional with row locking.

### Modified Capabilities
- None.

## Approach

- New `app/api/routes/compras_insumos.py` (follow `insumos.py`), registered in `router.py`.
- New schemas `app/schemas/compra_insumo.py`: `CompraInsumoCreate`, `CompraInsumoRead`.
- POST flow: validate insumo/proveedor → `select(Insumo).where(id==...).with_for_update()` → compute new cost in `Decimal` → update stock and cost → single commit, rollback on any failure.
- Row lock serializes same-insumo purchases; different insumos run in parallel.

## Unit-handling Stance (meters master)

Textiles are bought in metres, consumed in centimetres (BOM). For this phase:
- `unidad_medida` is the master unit; purchase quantity is recorded in that unit.
- No conversion factor now: WAC math stays single-unit. cm→m conversion is deferred to Phase 3 (BOM), where a master-unit + factor design belongs.

## Business Rules & Edge Cases

- Division by zero impossible: `cantidad` is `gt=0` (denominator `stock + cantidad > 0`). If `stock == 0`, new cost equals `precio_unitario` (correct).
- `precio_unitario_compra` `ge=0`; zero/negative quantities rejected before DB.
- `proveedor_id` optional (FK `SET NULL`); `insumo_id` required (FK `RESTRICT`).
- Precision: `Numeric(15,4)` everywhere; round to 2dp only at presentation, never in the engine.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Decimal drift in WAC | Med | Decimal + `Numeric(15,4)`; quantize only at presentation |
| Lost update on concurrent purchases | Low | `FOR UPDATE` + single transaction |
| Shared test DB collisions | Med | Reuse existing fixtures; unique names |

## Rollback Plan

Revert the router include and delete the new files (`compras_insumos.py`, `compra_insumo.py`, test file). No schema change or data migration — additive change only.

## Dependencies

- Phase 1 modules (`Insumo`, `CompraInsumo`, `Proveedor`; `require_roles`, `get_db`).

## Open Questions

- `GET /compras-insumos` also filter by `fecha_compra` range? (Default: no, only `insumo_id`.)

## Success Criteria

- [ ] Green pytest integration tests against real PostgreSQL (existing harness).
- [ ] Purchase atomically updates `stock_actual` and `costo_promedio_actual`.
- [ ] Concurrency test proves serialized WAC with no lost updates.