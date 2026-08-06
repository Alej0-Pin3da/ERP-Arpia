# Tasks: WAC — Cost Engine & Purchase Registration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~460–520 (6 files: 4 new + router +2) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (schemas + WAC service + service tests) → PR 2 (routes + wiring + endpoint tests) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending (feature-branch-chain suggested) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | `compra_insumo.py` schemas + `services/wac.py` registrar_compra + `test_wac.py` (engine + concurrency) | PR 1 (base feature/tracker branch) | `pytest backend/tests/test_wac.py -q` | Real test Postgres via conftest `SessionLocal` threads + `Barrier`; unblocks before commit | Delete `services/wac.py`, `schemas/compra_insumo.py`, `test_wac.py`; no router/writes |
| 2 | `compras_insumos.py` POST+GET + register in `router.py` + `test_compras_insumos.py` (authz, pagination, filter) | PR 2 (base = PR 1 branch) | `pytest backend/tests/test_compras_insumos.py -q` | FastAPI `TestClient` in conftest; tokens admin/operador/consulta | Revert router include + delete route + test files |

## Phase 1: Schemas

- [x] 1.1 Create `app/schemas/compra_insumo.py`: `CompraInsumoCreate` (insumo_id required; proveedor_id optional; cantidad_comprada `Field(gt=0)`; precio_unitario_compra `Field(ge=0)`), `CompraInsumoRead` (id, insumo_id, nullable proveedor_id, fecha_compra, cantidad, precio; `ConfigDict(from_attributes=True)`), mirroring `insumo.py` Decimal handling.

## Phase 2: WAC Engine (RED → GREEN)

- [x] 2.1 RED: create `test_wac.py` using `client`/`SessionLocal` fixtures — write failing tests for atomic commit, rollback-on-error, equal-price stable, fluctuation, higher lot, zero stock, precision-no-rounding.
- [x] 2.2 GREEN: create `app/services/wac.py` `registrar_compra(db, insumo_id, proveedor_id, cantidad, precio_unitario) -> CompraInsumo`: `select(Insumo).where(id==...).with_for_update()` → 404 if none; proveedor existence → 400; WAC in `Decimal` (no engine rounding; `stock==0` ⇒ nuevo == precio_unitario); update stock+cost; `add(CompraInsumo(...))`; single `db.commit()`; `db.rollback()` then re-raise on any exception; catch `IntegrityError` → `HTTPException(409)` (resolve D4 open question: map to 409, no 500 leak).
- [x] 2.3 RED: add concurrency test `send_concurrent_purchases_same_insumo` using `threading.Thread` + `Barrier`, per-thread `SessionLocal`; assert final stock==sum, cost==serialized WAC (no lost update). Add `test_wac.py::test_different_insumos_no_block`. Run `pytest backend/tests/test_wac.py -q` — close Phase 2 only when green.

## Phase 3: Routes & Wiring (RED → GREEN)

- [x] 3.1 RED `test/test_compras_insumos.py`: authz (no token 401, consulta POST 403, operador POST 201, any-role GET 200); 404 insumo, 400 proveedor, 422 quantity/price; pagination `limit=2&offset=2`; `insumo_id` filter; read-shape completeness.
- [x] 3.2 GREEN `app/api/routes/compras_insumos.py`: `POST` (deps `require_roles("admin","operador")`), `GET` (deps audited_user) paginated with optional `insumo_id` filter, ordered by id.
- [x] 3.3 Register in `app/api/router.py`: import + `include_router(compras_insumos.router)`.
- [x] 3.4 Close Phase 3 only when `pytest backend/tests/test_compras_insumos.py -q` passes.

## Phase 4: Verification & Cleanup

- [x] 4.1 Run full suite `pytest backend/tests -q`; confirm all green with no modifications to existing models/README/`.env`/migrations.
- [x] 4.2 Remove any leftover test scaffolding and verify router ordering and tags convention vs `insumos.py`.