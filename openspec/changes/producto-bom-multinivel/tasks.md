# Tasks: Product Engineering & Multilevel BOM (Phase 3)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,840–2,260 total (12 files: 11 new + router.py); S1 ~750–900, S2 ~600–740, S3 ~490–620 |
| 400-line budget risk | High (all 3 slices) |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (master CRUD) → PR 2 (BOM) → PR 3 (cost engine); sub-split PR 1a/1b if 400 is strict |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main (cached from wac-engine decision #338) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | `schemas/producto.py` + `routes/tipos_productos.py` + `routes/productos.py` + router include + `test_productos.py` | PR 1 (base main) | `pytest backend/tests/test_productos.py -q` | TestClient + admin/operador/consulta tokens vs real test Postgres | Remove 2 router includes; delete producto.py, tipos_productos.py, test_productos.py |
| 2 | `schemas/bom.py` + `routes/bom.py` (validators) + router include + `test_bom.py` | PR 2 (base = PR 1) | `pytest backend/tests/test_bom.py -q` | TestClient + SessionLocal validator tests | Revert bom include; delete bom.py (schemas+routes), test_bom.py |
| 3 | `schemas/costo.py` + `services/costos.py` + `routes/costos.py` + router include + `test_costos.py` | PR 3 (base = PR 2) | `pytest backend/tests/test_costos.py -q` | SessionLocal engine calls + TestClient `/costo` | Revert costos include; delete costo.py, costos.py (svc+route), test_costos.py |

## Slice 1: Master CRUD — PR 1 (RED → GREEN)

- [x] 1.1 Create `backend/app/schemas/producto.py`: TipoProducto/Producto/VarianteProducto Base/Create/Update/Read, `ConfigDict(from_attributes=True)`, nombre min/max, `requiere_fabricacion=True` default, Decimal `ge=0`/`gt=0`.
- [x] 1.2 RED `test_productos.py`: tipos — create 201, dup nombre 409, get missing 404, pagination limit/offset order by id, PUT 200, DELETE 204.
- [x] 1.3 RED: productos — create 201 w/ defaults, invalid tipo 400, negative costos/precio 422, missing 404, PUT 200, DELETE 204.
- [x] 1.4 RED: variantes — create 201, dup nombre per product 409, missing product 404, delete missing 404, PUT 200.
- [x] 1.5 RED: authz — no token 401, operador mutations 403, consulta GET 200.
- [x] 1.6 GREEN `routes/tipos_productos.py`: CRUD /tipos-producto; GET audited paginated; POST/PUT/DELETE admin; 404; IntegrityError→409 dup nombre.
- [x] 1.7 GREEN `routes/productos.py`: CRUD /productos (tipo FK→400; IntegrityError→409) + nested /variantes CRUD (404s; dup nombre 409).
- [x] 1.8 Wire both in `backend/app/api/router.py`.
- [x] 1.9 Close: `pytest backend/tests/test_productos.py -q` green.

## Slice 2: BOM Recipes — PR 2 (RED → GREEN)

- [x] 2.1 Create `backend/app/schemas/bom.py`: BomInsumo (variante_id optional, cantidad_requerida `gt=0`, porcentaje_desperdicio `ge=0 le=100` default 0) + BomProducto (cantidad `gt=0`) Create/Update/Read.
- [x] 2.2 RED `test_bom.py` service-level: import validators from routes/bom.py — NULL+NULL→409, same-variant→409, NULL+variant→ok.
- [x] 2.3 RED endpoints insumos: create 201 (waste 0), insumo missing 400, waste 150→422, variant of other product 400, parent missing 404, dup NULL 409, dup variant 409, NULL+variant 201, PUT/DELETE.
- [x] 2.4 RED endpoints combos: create 201, dup combo 409, included missing 400, parent missing 404, cantidad 0→422, PUT/DELETE.
- [x] 2.5 RED authz: 401/403 + any-role GET 200.
- [x] 2.6 GREEN `routes/bom.py`: nested insumos + productos CRUD; product 404; insumo FK 400; variante FK + same-product 400; `validar_linea_insumo_unica` explicit SELECT→409 (IntegrityError fallback); dup combo→409.
- [x] 2.7 Wire `bom` in router.py.
- [x] 2.8 Close: `pytest backend/tests/test_bom.py -q` green.

## Slice 3: Cost Engine — PR 3 (RED → GREEN)

- [x] 3.1 Create `backend/app/schemas/costo.py`: CostoLineaRead {tipo, id, nombre, cantidad, costo_unitario, costo_total} + CostoProduccionRead {total, lineas[]}.
- [x] 3.2 RED `test_costos.py` service: single 2×5+10=20.0000; waste 10×20%×5=60.0000; multilevel A(B×2)+10=70.0000; variant override; base fallback; non-fabricated→15.0000; no-BOM→15.0000; cycle A→B→A→409; precision no rounding; diamond A→{B,C}→D + cursor-execute counter (D once).
- [x] 3.3 GREEN `services/costos.py`: `calcular_costo_produccion(db, pid, vid=None)` + `desglosar_costo_produccion`; core `_calcular` with memo keyed (pid, vid) intra-call + path-stack cycle→409; effective qty×costo_promedio_actual; combo cantidad×child (vid propagates, unknown→NULL base); + fijos per level; read-only, no commits.
- [x] 3.4 RED endpoint: GET /productos/{id}/costo — 200 total+lineas (combo carries recursive cost), 404, 409 cycle, consulta 200, no token 401.
- [x] 3.5 GREEN `routes/costos.py`: GET /productos/{id}/costo (audited_user) → `desglosar_costo_produccion`.
- [x] 3.6 Wire `costos` in router.py (shares /productos prefix, no collision).
- [x] 3.7 Close: `pytest backend/tests/test_costos.py -q` green.

## Phase 4: Final Verification

- [ ] 4.1 Full suite `pytest backend/tests -q` green; no model/migration/README/.env changes.
- [ ] 4.2 Verify router ordering/tags match insumos.py convention.
