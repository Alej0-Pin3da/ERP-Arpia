# costos-produccion Specification

## Purpose

Recursive production-cost computation reused by Phase 4 (explosion, margins). `GET /productos/{id}/costo` returns total plus 1-level breakdown. Arithmetic in `Decimal`, `NUMERIC(15,4)`, no engine rounding. API `/api/v1`.

## Requirements

### Requirement: Recursive memoized cost service

The system MUST provide `calcular_costo_produccion(db, producto_id, variante_id=None)` computing total cost recursively: insumo contributions `effective_quantity × Insumo.costo_promedio_actual` (waste included), combo contributions `cantidad × costo(producto_incluido)`, plus `costos_operativos_fijos` at each manufactured level. Memoization MUST be intra-call only, keyed `(producto_id, variante_id)`.

#### Scenario: Single-level insumo cost

- GIVEN insumo line qty 2, cost 5, fixed ops 10
- WHEN the cost is computed
- THEN total is 20.0000

#### Scenario: Waste included in insumo contribution

- GIVEN qty 10, waste 20%, cost 5
- WHEN the cost is computed
- THEN the insumo contribution is 60.0000

#### Scenario: Multilevel combo cost

- GIVEN A includes B (qty 2), B costs 30, fixed ops 10
- WHEN A's cost is computed
- THEN total is 70.0000

#### Scenario: Shared subproduct computed once

- GIVEN A and C both include B; B costs 30
- WHEN A's cost is computed in one call
- THEN B's subtree is evaluated once

#### Scenario: Variant override used in cost

- GIVEN variant 3 has a variant line and a NULL base line
- WHEN cost is computed for variant 3
- THEN the variant quantity is used (not summed)

#### Scenario: Base rule fallback

- GIVEN variant 2 has no variant-specific lines
- WHEN cost is computed for variant 2
- THEN the NULL base rules apply

### Requirement: Cycle detection

The engine MUST track `producto_id` paths during recursion; a reappearing product MUST abort with 409 and no result.

#### Scenario: Direct cycle

- GIVEN A includes B and B includes A
- WHEN A's cost is computed
- THEN the engine raises 409 and no total

### Requirement: Non-fabricated or no-BOM cost rule

When `requiere_fabricacion` is False OR no BOM rows exist, the total MUST equal `costos_operativos_fijos` with a single-line breakdown. BOM traversal MUST happen only when `requiere_fabricacion` is True.

#### Scenario: Non-fabricated product

- GIVEN `requiere_fabricacion` False, `costos_operativos_fijos` 15
- WHEN the cost is computed
- THEN total is 15.0000 with a single-line breakdown

#### Scenario: Fabricated product without BOM

- GIVEN `requiere_fabricacion` True, `costos_operativos_fijos` 15, no BOM rows
- WHEN the cost is computed
- THEN total is 15.0000 with a single-line breakdown

### Requirement: Cost endpoint

The system MUST expose `GET /productos/{id}/costo` (audited_user) returning `total` and `lineas[]`, one entry per direct BOM line; combo lines MUST carry their full recursive cost. Missing product MUST 404; detected cycle MUST 409.

#### Scenario: Endpoint returns total and breakdown

- GIVEN a two-level BOM for product 1
- WHEN `GET /productos/1/costo`
- THEN 200 returns `total` and one line per direct BOM row

#### Scenario: Missing product

- GIVEN no product with `id` 999
- WHEN `GET /productos/999/costo`
- THEN 404 is returned

#### Scenario: Cycle via endpoint

- GIVEN a BOM cycle reachable from product 1
- WHEN `GET /productos/1/costo`
- THEN 409 is returned

#### Scenario: Any authenticated role may read

- GIVEN a `consulta` token and an existing product
- WHEN `GET /productos/1/costo`
- THEN 200 is returned

### Requirement: Read-only, Phase 4 reuse contract

The engine MUST perform only reads (no `SELECT ... FOR UPDATE` of its own) and MUST be callable inside a Phase 4 transaction with `FOR UPDATE` locks. Arithmetic MUST use `Decimal` with `NUMERIC(15,4)`; no rounding in the engine, MAY round only at presentation.

#### Scenario: Callable inside a locked transaction

- GIVEN a Phase 4 transaction with `FOR UPDATE` locks on insumo rows
- WHEN `calcular_costo_produccion` is called inside it
- THEN it computes with no extra locks or commits

#### Scenario: Precision preserved in engine

- GIVEN a fractional cost sum
- WHEN the engine computes it
- THEN intermediate totals keep 4 decimals, no engine rounding
