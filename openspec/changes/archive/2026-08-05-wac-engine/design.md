# Design: WAC — Cost Engine & Purchase Registration

## Technical Approach

Add the first write path over `Insumos.stock_actual`/`costo_promedio_actual`: a dedicated WAC service function that registers a `CompraInsumo` and updates inventory in a single atomic transaction, guarded by `SELECT ... FOR UPDATE` on the insumo row. Two thin FastAPI routes (`POST`/`GET /api/v1/compras-insumos`) delegate the mutation to the service. All money/quantity math uses Python `Decimal`; storage stays `NUMERIC(15,4)`; rounding happens only at presentation. Follows the existing module layout (`app/api/routes/insumos.py`, `app/schemas/*`, `app/core/deps.py`). `backend/app/services/` does not exist yet — this change creates it.

## Architecture Decisions

| # | Decision | Choice | Alternatives | Rationale |
|---|----------|--------|--------------|-----------|
| D1 | Service location | New `app/services/wac.py` with `registrar_compra(db, insumo_id, proveedor_id, cantidad, precio_unitario) -> CompraInsumo` | Put logic inline in route; separate package-per-domain | Keeps the route thin, isolates the WAC algebra for direct unit/concurrency testing, and leaves room for Phase 4 snapshot logic on the same service |
| D2 | Service signature | Accept a `Session`; return the ORM `CompraInsumo` | Return DTO; pass serializable params | Matches existing `insumos.py` which returns ORM rows and uses `db` directly; the route maps to the schema |
| D3 | Validation boundary | `cantidad_comprada > 0`, `precio >= 0` enforced by pydantic `Field(gt=0)`/`Field(ge=0)` → 422 before DB. `insumo_id` existence → 404, `proveedor_id` existence → 400, both from the service | All in route | 422 schema errors precede service; domain 404/400 live where the row lookup happens (service), matching `insumos.py` semantics |
| D4 | Error/rollback contract | Service: single `db.commit()` at end; on any exception call `db.rollback()` then re-raise. `HTTPException` (404/400) raised inside the try; DB errors (`IntegrityError`) propagate as 500 | Convert IntegrityError to 409 | Spec requires all-or-nothing rollback; a FK `RESTRICT` violation on a concurrently-deleted insumo surfaced as 500 is acceptable and simpler than mapping |
| D5 | Row locking | `db.execute(select(Insumo).where(Insumo.id == insumo_id).with_for_update())` | Pessimistic at read; optimistic version column | Matches config `SELECT FOR UPDATE`; Postgres holds the row lock until commit, serializing same-insumo purchases with zero lost updates |
| D6 | Decimal policy | Engine computes in `Decimal`; never quantize in engine; `NUMERIC(15,4)` storage quantizes at write; pydantic schemas carry `Decimal` (serialized as strings); 2dp rounding only at presentation | `float` (rejected), `Rounding` in engine | `config.yaml` forbids FLOAT for money; engine must not round to keep precision for downstream Phase 4 snapshots |
| D7 | Pessimistic vs lost update | Use row lock; no app-level retry loop | Optimistic MVCC with retry | Spec demands serialization of same-insumo writes; FOR UPDATE is simpler and race-free vs retry loops |

## Components

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/wac.py` | Create | `registrar_compra` engine (lock → compute → update → insert → commit/rollback) |
| `backend/app/schemas/compra_insumo.py` | Create | `CompraInsumoCreate`, `CompraInsumoRead` (Decimal fields, optional proveedor) |
| `backend/app/api/routes/compras_insumos.py` | Create | POST 201 + GET paginated, role-guarded |
| `backend/app/api/router.py` | Modify | `include_router(compras_insumos.router)` + import |
| `backend/tests/test_wac.py` | Create | Service unit + concurrency tests |
| `backend/tests/test_compras_insumos.py` | Create | Endpoint/permission/pagination tests |

## Flow Diagram

```
POST /api/v1/compras-insumos (admin|operador)
   │  CompraInsumoCreate (pydantic: cantidad>0, precio>=0 → 422)
   ▼
registrar_compra(db, insumo_id, proveedor_id, cantidad, precio)
  1  insumo = SELECT ... WHERE id ... FOR UPDATE   ──▸ 404 if none (rollback, no writes)
  2  proveedor? = SELECT Proveedor                 ──▸ 400 if non-existent
  3  nuevo = (stock*precio + cantidad*preecio) / (stock+cantidad)   # Decimal, no round
  4  insumo.stock_actual += cantidad
  5  insumo.costo_promedio_actual = nuevo
  6  add(CompraInsumo(..., fecha_compra=func.now()))
  7  db.commit()  ── single commit ── on any raise: db.rollback()
   ▼
201 CompraInsumoRead
```

Concurrency: T1 and T2 target same insumo. T1 acquires FOR UPDATE; T2's SELECT blocks; T1 commits; T2 re-reads updated values, applies its own WAC. Final stock = sum; final cost = serialized WAC. Different insumos: independent row locks, both proceed.

## Test Plan Mapping

| Spec scenario | Test (file) |
|---------------|-------------|
| Atomic commit / all-or-nothing rollback | `test_wac.py::test_purchase_atomic_write_commits_stock_and_cost`; `::test_rollback_on_error_leaves_unmodified` |
| Equal price stable / fluctuation / higher lot | `test_wac.py::test_wac_equal_prices`, `::test_wac_price_fluctuation`, `::test_wac_higher_lot` |
| Zero prior stock → new cost == unit price | `test_wac.py::test_wac_zero_stock` |
| Precision preserved (4dp, no engine rounding) | `test_wac.py::test_wac_precision_no_rounding` |
| Concurrent same-insumo serialize + no lost update | `test_wac.py::test_concurrent_purchases_same_insumo` (threads + `Barrier`, per-thread `SessionLocal`, calls service directly against test Postgres; assert final stock == sum, cost == serialized WAC) |
| Different insumos parallel | `test_wac.py::test_different_insumos_no_block` |
| 201 create + optional proveedor | `test_compras_insumos.py::test_create_purchase_with_proveedor`, `::test_create_without_proveedor` |
| 404 insumo / 400 proveedor / 422 qty-price | `::test_create_nonexistent_insumo_404`, `::test_invalid_proveedor_400`, `::test_invalid_quantity_price_422` |
| Authz: no token 401, consulta 403, operador 201, any-role GET 200 | `::test_post_unauth_401`, `::test_post_consulta_403`, `::test_post_operador_201`, `::test_get_consulta_200` |
| Pagination + filter | `::test_list_paginated_limit_offset`, `::test_list_filter_by_insumo` |

Concurrency test rationale: `TestClient` is synchronous and not reliable for true parallel request threads; the service-level concurrency test drives separate `SessionLocal` instances in `threading.Thread` with a `Barrier`, guaranteeing concurrent DB transactions against real Postgres. Serialization assertion derived from serial order of the injected candidates.

## Threat Matrix

N/A — no routing/shell/subprocess/VCS/executable-file/process-integration boundary.

## Migration / Rollout

No migration. `CompraInsumo`/`Insumo` columns already exist (Phase 1). Additive: new module files + router include. Rollback = remove router include + delete new files.

## Open Questions

- [ ] Confirm 409 vs 500 on `IntegrityError` (concurrent FK RESTRICT delete).
- [ ] `test_concurrent_purchases` thread count (2 is sufficient; keep runtime low).