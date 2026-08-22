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
