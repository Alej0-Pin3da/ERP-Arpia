# Design: compras-wac-ux — Registrar Compra WAC with Live Simulation & History

## Technical Approach

Extend SSOT `registrar_compra` for `modo TOTAL|UNIT` + `factura`/`proveedor_id`; preview display-only, backend authoritative. Reuse `GET ?insumo_id` for history. No trigger. Covers REQ-CI-001..004 + REQ-WAC-001..004; monolith `backend/app` + PrimeVue.

## Architecture Decisions

### Decision: Service vs DB trigger

| Option | Tradeoff | Decision |
|---|---|---|
| DB trigger | Hides logic, still needs lock, untestable, breaks `commit=False` batch | Rejected |
| Service `registrar_compra` | Explicit txn, testable, caller controls commit | **Chosen** |

**Choice**: TOTAL derives `price=costo_total/qty` (Decimal) then `(stock*cost+qty*price)/(stock+qty)`.
**Rationale**: Existing `SELECT FOR UPDATE` + atomic commit; trigger duplicates lock and blocks `migrate/purchases.py`.

### Decision: Decimal NUMERIC(15,4) vs float

| Option | Tradeoff | Decision |
|---|---|---|
| float / JS Number persisted | `0.1+0.2` drift, `toFixed(2)` breaks `10@5+10@9=7.0000` | Rejected for writes |
| `Decimal(str(v))` + `Numeric(15,4)` | Exact 4 decimals, quantizes at write | **Chosen** |

**Rationale**: `config.yaml` forbids FLOAT; REQ-WAC-002 forbids Infinity/NaN. JS `Number` only for display `computed`.

### Decision: Row locking

| Option | Tradeoff | Decision |
|---|---|---|
| No lock / optimistic | Lost update on concurrent same-insumo | Rejected |
| `SELECT ... FOR UPDATE` on `Insumo` | Serializes same-insumo, parallelizes distinct | **Chosen** |

**Rationale**: Already in `wac.py:44`; REQ-WAC-004 mandates it. Mitigates D12.

### Decision: Preview authority

| Option | Tradeoff | Decision |
|---|---|---|
| Client sends computed WAC | Drift, trust boundary violation | Rejected |
| `computed` mirrors formula display-only, toggle recalculates, backend authoritative | Parity to 4 decimals, no trust | **Chosen** |

**Rationale**: REQ-WAC-003 `unit=TOTAL?total/qty:unit; newWAC=(stock*cost+qty*unit)/newStock`; disable if `qty<=0||cost<=0||!isFinite`. Mitigates D13/D15.

## Data Flow

```
InventarioView --(+Compra/History)--> ComprasForm / HistorialDrawer
        |  props: insumo+stock/cost      | computed preview (display-only)
        +-- comprasApi.create(payload) -> POST /api/v1/compras-insumos
                                            -> CompraInsumoCreate (modo,factura)
                                            -> routes.create -> registrar_compra
                                                SELECT Insumo FOR UPDATE
                                                nuevo=(stock*cost+qty*price)/(stock+qty) [Decimal]
                                                UPDATE Insumo + INSERT CompraInsumo -> commit/rollback
                                            -> GET ?insumo_id DESC -> HistorialDrawer + CSV
```
Gate before service: `gt0` + `isFinite` -> 422 no write (D15, REQ-CI-001/REQ-WAC-002).

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/schemas/compra_insumo.py` | Modify | Add `modo`, `costo_total?`, `factura?≤100`, `proveedor_id?`; finite validator; extend `Read` with `costo_unitario_aplicado` `NUMERIC(15,4)` |
| `backend/app/services/wac.py` | Modify | TOTAL `price=costo_total/qty` Decimal then WAC; accept `factura`/`proveedor_id`; keep `FOR UPDATE` + atomic commit |
| `backend/app/api/routes/compras_insumos.py` | Modify | Pass new fields; 404 insumo / 400 proveedor; keep RBAC `audited` vs `mutation`; `fecha_compra DESC` |
| `backend/app/models/insumos.py` | Modify | Add `proveedor_id FK SET NULL`, `factura`, `costo_unitario_aplicado Numeric(15,4)`, index `fecha_compra` |
| `backend/alembic/versions/*_compras_wac_ux.py` | Create | Alembic cols + index |
| `frontend/src/utils/inventario.ts` | Modify | Extend `CompraPayloadInput` + `buildCompraPayload` TOTAL; add `buildHistorialCsv` |
| `frontend/src/components/inventario/ComprasForm.vue` | Modify | Toggle TOTAL|UNIT, `computed` `newStock/newWAC/valuation`, Confirm disabled `!isFinite` |
| `frontend/src/components/inventario/HistorialDrawer.vue` | Create | Drawer: date/qty/prev→new stock/cost/total/factura + CSV |
| `frontend/src/views/InventarioView.vue` | Modify | Per-row `+ Compra` (operador+ pre-filled) + `History`; consulta History only |
| `frontend/src/api/endpoints.ts` | Modify | Typed `comprasApi` for new fields |

## Interfaces / Contracts

```python
# schemas/compra_insumo.py + services/wac.py
class CompraInsumoCreate(BaseModel):
    insumo_id: int; proveedor_id: int | None = None
    cantidad_comprada: Decimal = Field(gt=0)
    modo: Literal["TOTAL","UNIT"] = "UNIT"
    precio_unitario_compra: Decimal | None = Field(default=None, ge=0)
    costo_total: Decimal | None = Field(default=None, gt=0)
    factura: str | None = Field(default=None, max_length=100)
class CompraInsumoRead(BaseModel):  # from_attributes=True
    id:int; insumo_id:int; proveedor_id:int|None; fecha_compra:datetime
    cantidad_comprada:Decimal; precio_unitario_compra:Decimal
    costo_unitario_aplicado:Decimal; factura:str|None
def registrar_compra(db, insumo_id, cantidad, precio_unitario=None, costo_total=None,
                     modo="UNIT", factura=None, proveedor_id=None, fecha_compra=None, commit=True) -> CompraInsumo: ...
```

```typescript
// utils/inventario.ts preview (display-only, backend authoritative)
const unit = modo==='TOTAL' ? total/qty : unitInput
const newStock = stock + qty
const newWAC = (stock*cost + qty*unit)/newStock
const CSV_HEADER = "fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura"
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit BE | TOTAL→unit, zero-stock `nuevo==price`, 4 decimals, `Infinity/NaN/qty<=0` 422, `commit=False` | `pytest test_wac.py` SCN-WAC-001..003 |
| Unit FE | `computed` parity `10@5+10@9→7.0000`, toggle recalc, disabled gate, CSV | `vitest` `compras-form.spec.ts` + `historial-drawer.spec.ts` |
| Integration | POST TOTAL/UNIT 201 + factura/proveedor, 422/404/400 no write, GET `?insumo_id` DESC, RBAC `consulta GET 200 POST 403` | `pytest test_compras_insumos.py` SCN-CI-001..005 |
| Concurrent | Same-insumo serializes no lost update, distinct parallelizes | Threaded `pytest` on Docker PG (SCN-WAC-005) |

Mitigates D12 lost update (FOR UPDATE), D13 drift (authoritative), D14 precision (NUMERIC 15,4), D15 Infinity (finite gate).

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

Alembic nullable `proveedor_id` (FK deferred), `factura`, `costo_unitario_aplicado`; backfill `NULL`; `modo` default `UNIT` backward compat. Rollback: revert migration + schema/route + `ComprasForm.vue`, single commit. Budget ≤800 lines via `<250` slices.

## Open Questions

- [ ] Proveedor FK without table — nullable unconstrained or defer?
- [ ] History ordering: override `Paginated` id-ASC to `fecha_compra DESC`?
- [ ] `prev→new` CSV: client-computed from rows or expose `prev_*` in read?
