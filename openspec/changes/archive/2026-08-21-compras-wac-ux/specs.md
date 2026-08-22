# Specs - compras-wac-ux (concatenated)
> Source: specs/compras-insumos/spec.md and specs/wac-engine/spec.md


# Delta for compras-insumos

## MODIFIED Requirements

### Requirement: REQ-CI-001 — Register purchase with modo/factura
System MUST expose `POST /api/v1/compras-insumos` with `insumo_id` (RESTRICT), optional `proveedor_id` (SET NULL, 400 if missing), `cantidad_comprada>0`, `modo TOTAL|UNIT` (default UNIT), `precio_unitario` (UNIT) or `costo_total` (TOTAL), optional `factura` ≤100. TOTAL MUST derive `price=costo_total/qty` in Decimal. `qty<=0|cost<=0|Infinity|NaN` MUST 422 before write. `fecha_compra` server-set. 201 + `CompraInsumoRead` + atomic WAC. (Prev: no modo/factura/Infinity guard.)
#### Scenario: SCN-CI-001 — TOTAL purchase
- GIVEN stock 10@5, POST qty10 costo_total90 modoTOTAL facturaF-001
- WHEN succeeds
- THEN 201, unit9, stock20, cost7.0000, factura stored
#### Scenario: SCN-CI-002 — Rejects invalid
- GIVEN qty<=0 or cost<=0 or Infinity
- WHEN POST
- THEN 422 no write no stock change
#### Scenario: SCN-CI-003 — Unknown FK
- GIVEN unknown insumo or proveedor
- WHEN POST
- THEN 404 for insumo, 400 for proveedor

### Requirement: REQ-CI-002 — Response shape
`CompraInsumoCreate` MUST accept insumo_id, proveedor_id?, cantidad_comprada, precio|costo_total, modo, factura. `CompraInsumoRead` MUST include id, insumo_id, proveedor_id?, fecha_compra, cantidad_comprada, precio_unitario_compra, factura, costo_unitario_aplicado as NUMERIC(15,4) strings. (Prev: no modo/factura.)
#### Scenario: SCN-CI-004 — Shape
- GIVEN persisted purchase
- WHEN read
- THEN all fields present, decimals 4-place strings

## ADDED Requirements

### Requirement: REQ-CI-003 — History and CSV
System MUST expose `GET .../compras-insumos?insumo_id=X` ordered fecha_compra desc; any authenticated MAY read. `HistorialDrawer.vue` MUST show date, qty, prev→new stock/cost, total, factura. CSV MUST export same columns.
#### Scenario: SCN-CI-005 — Drawer + CSV + RBAC
- GIVEN 2 purchases for insumo
- WHEN opening drawer then Export CSV
- THEN rows show prev→new stock/cost factura; CSV header fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura; consulta GET 200 POST 403

### Requirement: REQ-CI-004 — Inventory view actions
`InventarioView.vue` MUST add per-row `+ Compra` (opens ComprasForm with insumo_id) and `History` (opens HistorialDrawer); consulta sees History only.
#### Scenario: SCN-CI-006 — Wiring
- GIVEN operador vs consulta on InventarioView
- WHEN row rendered then click +Compra
- THEN operador form pre-filled; consulta +Compra hidden History visible

---

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
