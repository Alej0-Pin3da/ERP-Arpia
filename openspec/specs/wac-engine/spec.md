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

### Requirement: REQ-WAC-001 — WAC formula with TOTAL

Engine MUST compute `nuevo=(stock*cost+qty*price)/(stock+qty)` in Decimal `NUMERIC(15,4)`. If TOTAL, `price=costo_total/qty` in Decimal before. If `stock==0`, MUST yield `nuevo==price`. MUST set `stock+=qty`, `cost=nuevo` atomically with purchase row. No FLOAT/Infinity. (Prev: no TOTAL.)

#### Scenario: SCN-WAC-001 — TOTAL + zero-stock
- GIVEN 10@5 + buy10 costo_total90 TOTAL
- WHEN WAC runs
- THEN price9 newCost7.0000 stock20; stock0+20@7→7.0000

#### Scenario: SCN-WAC-002 — Stable
- GIVEN 10@5 +10@5 UNIT
- WHEN runs
- THEN cost5.0000

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

### Requirement: REQ-WAC-002 — Edge cases precision

Denominator MUST be >0 (`qty>0` 422). `qty<=0|cost<=0|Infinity|NaN` MUST 422 before write. Decimal `NUMERIC(15,4)`; engine MUST NOT round, display-only rounding. (Prev: generic no Infinity.)

#### Scenario: SCN-WAC-003 — Rejects + precision
- GIVEN qty<=0 or Infinity or fractional WAC
- WHEN POST or stored
- THEN 422 no write; else 4 decimals preserved (e.g. 3.2308)

### Requirement: REQ-WAC-003 — Live preview contract

`ComprasForm.vue` MUST compute preview via `computed` mirroring backend: `unit=TOTAL?total/qty:unitInput; newStock=stock+qty; newWAC=(stock*cost+qty*unit)/newStock; valuation=newStock*newWAC` (JS Number display-only; backend authoritative). MUST disable Confirm if `qty<=0||cost<=0||!isFinite`. Toggle TOTAL|UNIT MUST recalc instantly. Preview MUST match backend to 4 decimals on `10@5+10@9→7.0000`. (Prev: none.)

#### Scenario: SCN-WAC-004 — Preview parity + disabled
- GIVEN 10@5 input qty10 TOTAL90
- WHEN preview computed
- THEN newStock20 newWAC7.0000 valuation140 matches backend; qty0 disables Confirm; toggle recalculates

### Requirement: REQ-WAC-004 — Atomicity and row locking

WAC MUST run in same tx as insert with `SELECT ... FOR UPDATE` on `Insumo`; commit atomically or full rollback. Concurrent same-insumo MUST serialize; different insumos MAY parallelize; lost update MUST NOT occur. Covers and extends the atomic and row-locking requirements above.

#### Scenario: SCN-WAC-005 — Concurrent
- GIVEN 2 simultaneous POSTs same insumo and distinct insumos
- WHEN run
- THEN same serializes to correct stock/cost no lost update; distinct no blocking
