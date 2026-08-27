# Exploration: v4-fase3-maestros

## Current State

### How the system works today relevant to Maestros (catalogs)

**Backend Postgres (head 0013 after Fase 2):**
- 17 active tables + `AuditLog/RefreshToken`. Maestros domain has **only** 2 partial tables: `maestros_canales_venta` (`id, codigo VARCHAR(50) UNIQUE, nombre VARCHAR(100), created_at`) and `maestros_metodos_pago` (same shape) created in `0010_ventas_canal_pago.py` with `ON CONFLICT DO NOTHING` seeds (5 + 4 rows). No SQLAlchemy model — raw SQL only via Alembic + `app/seeder.py`. No Pydantic schemas, no REST routes, no `app/models/maestros.py`.
- `0008_remove_proveedores.py` deleted historical `Proveedores` + FK from `Compras_Insumos`. Any new `ProveedorMaestro` must be `maestros_proveedores` (lightweight catalog, no FK to Compras) per `ERP-V4.md:31` — do not recreate the dropped table.
- `Ventas` already has `canal_venta VARCHAR(50) CK 5 values (web, whatsapp, instagram, feria, showroom_pereira)` + `metodo_pago VARCHAR(50) nullable` aligned to the 2 maestros tables. Validation is CK + Pydantic Literals in `schemas/venta.py` — not FK.
- `Insumos` (`Insumos`, `Categorias_Insumos`) exists — **collision risk**: `CategoriaInsumo` (FK for raw material type) is distinct from `CategoriaColeccionMaestro` (product family `CON_TALLAS_ESTANDAR | SIN_TALLA_MERCH | TALLA_UNICA`). Must keep namespaces separate.
- `Socios_Configuracion` / `liquidaciones` / `anticipos` closed in Fase 2 (0011-0013) with 10 nullable cols, sum-to-100 service validation, `LiquidacionEstado`/`AnticipoEstado`, `FOR UPDATE` locks. `ParametrosCosteoMaestro` mirrors the 40/30/30 `distribucion_*` pattern but is **singleton/global**, not per-socia.

**Frontend mock (`src/stores/atelier.ts` 3411 lines, `@deprecated` header for `VITE_USE_MOCK=true`):**
- 8 Maestro interfaces + seed arrays + 25 CRUD actions (`crearProveedor/actualizarProveedor/eliminarProveedor` etc.; `actualizarParametrosCosteo` for singleton):
  - `ProveedorMaestro` (9 cols: nombre, categoria free VARCHAR `'Telas Principales' | 'Herrajes ...'`, ciudad, contacto, telefono, email, tiempo_entrega_dias number, condicion_pago free, calificacion number, activo bool, notas?)
  - `CanalVentaMaestro` (5 cols: nombre, tipo `'FISICO'|'DIGITAL'|'EVENTO'`, comision_pct, costo_fijo_mensual, activo, descripcion)
  - `MetodoPagoMaestro` (5 cols: nombre, tipo `'TRANSFERENCIA'|'BILLETERA_DIGITAL'|'EFECTIVO'|'PASARELA_DATAFONO'`, comision_pct, tiempo_acreditacion, activo, datos_cuenta?)
  - `CategoriaColeccionMaestro` (5 cols: nombre, tipo_talla `'CON_TALLAS_ESTANDAR'|'SIN_TALLA_MERCH'|'TALLA_UNICA'`, descripcion, margen_meta_pct, total_modelos number, activo)
  - `UbicacionTallerMaestro` (5 cols: codigo `UB-...`, nombre, tipo `'ROLLOS_TELAS'|'GAVETAS_HERRAJES'|'PERCHERO_SHOWROOM'|'ACCESORIOS_BODEGA'`, capacidad free, observaciones)
  - `TallaEstandarMaestro` (7 cols: talla free `'XXS'..'XL'`, busto/cintura/cadera/reduccion_corset free strings `'78 - 82 cm'`, descripcion, orden number, activo) — seed 6 rows XXS(1)..XL(6) matrix
  - `ProductoSinTallaMaestro` (6 cols: nombre, categoria free, dimensiones, materiales, descripcion, precio_sugerido NUMERIC, activo) — 4 seed rows
  - `ParametrosCosteoMaestro` (8 cols: costo_minuto_costura, costo_hora_patronaje, margen_meta_global_pct, desperdicio_textil_default_pct, iva_regimen_pct, distribucion_reinversion/margara/valqui *_pct) — single object with sum-to-100 guard.
- `src/views/MaestrosView.vue` (1450 lines, 7 tab types `'proveedores'|'canales'|'pagos'|'categorias'|'ubicaciones'|'costeo'|'tallas'` — note `tallas` tab merges 2 entities: `TallaEstandar` table + `ProductoSinTalla` cards). Each tab: local `ref<Partial<...>>` form, `abrirNuevo/Editar`, `guardar*` calls `store.crear*/actualizar*`, delete calls `store.eliminar*`. `costeo` tab has `sumaDistribucion` computed + `sumaDistribucion !== 100` alert guard identical to Socios sum-to-100. Filtering only `filtroCategoriaProv`.
- `src/services/api/maestros.ts` (53 lines) — **stub**: exports `CANALES_VENTA`/`METODOS_PAGO` static 5+4 `codigo/nombre` arrays + `listCanales()/listMetodosPago()` via `tryFetch('/maestros/...', fallback)`. No other catalogs, no CRUD, no Paginated.
- Auth/CRUD pattern established: `useMode.ts` (`isMock` computed from `GET /api/__mode` then `VITE_USE_MOCK`), `src/services/api/{clientes,ventas,socios,liquidaciones,anticipos}.ts` via `client.ts`, `src/composables/useClientes/useVentas/useSocios/useFinanzas.ts` adapter `isMock ? atelier : client` with `Paginated<T>` (`items, total`) + `limit/offset/canal_venta/estado/sort_by/order` filters, `aplicar_orden`/`paginar` on backend. Maestros will follow same adapter — `*.vue` intact per charter.

### Affected Areas
- `backend/app/models/__init__.py` — export new `Maestros*` models (8 tables or 7 if canales/pagos extended)
- `backend/app/models/maestros.py` — **new** (or extend `insumos.py`/`finanzas.py` — recommend dedicated file)
- `backend/app/schemas/maestros.py` — **new** (Create/Update/Read per entity; Literal enums for tipo fields; money NUMERIC(15,4))
- `backend/app/schemas/common.py` — `Paginated` already exists, reuse
- `backend/app/api/routes/maestros.py` — **new** (CRUD + `GET list` with `Paginated`; singleton `GET/PATCH /maestros/parametros-costeo`)
- `backend/app/api/main.py` (or `app/main.py`) — register `maestros` router under `/api/v1`
- `backend/app/services/maestros.py` — **new** optional (sum-to-100 for Parametros singleton, orden uniqueness for Tallas)
- `backend/alembic/versions/0014_*` (+ `0015_*` if sliced) — create/extend maestros tables + guards + seeds + downgrade
- `backend/app/seeder.py` — extend seeds to mirror Alembic (idempotent `ON CONFLICT DO NOTHING`)
- `src/services/api/maestros.ts` — **rewrite** from stub to full CRUD per sub-resource (`proveedores`, `canales-venta`, `metodos-pago`, `categorias-coleccion`, `ubicaciones-taller`, `tallas-estandar`, `productos-sin-talla`, `parametros-costeo` singleton)
- `src/composables/useMaestros.ts` — **new** (`useMode` toggle, same as `useSocios`/`useFinanzas`)
- `src/views/MaestrosView.vue` — **no template rewrite**; wire `guardar*/eliminar*` through `useMaestros` async (keep `isMock` fallback)
- `src/stores/atelier.ts` — only header `@deprecated` already covers maestros; no code change
- `src/components/atelier/*` — no maestros modals exist; inline modals in view stay intact
- Tests: `backend/tests/test_maestros*.py` + `src/composables/useMaestros.test.ts` (Vitest jsdom)
- Docs: `openspec/specs/maestros-*/spec.md` (8 catalogs or grouped), `ERP-V4.md` §4.4/§5 roadmap, `CambiosV3.md`

### Approaches

#### 1. Monolithic single Alembic (0014 with 8 tables)
- Pros: One migration to review; all maestros land atomically; single seed pass mirrors `atelier.ts` arrays.
- Cons: ~600-800 DDL+seed lines exceeds 400-line review budget; large rollback surface (drop 8 tables + 2 alters if extending canales/pagos); one failure blocks all catalogs; `git diff` noise hard to review for each catalog's CHECKs/indexes.
- Effort: Medium (1 migration) but review risk High.

#### 2. Sliced 2-migration sequence (recommended, fits 400-line budget)
- Pros: Each PR <400 lines; independently reversible; allows stacking: PR1 = 4 core catalogs (`maestros_proveedores`, `maestros_categoria_coleccion`, `maestros_ubicacion_taller`, `maestros_parametros_costeo` singleton) + PR2 = 3 remaining (`maestros_talla_estandar`, `maestros_producto_sin_talla`, extend `maestros_canales_venta`/`maestros_metodos_pago` with new columns `tipo/comision_pct/...` to upgrade 0010 stubs). Downgrade is `downgrade -1` per slice. Parallelizable after design freeze.
- Cons: Two reviews + two deploys; need to coordinate `alembic head` across slices.
- Effort: Medium (2 migrations, 8 tables total).

#### 3. Enum vs free VARCHAR for `categoria`/`tipo` fields
- Pros (Enum CHECK): DB rejects invalid `FISICO|DIGITAL|EVENTO` etc., aligns to `atelier.ts` Literal; self-documenting.
- Cons: Adding a new canal tipo requires new Alembic `DROP CONSTRAINT / CREATE CHECK`. Free VARCHAR is more flexible (atelier adds categories without migration).
- Effort: Low. **Recommendation: keep CHECK for `tipo` enums (they are domain-closed: Canal 3 values, Metodo 4, Ubicacion 4, Categoria tipo_talla 3) but leave `Proveedor.categoria` and `ProductoSinTalla.categoria` as free VARCHAR(100) — they are open-ended (`'Telas Principales'` etc. are seeds, not closed sets). Mirrors Fase 1/2 pattern where `Ventas.canal_venta` uses CHECK 5 values but `Cliente.tipo` is VARCHAR.**

#### 4. TallaEstandar matrix vs single table
- Pros (matrix 6-row seed): Frontend table maps 1:1; `orden UNIQUE` gives stable XXS→XL sort; no join needed.
- Cons (matrix table per size): Over-engineered for 6 rows today.
- Effort: Low. **Recommendation: single table `maestros_tallas_estandar` with `talla VARCHAR(20) UNIQUE`, `orden INT UNIQUE`, free measure strings. Do not create per-measure columns as NUMERIC ranges — atelier stores `'78 – 82 cm'` as display string, not computable bounds.**

### Recommendation

**Adopt Approach 2 (sliced 2 migrations) + Approach 3 hybrid (CHECK for closed `tipo` enums, free VARCHAR for open categorias) + single-table Talla.**

Rationale: Fase 2 proved 3 isolated migrations (0011/12/13) keep each slice reversible and under 400 lines; maestros are 8 independent catalogs with no cross-FK (except `Insumo.ubicacion` MAY reference `maestros_ubicaciones_taller` as free text — not FK to avoid circular dep). 0010 already created `maestros_canales_venta`/`maestros_metodos_pago` with stub shape (`codigo,nombre`); Fase 3 must **extend** them (add `tipo, comision_pct NUMERIC(15,4), costo_fijo_mensual, activo, descripcion/datos_cuenta`) via `ALTER TABLE` + seed enrichment, not recreate — preserves existing `Ventas` data + `ON CONFLICT` idempotency. Talla as flat table avoids premature normalization; `ParametrosCosteo` as singleton row `id=1` with `CHECK distribucion sum handled in service` (same rationale as Socios sum-to-100 cannot be DB CHECK).

Delivery: `0014a_maestros_core` (proveedores, categorias_coleccion, ubicaciones_taller, parametros_costeo singleton + extend canales/pagos) + `0014b_maestros_tallas` (tallas_estandar + productos_sin_talla) OR `0014` + `0015` numbering. Keep `useMaestros` adapter mirroring `useSocios`/`useFinanzas` so `MaestrosView.vue` stays intact.

### Risks

- **0010 canales/pagos extension collision**: Tables exist with `codigo UNIQUE`. Adding `tipo/comision_pct/costo_fijo/activo/descripcion` must be nullable or with server_default; downgrade must not drop table if `Ventas` still references its `codigo` values (even though no FK, CK may break). Mitigation: use `_has_column` guards, add cols nullable, backfill from static constants.
- **Review budget breach if monolithic**: 8 CreateTable + 8 seed blocks + indexes + downgrades >400 lines → reviewer fatigue, missed CHECK typo. Mitigation: sliced 2 PRs as recommended.
- **Proveedor refund vs 0008 deletion confusion**: Recreating `Proveedores` name collides with archived intent; must use `maestros_proveedores` explicitly and document in `ERP-V4.md:31`. Risk of reviewer requesting FK to `Compras_Insumos.proveedor_id` (re-introduced nullably in `insumos.py` as `proveedor_id nullable no FK`) — reject; keep decoupled.
- **Talla `orden` uniqueness vs free talla names**: User can insert `XXL` with `orden=7` or duplicate `S` with different `orden`; need `UNIQUE(talla)` + `UNIQUE(orden)` + service check `orden` auto-increment (`MAX(orden)+1`) to avoid gaps. Frontend currently does `store.tallasEstandarMaestros.length+1` — race if concurrent; backend must enforce.
- **ParametrosCosteo singleton race**: Two concurrent `PATCH /parametros-costeo` could interleave sum-to-100 check; need `SELECT FOR UPDATE` on the singleton row or serialize via single row lock (same pattern as `anticipos` `FOR UPDATE`). Also `distribucion_reinversion+ margara + valqui !=100` must be 422, not silent clamp. Existing `MaestrosView.vue` already has frontend guard but service must re-validate.
- **Money precision drift**: `comision_pct`, `costo_fijo_mensual`, `margen_meta_pct` vs `precio_sugerido` should be `NUMERIC(15,4)` per project convention (not `NUMERIC(12,2)` used in `liquidaciones`). Mixing precisions causes rounding mismatches in reports.
- **Insumo Ubicacion collision**: `Insumo.ubicacion` is free VARCHAR today (e.g. `'Estante Telas Atenea A1'`). If `maestros_ubicaciones_taller` becomes authoritative, consider optional FK or keep free text + UI autocomplete from maestros — do not force FK migration that would require backfilling 12 insumos.
- **MaestrosView.vue stale index**: CodeGraph reports file pending sync; direct Read required for edits — stale reads may miss recent `useFinanzas` wiring commit `b9f453a`.
- **Phase overlap**: Fase 2 pending `verify+archive` on `feat/v4-fase2-pr3-integration`; Fase 3 branch must stack from that branch, not `main`, or rebase after Fase 2 merges to avoid missing 0011-0013 history.

### Ready for Proposal

Yes — sufficient evidence to draft proposal. Orchestrator should prompt user with `proposal` next, noting:

- Confirm slice boundary (2 migrations vs 1) — default to 2 for budget.
- Confirm `maestros_proveedores` stays decoupled from `Compras_Insumos`.
- Confirm Talla stays flat table (no numeric range columns) and `orden` uniqueness rule.
- Confirm ParametrosCosteo singleton `id=1` with service sum-to-100 guard.
- Confirm extending (not recreating) `maestros_canales_venta`/`maestros_metodos_pago` from 0010 stub shape.

---

## Extended Analysis (for Proposal Inputs)

### Similar Patterns from Fase 1/2 (to reuse)

| Pattern | Fase 1 (clientes/ventas) | Fase 2 (socios/liquidaciones/anticipos) | Reuse for Maestros |
|---------|--------------------------|-----------------------------------------|--------------------|
| Model | `Clientes` +10 nullable cols, extend not recreate | `Socios_Configuracion` +10 nullable cols; `liquidaciones` header+`liquidacion_distribucion` child FK CASCADE | `maestros_*` all new tables; extend 2 stub tables with `ALTER TABLE + _has_column` guards |
| Schema | `ClienteCreate/Read` with `Literal` for `canal_venta`, `metodo_pago`; `medidas JSONB` flexible | `SocioConfiguracionCreate` Literals for `tipo_cuenta`, EmailStr validator; `LiquidacionCreate` 6× totals | Per-catalog `Create/Update/Read` Literals (`FISICO/DIGITAL/EVENTO`, `TRANSFERENCIA...`, `ROLLOS_TELAS...`, `CON_TALLAS...`); keep proveedor categoria free |
| Route | `ventas.py` `Paginated[VentaRead]` + `aplicar_orden` + `paginar` + `user_limiter` + `require_roles` | `finanzas.py` `Paginated` + transition `PATCH /{id}/state` + `LiquidacionRead.warnings[]` | `maestros.py` `GET /maestros/{catalog}?limit&offset&q&tipo&activo&sort_by&order` + `POST/PATCH/DELETE /{id}` + singleton `GET/PATCH /parametros-costeo`; same limiter/roles |
| Service | `services/audit.py` + inventory WAC (not relevant) | `services/finanzas.py` sum-to-100, drift>5% warning, `FOR UPDATE` double-discount lock | `services/maestros.py` only for singleton sum-to-100 + talla `orden` auto-increment; no WAC |
| Frontend api | `services/api/clientes.ts` `client.get<Paginated<ClienteRead>>('/clientes', {params})` via `client.ts` | `services/api/{socios,liquidaciones,anticipos}.ts` same; `tryFetch` fallback not used in Fase 2 (real required) | `services/api/maestros.ts` sub-resources `proveedores`, `canales-venta`, `metodos-pago`, `categorias-coleccion`, `ubicaciones-taller`, `tallas-estandar`, `productos-sin-talla`, `parametros-costeo` |
| Composable | `useClientes.ts` `isMock ? atelier.clientes : await api.list()` + `useMode` | `useSocios.ts` + `useFinanzas.ts` same adapter, Vitest `useMode.test.ts` + `use* .test.ts` jsdom | `useMaestros.ts` same; 8 `list/get/create/update/remove` groups + `parametros` singleton; Vitest mock-vs-real toggle |
| UI | `ClientesView.vue` + `NuevoClienteModal.vue` intact, wired via composable | `FinanzasView.vue` + `GestionSociasModal.vue`/`NuevaLiquidacionModal.vue`/`NuevoAnticipoModal.vue` wired | `MaestrosView.vue` 7 tabs + inline modals intact — only `guardar*/eliminar*` become `await useMaestros().create*/update*/remove*` with `isMock` fallback |
| Migration guard | `0009_extend_clientes_crm.py` `_has_column` guards, reversible downgrade | `0011/12/13` idempotent guards `_has_table/_has_column/_has_constraint`, `ON CONFLICT DO NOTHING` seeds | Same `_has_*` guards + `ON CONFLICT (codigo/nombre/talla) DO NOTHING` seeds from `atelier.ts` arrays |
| Money | `NUMERIC(15,4)` for `descuento_porcentaje/total_venta` | `NUMERIC(12,2)` for liquidaciones/anticipos (exception due to domain spec; maestros should follow 15,4) | `NUMERIC(15,4)` for `comision_pct/costo_fijo/margen_meta/ precio_sugerido/costo_minuto` per project convention |
| Verification | Smoke: create client with `medidas JSONB`, sale with `canal_venta+metodo_pago`, `psql` persist, `F5` no reset | Smoke: socia sum 100, liquidacion `LIQ-YYYY-NN` + warnings, anticipo double-discount 409, `F5` persists, `GET /api/__mode` | Smoke: each tab `list/create/edit/delete` persists + `F5`, singleton `PATCH` sum-to-100 422, `GET /api/__mode` still `real` |

### Key Gaps (8 tablas faltan, no API, no Paginated filters)

1. **No models/schemas/routes/API at all** for any of 8 catalogs beyond the 2 stub tables (which themselves have no ORM model). `maestros_proveedores`, `maestros_categorias_coleccion`, `maestros_ubicaciones_taller`, `maestros_tallas_estandar`, `maestros_productos_sin_talla`, `maestros_parametros_costeo` do not exist; `maestros_canales_venta`/`maestros_metodos_pago` are incomplete (missing domain columns).
2. **No Paginated filters**: MaestrosView today does client-side `filter((p)=>p.categoria===...)` for proveedores only; no backend `q/tipo/activo/categoria` filters, no `limit/offset`, no `sort_by/order` (`aplicar_orden` whitelist pattern not applied).
3. **No seeds/automation**: Seeds hard-coded only in `atelier.ts` arrays (6 proveedores, 5 canales, 5 metodos, 5 categorias, 5 ubicaciones, 6 tallas, 4 sin-talla, 1 parametros). No Alembic `bulk_insert`/`ON CONFLICT` or `seeder.py` entries for 6 of 8 catalogs.
4. **No audit**: `audit.py` covers `clientes/ventas/finanzas`; maestros mutations not logged.
5. **No validation on singleton**: `MaestrosView.vue` frontend `sumaDistribucion !==100` alert exists but no backend `422` for `ParametrosCosteo`; race without lock.
6. **No coverage**: `backend/tests/` has `test_clientes*`, `test_ventas*`, `test_finanzas*`; zero maestros tests; `src/composables/useMaestros.test.ts` missing.

### Implications (What proposal MUST include)

- **Schema/Migration/Backend**: Create 6 tables + extend 2; add `activo` bool default true where applicable; add `orden INT UNIQUE` for tallas; add `codigo VARCHAR UNIQUE` for ubicaciones; add `UNIQUE(nombre)` for proveedores/categorias where domain says unique (check `atelier.ts` seeds have unique nombres). Use `CheckConstraint` for closed enums; use `Numeric(15,4)` for money; add `Index` on `activo`, `tipo`, `categoria`, `orden`. Extend `seeder.py` + define `Maestros*` models with `__table_args__`.
- **API surface**: `GET /maestros/proveedores` (q, categoria, ciudad, activo, sort), `POST/PATCH/DELETE`; `GET /canales-venta` (tipo, activo), `GET /metodos-pago` (tipo, activo), `GET /categorias-coleccion` (tipo_talla, activo), `GET /ubicaciones-taller` (tipo), `GET /tallas-estandar` (activo, sort orden), `GET /productos-sin-talla` (categoria, activo), `GET /parametros-costeo` singleton + `PATCH`. All `Paginated` except singleton.
- **Frontend**: Rewrite `src/services/api/maestros.ts` from 53-line stub to ~250-line full CRUD (8 sub-clients) + `src/composables/useMaestros.ts` + wire `MaestrosView.vue` 8 `guardar*`/`eliminar*` to async composable (keep `isMock` branch for rollback). Keep `VITE_USE_MOCK=true` fallback to current `atelier.ts`.
- **Testing**: 2 layers: `pytest` for enum validation, `UNIQUE` dup 409, singleton sum-to-100 422, `orden` duplicate 409; `Vitest` for `useMaestros` mock/real toggle + `MaestrosView` persist smoke.

### Assumptions (to confirm in proposal)

- `maestros_proveedores` remains lightweight catalog decoupled from `Compras_Insumos` (no FK reintroduced) — per `ERP-V4.md:31`.
- `maestros_canales_venta`/`maestros_metodos_pago` extended via `ALTER TABLE`, not dropped/recreated, to preserve `Ventas` CK values.
- Talla measures stay free display strings, not numeric bounds — no `busto_min/busto_max` columns.
- `ParametrosCosteo` singleton row `id=1` created on migration; `PATCH` is the only mutation (no POST/DELETE).
- `CategoriaColeccionMaestro.total_modelos` stays as stored count (not FK count to `BOM`) — matches mock; no trigger to sync with real `BOM_Productos`.
- `UbicacionTallerMaestro.capacidad` stays free string (`'25 Rollos'`) not numeric capacity — matches mock.

### Open Questions (for proposal phase)

1. Should `Insumo.ubicacion` become FK to `maestros_ubicaciones_taller.codigo` (or keep free text with autocomplete)? Decision affects whether `maestros_ubicaciones_taller` needs `ON DELETE RESTRICT`.
2. Should `maestros_canales_venta.codigo` become FK target for `Ventas.canal_venta` (replace CK 5 values with FK), or keep CK + sync seeds? FK adds referential integrity but requires data migration for legacy `'feria'` vs `'Feria Showroom'` mapping already done in 0010.
3. Does `CategoriaColeccion` need `producto_ids` linkage, or is `total_modelos` manual count sufficient for Fase 3?
4. Should `TallaEstandar` enforce `orden` contiguous 1..N (no gaps after delete) via service re-order, or allow gaps?
5. Is `ParametrosCosteo.iva_regimen_pct` fixed 0 today but future non-zero IVA needs history/versioning (audit trail) or just overwrite singleton?
6. Spec naming: `maestros_*` prefix vs `catalogos_*` — `ERP-V4.md` uses `maestros_*`, Fase 1/2 used `liquidaciones`/`anticipos` without prefix; keep `maestros_` for 8 catalogs for clarity.

---

## Impact / Risk Summary for 400-line Budget

- Estimated author lines (excluding tests/seeds): models ~120, schemas ~140, routes ~220, migrations 2× ~180 each → **~660 total**. Split as 2 PRs: PR-A ~350 (core 4 tables + extend 2 + backend wiring) fits budget; PR-B ~310 (tallas + sin-talla + frontend composable) fits budget. Monolithic single PR would be ~660 → **High budget risk** → must slice.
- `*.vue` intact principle protects `MaestrosView.vue` 1450 lines from churn; only script setup `guardar*` wiring changes (~40 lines) → low UI regression risk, high confidence via `useMode` toggle.
- Rollback: `VITE_USE_MOCK=true` instant fallback to `atelier.ts`; `downgrade -1` per slice restores prior head. No data loss because maestros are catalogs with no foreign dependents yet (except potential `Insumo.ubicacion` which we keep free text).

## Edge Cases

- Concurrent `crearTallaEstandar` with same `talla` or `orden` → expect 409 `UniqueViolation` mapped to 409, not 500.
- `Proveedor.email` invalid format → EmailStr validator 422 (add to schema, not present in mock but should be stricto).
- `tiempo_entrega_dias` negative or 0 → `ge=0` vs `gt=0` — mock allows 1 day; spec should allow 0 for immediate.
- `calificacion` 0-5 range — mock uses `5`/`4.8`; need `ge=0 le=5` CheckConstraint.
- `comision_pct` negative → `ge=0 le=100`.
- `margen_meta_pct` >100 → backend clamp 422; mock allows any but UI shows `%`.
- Singleton `parametros-costeo` `GET` before seed → return 404 or auto-create? Prefer auto-create `id=1` on first GET (like seeder) to avoid empty state.
- Deleting a `CanalVenta`/`MetodoPago` still referenced by `Ventas.canal_venta` values → if no FK, orphan string remains; if FK, `ON DELETE RESTRICT` blocks delete → need 409 with message. Recommend keep CK (no FK) for Fase 3, add FK later if needed.

---

*Exploration produced for hybrid store — also persisted as Engram topic `sdd/v4-fase3-maestros/explore`.*
