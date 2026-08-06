# Design: Product Engineering & Multilevel BOM (Phase 3)

## Technical Approach

Three additive slices over the Phase-1 models (no migration, no model edits): (1) master CRUD for Tipos/Productos/Variantes, (2) nested BOM recipe CRUD with FK/duplicate validation, (3) a read-only recursive memoized cost engine + `GET /productos/{id}/costo`. Routers follow `insumos.py` (audited_user GETs, require_admin mutations); the engine follows `wac.py` conventions (Session first, Decimal, HTTPException from service, no rounding in engine). Slices map 1:1 to chained PRs so each stays under the review budget.

## Architecture Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Slice order | productos → bom → costos | Each PR green and <400 lines; costos depends on both |
| 2 | Engine location | `services/costos.py`, pure reads | Phase-4 explosion/margins reuse without duplicated logic |
| 3 | Signature | `calcular_costo_produccion(db, producto_id, variante_id=None) -> Decimal`; no locks/commits | Read-only so Phase 4 wraps it in its own FOR UPDATE txn (spec) |
| 4 | Recursion | one core `_calcular(db, pid, vid, path, memo, lineas_out=None)`; line collector root-only | One code path; breakdown built by the same traversal, never recomputed |
| 5 | Memoization | intra-call dict keyed `(producto_id, variante_id)`; never across calls | `costo_promedio_actual` changes between calls → stale costs |
| 6 | Cycle detection | path stack on `producto_id` → HTTPException 409; cost-time only | Spec mandates 409 on GET /costo; write-time reachability DFS would block incremental recipe editing |
| 7 | Variante propagation | caller `variante_id` propagates to combo children; unknown variant id in child falls back to NULL base | Honors memo key contract; Phase-4 variant explosion; fallback keeps base semantics |
| 8 | Duplicate NULL-variant | module-level `validar_linea_insumo_unica` in `routes/bom.py`: explicit SELECT → 409; IntegrityError → 409 fallback | Postgres `NULL != NULL` defeats the DB unique constraint |
| 9 | Breakdown | root returns `{total, lineas[]}`; combo lines carry full recursive cost as `costo_unitario` | 1-level debug shape per spec; deeper folding bounds payload |
| 10 | Non-fabricated / no-BOM | total = `costos_operativos_fijos`, single `operativos_fijos` line | Only cost source exists (purchases out of scope) |
| 11 | Errors | 401/403 deps; 404 not found; 400 bad FK; 422 pydantic; 409 duplicate/cycle | Matches wac.py + spec; no 500 leaks |
| 12 | Duplicate nombre (tipos/productos) | IntegrityError at commit → rollback → 409 | Unique constraint catches it; same mapping as wac.py |

## Data Flow

```
GET /api/v1/productos/{id}/costo  (audited_user)
  └─ costos.py get_costo → services/costos.py desglosar_costo_produccion(db, id, variante_id=None)
       └─ _calcular root (lineas_out=[])
            ├─ BOM_Insumos: variant row else NULL base; qty × (1+pct/100) × Insumo.costo_promedio_actual
            ├─ BOM_Productos: cantidad × _calcular(child, same vid)   [memo hit → no re-traverse]
            └─ + Producto.costos_operativos_fijos
       → (total, lineas[]) → CostoProduccionRead
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/schemas/producto.py` | Create | Tipo/Producto/Variante Base/Create/Update/Read; Decimal `ge=0`/`gt=0` |
| `backend/app/schemas/bom.py` | Create | BomInsumo/BomProducto Create/Update/Read |
| `backend/app/schemas/costo.py` | Create | CostoProduccionRead `{total, lineas[]}` + CostoLineaRead |
| `backend/app/api/routes/tipos_productos.py` | Create | CRUD `/tipos-producto` |
| `backend/app/api/routes/productos.py` | Create | CRUD `/productos` + nested `/variantes` |
| `backend/app/api/routes/bom.py` | Create | nested `/bom/insumos` + `/bom/productos`; duplicate validators |
| `backend/app/api/routes/costos.py` | Create | `GET /productos/{id}/costo` |
| `backend/app/api/router.py` | Modify | include 4 new routers |
| `backend/app/services/costos.py` | Create | engine + `desglosar_costo_produccion` |
| `backend/tests/test_productos.py` | Create | endpoint CRUD/authz/pagination |
| `backend/tests/test_bom.py` | Create | endpoint + service-level validators |
| `backend/tests/test_costos.py` | Create | service engine + endpoint |

## Interfaces / Contracts

```python
def calcular_costo_produccion(db: Session, producto_id: int, variante_id: int | None = None) -> Decimal
def desglosar_costo_produccion(db: Session, producto_id: int, variante_id: int | None = None) -> tuple[Decimal, list[CostoLineaRead]]
# effective_qty = qty × (1 + pct/100);  combo = cantidad × cost(child, vid)
# requiere_fabricacion=False or no rows → costos_operativos_fijos;  cycle → HTTPException 409
# CostoLineaRead: {tipo: "insumo"|"producto"|"operativos_fijos", id, nombre, cantidad, costo_unitario, costo_total}

def validar_linea_insumo_unica(db, producto_id, insumo_id, variante_id, exclude_id=None) -> None
# explicit SELECT on (producto_id, insumo_id) with variante_id IS [NOT] NULL → HTTPException 409
```

## Endpoints

| Method/Path | Authz | Errors |
|---|---|---|
| POST/GET/PUT/DELETE `/tipos-producto[/{id}]` | GET audited, rest admin | 404/400/409/422 |
| POST/GET/PUT/DELETE `/productos[/{id}]` | same | 404/400/409/422 |
| POST/GET/PUT/DELETE `/productos/{id}/variantes[/{vid}]` | same | 404/409/422 |
| POST/GET/PUT/DELETE `/productos/{id}/bom/insumos[/{bid}]` | same | 404/400/409/422 |
| POST/GET/PUT/DELETE `/productos/{id}/bom/productos[/{bid}]` | same | 404/400/409/422 |
| GET `/productos/{id}/costo` | audited | 404/409 |

Pagination: `/productos` and `/tipos-producto` (limit default 50, offset, `order_by(id)`); nested lists unpaginated.

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Service (real Postgres, SessionLocal) | engine: single-level 2×5+10=20; waste 10×20%×5=60; multilevel A(B×2)=70; variant override/fallback; non-fabricated/no-BOM → fixed; cycle A→B→A → 409; precision | `test_costos.py` direct calls, `pytest.raises(HTTPException)`; diamond A→{B,C}→D + cursor-execute event counter asserting D's rows fetched once (memo) |
| Service | duplicate validators | import from `routes/bom.py`: NULL+NULL → 409, same-variant → 409, NULL+specified → ok |
| Endpoint (tokens) | authz 401/403; CRUD 201/200/204; 404/400/422/409; pagination; GET /costo 200/404/409 | TestClient + admin/operador/consulta tokens; `_make_`/cleanup helpers with unique names (existing pattern) |

Cleanup note: delete Producto/BOM rows before Insumo (FK RESTRICT).

## Threat Matrix

N/A — FastAPI HTTP routing only; no shell, subprocess, VCS/PR automation, executable-classification, or process-integration boundary. All 5 rows not applicable.

## Migration / Rollout

No migration (tables exist from migration 0001). Additive; rollback = remove 4 router includes + delete new files. PR chain: productos → bom → costos.

## Open Questions

- [ ] Variante propagation to combo children (propagate vs always base) — confirm at review
- [ ] CostoLineaRead field names — UI-driven tweak acceptable
- [ ] Pagination defaults (50) and unpaginated nested lists — confirm
