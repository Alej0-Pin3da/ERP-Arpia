# Delta for wac-engine

## MODIFIED Requirements

### Requirement: REQ-WAC-001 — WAC formula with TOTAL
Engine MUST compute `nuevo=(stock*cost+qty*price)/(stock+qty)` in Decimal NUMERIC(15,4). If TOTAL, `price=costo_total/qty` in Decimal before. If stock==0, MUST yield `nuevo==price`. MUST set `stock+=qty`, `cost=nuevo` atomically with purchase row. No FLOAT/Infinity. (Prev: no TOTAL.)
#### Scenario: SCN-WAC-001 — TOTAL + zero-stock
- GIVEN 10@5 + buy10 costo_total90 TOTAL
- WHEN WAC runs
- THEN price9 newCost7.0000 stock20; stock0+20@7→7.0000
#### Scenario: SCN-WAC-002 — Stable
- GIVEN 10@5 +10@5 UNIT
- WHEN runs
- THEN cost5.0000

### Requirement: REQ-WAC-002 — Edge cases precision
Denominator MUST be >0 (qty>0 422). qty<=0|cost<=0|Infinity|NaN MUST 422 before write. Decimal NUMERIC(15,4); engine MUST NOT round, display-only rounding. (Prev: generic no Infinity.)
#### Scenario: SCN-WAC-003 — Rejects + precision
- GIVEN qty<=0 or Infinity or fractional WAC
- WHEN POST or stored
- THEN 422 no write; else 4 decimals preserved

## ADDED Requirements

### Requirement: REQ-WAC-003 — Live preview contract
`ComprasForm.vue` MUST compute preview via `computed` mirroring backend: `unit=TOTAL?total/qty:unitInput; newStock=stock+qty; newWAC=(stock*cost+qty*unit)/newStock; valuation=newStock*newWAC` (JS Number display-only; backend authoritative). MUST disable Confirm if qty<=0||cost<=0||!isFinite. Toggle TOTAL|UNIT MUST recalc instantly. Preview MUST match backend to 4 decimals on `10@5+10@9→7.0000`. (Prev: none.)
#### Scenario: SCN-WAC-004 — Preview parity + disabled
- GIVEN 10@5 input qty10 TOTAL90
- WHEN preview computed
- THEN newStock20 newWAC7.0000 valuation140 matches backend; qty0 disables Confirm; toggle recalculates

### Requirement: REQ-WAC-004 — Atomicity and row locking
WAC MUST run in same tx as insert with `SELECT ... FOR UPDATE` on Insumo; commit atomically or full rollback. Concurrent same-insumo MUST serialize; different insumos MAY parallelize; lost update MUST NOT occur.
#### Scenario: SCN-WAC-005 — Concurrent
- GIVEN 2 simultaneous POSTs same insumo and distinct insumos
- WHEN run
- THEN same serializes to correct stock/cost no lost update; distinct no blocking
