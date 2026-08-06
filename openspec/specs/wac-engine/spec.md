# wac-engine Specification

## Purpose

Weighted-average-cost (WAC) cost recomputation triggered when a purchase is registered. Runs inside the purchase transaction with row locking so concurrent purchases of the same insumo cannot corrupt stock or cost. API prefix `/api/v1`. Money and quantities `NUMERIC(15,4)`.

## Requirements

### Requirement: Atomic WAC in the purchase transaction

The WAC recomputation SHALL run inside the SAME transaction as the `CompraInsumo` insert and MUST commit atomically. On any failure the entire transaction MUST roll back, leaving stock, cost, and the purchase row unchanged (no partial write).

#### Scenario: Atomic commit

- GIVEN a valid purchase for an insumo
- WHEN the purchase is posted
- THEN the purchase row, `stock_actual`, and `costo_promedio_actual` change in one commit

#### Scenario: All-or-nothing rollback

- GIVEN a write error after stock/cost has been staged
- WHEN the patch fails
- THEN the transaction rolls back and the insumo and purchases show no change

### Requirement: Weighted-average cost formula

The engine MUST compute `nuevo_costo = (stock_actual * costo_promedio_actual + cantidad_comprada * precio_unitario_compra) / (stock_actual + cantidad_comprada)` in `Decimal`. The engine MUST set `stock_actual = stock_actual + cantidad_comprada` and `costo_promedio_actual = nuevo_costo`.

#### Scenario: Equal unit price keeps cost stable

- GIVEN 10 units at cost 5, then a purchase of 10 at price 5
- WHEN the WAC runs
- THEN `costo_promedio_actual` stays 5.0000

#### Scenario: Price fluctuation moves the average

- GIVEN 10 units at cost 5 and a purchase of 10 units at price 9
- WHEN the WAC runs
- THEN `stock_actual` is 20.0000 and `costo_promedio_actual` is 7.0000

#### Scenario: Cost rises on higher-priced lot

- GIVEN 100 units at 5 and 50 units bought at 8
- WHEN the WAC runs
- THEN `costo_promedio_actual` becomes 6.0000

### Requirement: Row locking for concurrency

Before reading `stock_actual` and `costo_promedio_actual` the engine MUST `SELECT ... FOR UPDATE` the targeted `Insumo` row within the transaction. Concurrent purchases of the SAME insumo MUST serialize on that row lock; purchases of DIFFERENT insumos MAY proceed in parallel. The system MUST never produce a lost update.

#### Scenario: Concurrent same-insumo purchases stay consistent

- GIVEN two simultaneous purchases of the same insumo
- WHEN both run
- THEN the resulting stock and cost equal the value of running the two transactions serially, with no lost update

#### Scenario: Different insumos run in parallel

- GIVEN purchase targets two distinct `Insumo` rows
- WHEN both run concurrently
- THEN row locks on distinct rows do not block each other

#### Scenario: Concurrency test requirement

- Test MUST issue concurrent POSTs for the same insumo and MUST assert final stock+cost equals the expected serialized result and no lost update occurs

### Requirement: Edge cases and precision

The denominator `stock_actual + cantidad_comprada` MUST always be > 0 because `cantidad_comprada` is enforced > 0. When `stock_actual == 0`, the formula MUST yield `nuevo_costo == precio_unitario_compra`. All arithmetic MUST use `Decimal` with `NUMERIC(15,4)` storage and MUST NOT round inside the engine; rounding MAY occur only at presentation. Non-positive or otherwise invalid purchase values MUST be rejected (400/422) BEFORE any DB write.

#### Scenario: Zero prior stock

- GIVEN an insumo with zero stock and a purchase of 20 at price 7
- WHEN the WAC runs
- THEN `costo_promedio_actual` equals 7.0000

#### Scenario: Precision preserved

- GIVEN a purchase whose WAC result has a fractional value
- WHEN stored
- THEN cost is stored to 4 decimal places with no rounding at the engine layer

#### Scenario: Precondition before writes

- GIVEN a nonexistent `Insumo` or invalid quantity
- WHEN posting the purchase
- THEN the system returns 404/422 and writes nothing