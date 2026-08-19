# Tasks: Frontend Migration Element Plus → PrimeVue 4.5.5 (MIT)

> **Verification command (all PRs): `npm test` (vitest run) in `frontend/`** — the full suite is **55 spec files** (38 `tests/component/` + 16 `tests/unit/` + 1 `tests/App.spec.ts`). This overrides `openspec/config.yaml` `verify.test_command` (backend pytest) — this change is frontend-only (MIG-1). Build baseline/compare: `npm run build` in `frontend/`.
> **Q8 scope guard**: no new DataTable features (CSV export, virtual scroll, sticky, pin) — only current-spec behavior.

## Review Workload Forecast

| Slice | PRs | Est. changed lines (add+del) | 800-line budget risk |
|---|---|---|---|
| 0 Foundations | 1 (PR 0) | ~350–450 | Low |
| 1 Tables | 3 (1a Ventas ~350–450, 1b Insumos/Movimientos ~300–400, 1c Compras ~350–450) | ~900–1,200 | **High** per slice; each PR < 800 |
| 2 1:1 components | 2 (2a forms ~350–450, 2b tags/buttons/tabs ~250–350) | ~600–800 | Medium |
| 3 No-clean-equivalent | 2 (3a empty/alert/loading ~150–250, 3b layout+Login ~250–350) | ~400–600 | Medium |
| 4 Messages + theme | 2 (4a messages ~450–550, 4b theme ~400–500) | ~800–1,000 | **High** per slice; split 4a/4b |
| 5 Cleanup | 1 (PR 5) | ~150–250 | Low |
| **Total** | **11 PRs** | **~3,350–4,300** | **High overall** |

```text
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
800-line budget risk: High
400-line budget risk: High
```

Decision resolved during design: **PrimeVue 4.5.5 MIT** (pinned); chain strategy **stacked-to-main** (auto-chain delivery, per preflight #509). Slice→PR mapping locked: 0→1, 1→3 (1a Ventas / 1b Insumos-Movimientos / 1c Compras), 2→2 (2a forms / 2b sweep), 3→2 (3a empty-alert-loading / 3b layout-Login), 4→2 (4a messages / 4b theme), 5→1.

### Suggested Work Units (per PR)

| Unit | Goal | Likely PR | Focused test command (in `frontend/`) | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Deps pin, dual registration, hosts, pilot spec, build baseline | PR 0 | `npm test -- tests/component/layout.spec.ts` | `npm run dev` boot (both frameworks render) | Revert PR 0; EP intact |
| 2 | DataTable adapter + Ventas table/view (nested expand) | PR 1a | `npm test -- table-filters ventas-table ventas-view` | `npm run dev` → /ventas expand+funnels | Revert PR 1a |
| 3 | Insumos/Movimientos/Socios/Devoluciones tables + views | PR 1b | `npm test -- insumos-table movimientos-table socios-table devoluciones-table devoluciones-view inventario-view finanzas-view` | `npm run dev` → /inventario /finanzas | Revert PR 1b |
| 4 | Compras + remaining tables + views | PR 1c | `npm test -- compras-table productos-table variantes-table bom-productos-table bom-insumos-table maestros-table omisiones-view usuarios-view dashboard-view` | `npm run dev` → /productos /dashboard | Revert PR 1c |
| 5 | Forms + dashboard panels 1:1 batch | PR 2a | `npm test -- insumo-form compras-form producto-form variante-form bom-producto-form bom-insumo-form maestro-form usuario-form socios-form movimientos-form liquidaciones-form devoluciones-form ventas-form dashboard-panels` | `npm run dev` → open each form dialog | Revert PR 2a |
| 6 | Tags/buttons/tabs/tooltip sweep | PR 2b | `npm test -- productos-view inventario-view finanzas-view maestros-view usuarios-view omisiones-view dashboard-view` | `npm run dev` → tab navigation + buttons | Revert PR 2b |
| 7 | empty/alert/loading sweep | PR 3a | `npm test` (audit el-empty/el-alert/v-loading assertions) | `npm run dev` → empty states + loading | Revert PR 3a |
| 8 | CSS grid shell + SidebarMenu nav + LoginView validation | PR 3b | `npm test -- layout login` | `npm run dev` → /login validation, sidebar nav | Revert PR 3b |
| 9 | Toast/ConfirmDialog services sweep + client.ts 403 | PR 4a | `npm test -- client-403` | `npm run dev` → trigger 403 + save/delete flows | Revert PR 4a; EP messages still available |
| 10 | Theme preset tokens + `.el-*` overrides + visual QA | PR 4b | `npm test` | `npm run dev` → dark-mode QA sign-off (BEH-4) | Revert PR 4b; EP CSS still present |
| 11 | Remove EP, lint/typecheck/format, final build compare | PR 5 | `npm test` (55 specs) | `npm run dev` full smoke; `npm run build` size ≤ B×1.10 | Revert PR 5 restores dual registration |

## Phase 1 — Slice 0: Foundations (PR 0)

- [x] **S0-T1** Add deps: `primevue@4.5.5` (exact pin), `@primeuix/themes@^2`, `primeicons` in `frontend/package.json` + `npm install`. Deps: —. Verify: `npm test` (additive; suite stays green).
- [x] **S0-T2** Create `frontend/src/styles/arpia-preset.ts` skeleton: `definePreset(AuraCompat, {...})`, dark scheme only, driven by `--arpia-*` vars (D2; full tokens in S4-T6). Deps: S0-T1. Verify: `npm test` + typecheck.
- [x] **S0-T3** Create `frontend/src/utils/locales/es-CO.ts`: authored es-CO object (~40 keys, D5 — paginator/aria/filter/datepicker values match EP es labels). Deps: S0-T1. Verify: imports clean; `npm test`.
- [x] **S0-T4** Create `frontend/src/utils/toast.ts` singleton: `setToastInstance`/`showToast(severity,summary,detail,life=3000)`, no-op before set (BEH-2 path). Deps: S0-T1. Verify: unit no-op coverage (extended in S4-T4).
- [x] **S0-T5** Modify `frontend/src/main.ts`: dual registration — keep `app.use(ElementPlus,{locale:es})`; add `app.use(PrimeVue,{theme:{preset:ArpiaPreset,options:{darkModeSelector:'html'}},locale:esCO})` + ToastService + ConfirmationService + `app.directive('tooltip', Tooltip)` (MIG-2). Deps: S0-T2..T4. Verify: dev boot; `npm test`.
- [x] **S0-T6** Modify `frontend/src/App.vue`: mount `<Toast position="top-right"/>` + `<ConfirmDialog/>` beside `<router-view/>`; capture `useToast()`/`useConfirm()` into singletons (D4). Update `frontend/tests/App.spec.ts` (hosts Teleport — attachTo if needed). Deps: S0-T5. Verify: `npm test -- App.spec`.
- [x] **S0-T7** Pilot spec: migrate `frontend/tests/component/layout.spec.ts` FIRST — per-component Tag/Button imports on the AppLayout mount, `attachTo: document.body` for Toast/ConfirmDialog hosts, keep `plugins:[ElementPlus]` only for el-menu assertions until S3 (proves per-component imports + Teleport + dual coexistence; MIG-4 slice-0 pilot). Deps: S0-T6. Verify: `npm test -- tests/component/layout.spec.ts`.
- [x] **S0-T8** Build baseline (MIG-3): `npm run build` in `frontend/`, record output size **B**. Deps: S0-T1. Verify: build completes; B recorded.
- [x] **S0-T9** PR-0 gate: full `npm test` green — 55 specs. Deps: all S0. Verify: `npm test` exit 0.

## Phase 2 — Slice 1: Tables (PRs 1a / 1b / 1c)

- [x] **S1-T1** RED adapter tests: extend `frontend/tests/unit/table-filters.spec.ts` — `parsePrimeVueFilters` (single/multi constraint, `{value:null}`→`[null]`→null via `parseColumnFilter`, `{text,value}` unwrap) + `parsePrimeVueSort` (1→asc, -1→desc, 0/undefined→null). Fails (funcs absent). Deps: —. Verify: RED on `npm test -- table-filters`.
- [x] **S1-T2** GREEN adapter: add `parsePrimeVueFilters`/`parsePrimeVueSort` to `frontend/src/utils/table-filters.ts` (D6 contract); `parseColumnFilter` UNCHANGED (9 callers). Deps: S1-T1. Verify: table-filters green (BEH-1).
- [x] **S1-T3** PR1a `VentasTable.vue`: DataTable lazy (`:value`, Column expander + `#expansion` nested DataTable, `#empty`, `:loading`, `@filter`/`@sort`→adapter→same emits, `:showFilterMenu`+`filterElement` for Canal/Estado, v-tooltip gift D8). Q8 guard: no new features. Deps: S1-T2. Verify: ventas specs (BEH-1/BEH-6).
- [x] **S1-T4** PR1a `VentasView.vue`: el-pagination→Paginator (`:totalRecords/:rows/:first/@page`, template FirstPageLink..CurrentPageReport). Deps: S1-T3. Verify: ventas-view.spec.
- [x] **S1-T5** PR1a migrate `ventas-table.spec.ts` (`.el-table__row`→`.p-datatable-row`, expander, gift tooltip aria) + `ventas-view.spec.ts` (paginator). Deps: S1-T3/T4.
- [x] **S1-T6** PR1a gate: `npm test` green (focused: table-filters, ventas-table, ventas-view).
- [x] **S1-T7** PR1b tables: `InsumosTable` (adapter), `MovimientosTable` (adapter), `SociosTable`, `DevolucionesTable` (nested expand, BEH-6) → DataTable lazy/`:loading`/`#empty`. Deps: S1-T2. Verify: per-table specs.
- [x] **S1-T8** PR1b views: `InventarioView`, `FinanzasView`, `DevolucionesView`, `AnalisisView` — DataTable + Paginator parts (AnalisisView 2 direct tables; FinanzasView liquidacion table); tabs/dialogs stay S2. Deps: S1-T7.
- [x] **S1-T9** PR1b migrate specs: insumos-table, movimientos-table, socios-table, devoluciones-table, devoluciones-view, inventario-view, finanzas-view (table selectors only; `.el-tabs__item` stays S2). Deps: S1-T7/T8.
- [x] **S1-T10** PR1b gate: `npm test` green.
- [x] **S1-T11** PR1c tables: `ComprasTable` (adapter), `ProductosTable`, `VariantesTable`, `BomProductosTable`, `BomInsumosTable`, `UsuariosTable`, `MaestrosTable`, `OmisionesTable`, `BajoStockTable`, `MargenTable` → DataTable (`:loading`, `#empty`, `@sort` adapter where wired). Deps: S1-T2. Verify: per-table specs.
- [x] **S1-T12** PR1c views: `ProductosView`, `UsuariosView`, `MaestrosView`, `OmisionesView`, `DashboardView` — table/paginator parts; tabs/dialogs stay S2. Deps: S1-T11.
- [x] **S1-T13** PR1c migrate specs: compras-table, productos-table, productos-view (table parts), variantes-table, bom-productos-table, bom-insumos-table, maestros-table, maestros-view, omisiones-view, usuarios-table, usuarios-view, dashboard-view, dashboard-panels (table parts). Deps: S1-T11/T12.
- [x] **S1-T14** PR1c gate: `npm test` green.

## Phase 3 — Slice 2: 1:1 Components (PRs 2a / 2b)

- [x] **S2-T1** PR2a forms+panels batch — VentasForm, InsumoForm, ComprasForm, ProductoForm, VarianteForm, BomProductoForm, BomInsumoForm, MaestroForm, UsuarioForm, SociosForm, MovimientosForm, LiquidacionesForm, DevolucionesForm, KpiCards, FinanzasMensualesChart, VentasMensualesChart: el-input→InputText, el-input-number→InputNumber (verify step/min/max), el-select/el-option→Select/SelectOption (`:options`+optionLabel), el-dialog→Dialog (`v-model:visible`, width→style, Teleport), el-date-picker→DatePicker (es-CO, BEH-7), el-card→Card, el-skeleton→Skeleton, el-switch→ToggleSwitch, el-progress→ProgressBar, el-form/el-form-item→plain divs (validation already manual; only LoginView had rules, D7). ElMessage service calls STAY until S4a. Deps: S0. Verify: form specs.
- [x] **S2-T2** PR2a migrate form specs (drop `plugins:[ElementPlus]`, `attachTo` for Dialog/DatePicker Teleport, `.el-select-dropdown__item`→`.p-select-option`): insumo-form, compras-form, producto-form, variante-form, bom-producto-form, bom-insumo-form, maestro-form, usuario-form, socios-form, movimientos-form, liquidaciones-form, devoluciones-form, ventas-form, dashboard-panels (`.el-skeleton`→`.p-skeleton`). Deps: S2-T1.
- [x] **S2-T3** PR2a gate: `npm test` green.
- [x] **S2-T4** PR2b tags/buttons/tabs/tooltip sweep — remaining el-tag→Tag (`type`→`severity`), el-button→Button (`type`→`severity`, `plain`→`text`, `native-type`→`type`) across views + table `#body` cells (SociosTable, MaestrosTable, OmisionesTable, UsuariosTable, ProductosTable, VariantesTable, BomProductosTable, BomInsumosTable, InsumosTable, ComprasTable, VentasView, UsuariosView, InventarioView, FinanzasView, MaestrosView, DevolucionesView, DashboardView, AnalisisView, OmisionesView, ProductosView); el-tabs/el-tab-pane→Tabs v4 (TabList/Tab/TabPanels/TabPanel) in ProductosView/InventarioView/FinanzasView/MaestrosView; el-tooltip→v-tooltip directive (D8). Deps: S1. Verify: view specs.
- [x] **S2-T5** PR2b migrate specs: productos-view, inventario-view, finanzas-view, maestros-view (`.el-tabs__item`→`.p-tab`), usuarios-view, omisiones-view, dashboard-view, ventas specs (button/tag selectors). Deps: S2-T4.
- [x] **S2-T6** PR2b gate: `npm test` green.

## Phase 4 — Slice 3: No-Clean-Equivalent (PRs 3a / 3b)

- [x] **S3-T1** PR3a empty/alert/loading sweep — el-empty→DataTable `#empty`/custom markup (description kept, BEH-6); el-alert→Message (`type`→`severity`) view error alerts; v-loading→`:loading`/Skeleton/overlay (CostoTree, AnalisisView, views). Deps: S1/S2. Verify: view specs.
- [x] **S3-T2** PR3a audit + update specs asserting el-empty/el-alert/v-loading behavior. Deps: S3-T1.
- [x] **S3-T3** PR3a gate: `npm test` green.
- [ ] **S3-T4** PR3b `AppLayout.vue`: CSS grid shell (D3) — el-container/el-header/el-aside/el-main → `.app-layout` `grid-template-areas` (aside 220px/header/main); `SidebarMenu.vue`: el-menu/el-menu-item → flat `<nav>`+`<router-link>` list, active class from `route.path`. Deps: S0-T7. Verify: layout.spec.
- [ ] **S3-T5** PR3b `LoginView.vue` manual validation (D7/BEH-3): InputText/Password/Button, blur-triggered email required+type / password required with exact messages ("Ingrese su correo electrónico", "El correo no es válido", "Ingrese su contraseña"), submit blocked while invalid, inline Message error for 401/connection, loading state. Deps: S3-T4. Verify: login.spec.
- [ ] **S3-T6** PR3b migrate `layout.spec.ts` (`.el-menu-item`→nav-link active assertions — final plugins drop) + `login.spec.ts` (validation messages, no request on invalid, alert→Message). Deps: S3-T4/T5.
- [ ] **S3-T7** PR3b gate: `npm test` green.

## Phase 5 — Slice 4: Messages + Theme (PRs 4a / 4b)

- [ ] **S4-T1** PR4a create `frontend/src/utils/confirm.ts`: `setConfirmInstance`/`confirmAction(opts): Promise<'accept'|'reject'>`. Deps: S0-T4 pattern. Verify: unit coverage.
- [ ] **S4-T2** PR4a messages sweep (BEH-5): ElMessage (104) + ElMessageBox (18) → `showToast`/`confirmAction` preserving severity+text across VentasView, VentasForm, UsuariosView, UsuarioForm, InventarioView, InsumoForm, ComprasForm, MaestrosView, MaestroForm, OmisionesView, MovimientosForm, SociosForm, LiquidacionesForm, DevolucionesForm, BomInsumoForm, BomProductoForm, useProductosCosto.ts, useProductosCatalog.ts, useProductosBom.ts (+ remaining). `await confirmAction`→`if (choice!=='accept') return`. Deps: S4-T1.
- [ ] **S4-T3** PR4a `frontend/src/api/client.ts` 403 interceptor (BEH-2): `ElMessage.error(FORBIDDEN_MESSAGE)` → `showToast('error','Acceso denegado',FORBIDDEN_MESSAGE)`; promise reject unchanged. Deps: S4-T2.
- [ ] **S4-T4** PR4a tests: update `frontend/tests/unit/client-403.spec.ts` (toast called + reject), add toast singleton no-op/set coverage, update specs asserting message behavior. Deps: S4-T2/T3.
- [ ] **S4-T5** PR4a gate: `npm test` green.
- [ ] **S4-T6** PR4b theme: `frontend/src/styles/main.css` — map 110 `--el-*` vars + `.el-*` overrides onto `--p-*` preset tokens, `--arpia-*` single source (BEH-4); complete `arpia-preset.ts` full token inventory (dark scheme). Deps: S0-T2. Verify: `npm test`; visual.
- [ ] **S4-T7** PR4b **VISUAL QA GATE (BEH-4 — not a code task)**: manual dark-mode QA — main views (tables, dialogs, forms, toasts) vs pre-migration: surfaces, text, borders, gold/lavender accents; CSS grid shell (D3) + AuraCompat 14px density under 16px root (D1) acceptance. **Sign-off REQUIRED before slice 5.** Deps: S4-T6. Verify: QA record committed.
- [ ] **S4-T8** PR4b gate: `npm test` green + QA sign-off recorded.

## Phase 6 — Slice 5: Cleanup (PR 5)

- [ ] **S5-T1** Remove EP (MIG-2): drop `element-plus` from `frontend/package.json`, `app.use(ElementPlus)` + `element-plus/dist/index.css` from `main.ts`; strip last `plugins:[ElementPlus]` in specs; audit zero `el-*`/`element-plus` refs in `frontend/src` + `frontend/tests` (MIG-1: diff isolated to `frontend/`). Deps: S4 gates. Verify: `npm test`.
- [ ] **S5-T2** Lint/typecheck/format: `npm run lint`, `npm run format`, `npx vue-tsc --noEmit` (or `npx tsc --noEmit` as configured). Deps: S5-T1.
- [ ] **S5-T3** Final build size (MIG-3): `npm run build` → S ≤ B×1.10 (B from S0-T8); record comparison. Deps: S5-T1.
- [ ] **S5-T4** Final gate: `npm test` green (55 specs) + zero EP refs + budget met → merge PR 5 (only after S4-T7 QA sign-off). Deps: S5-T1..T3.

## Task Coverage Matrix

| Requirement | Implementing tasks |
|---|---|
| MIG-1 frontend-only | All (isolation audit S5-T1; diff restricted to `frontend/`) |
| MIG-2 hybrid dual-registration | S0-T5, S0-T6, S5-T1 |
| MIG-3 build size ≤ B×1.10 | S0-T8 (baseline), S5-T3 (compare) |
| MIG-4 suite green per slice | S0-T7, S0-T9; per-PR gates S1-T6/T10/T14, S2-T3/T6, S3-T3/T7, S4-T5/T8, S5-T4 |
| BEH-1 filter/sort parity | S1-T1, S1-T2, S1-T3, S1-T5, S1-T7, S1-T11 |
| BEH-2 403 toast | S4-T3, S4-T4 |
| BEH-3 login validation | S3-T5, S3-T6 |
| BEH-4 dark theme parity | S4-T6 (tokens), S4-T7 (QA gate) |
| BEH-5 messages/confirmations | S4-T1, S4-T2 |
| BEH-6 workflows (expand/empty/loading) | S1-T3, S1-T7, S3-T1 |
| BEH-7 es-CO locale | S0-T3, S2-T1 (DatePicker) |

## Component Mapping Appendix — 42 remaining .vue files (per design mapping table)

| File | Slice-PR | Mappings applied |
|---|---|---|
| views/VentasView.vue | 1a, 2b, 4a | DataTable+Paginador; Button/Tag; Toast/ConfirmDialog |
| views/UsuariosView.vue | 1c, 2b, 4a | DataTable+Paginador; Button/Tag; Toast/ConfirmDialog |
| views/ProductosView.vue | 1c, 2b, 4a | DataTable+Paginador; Tabs v4; Toast/ConfirmDialog |
| views/OmisionesView.vue | 1c, 2b, 4a | DataTable+Paginador; Button/Tag; Toast |
| views/MaestrosView.vue | 1c, 2b, 4a | DataTable+Paginador; Tabs v4; Toast/ConfirmDialog |
| views/InventarioView.vue | 1b, 2b, 4a | DataTable+Paginador; Tabs v4; Toast/ConfirmDialog |
| views/FinanzasView.vue | 1b, 2b, 4a | DataTable+Paginador (liquidacion); Tabs v4; Toast |
| views/DevolucionesView.vue | 1b, 2b, 4a | DataTable+Paginador; Button/Tag; Toast |
| views/DashboardView.vue | 1c, 2a, 2b, 4a | DataTable containers; Card/Skeleton (2a); Button/Tag (2b); Toast |
| views/AnalisisView.vue | 1b, 2b, 4a | 2 direct DataTables; Button/Tag; Toast |
| views/RoutePlaceholder.vue | 5 | audit only (no EP tags expected) |
| components/ventas/VentasForm.vue | 2a, 4a | InputText/InputNumber/Select/Dialog/DatePicker; Toast |
| components/finanzas/SociosTable.vue | 1b, 2b | DataTable (:loading/#empty/@sort); Tag/Button cells |
| components/finanzas/SociosForm.vue | 2a, 4a | InputText/InputNumber/Select/Dialog; Toast |
| components/finanzas/MovimientosTable.vue | 1b, 2b | DataTable (adapter filters/sort); Tag/Button cells |
| components/finanzas/MovimientosForm.vue | 2a, 4a | InputText/InputNumber/Select/Dialog; Toast |
| components/finanzas/LiquidacionesForm.vue | 2a, 4a | InputNumber/Dialog/Button; Toast |
| components/devoluciones/DevolucionesTable.vue | 1b, 2b | DataTable nested expand; Tag/Button cells |
| components/devoluciones/DevolucionesForm.vue | 2a, 4a | InputNumber/Select/Dialog; Toast |
| components/dashboard/KpiCards.vue | 2a | Card, Skeleton |
| components/dashboard/FinanzasMensualesChart.vue | 2a | Card |
| components/dashboard/VentasMensualesChart.vue | 2a | Card |
| components/dashboard/BajoStockTable.vue | 1c, 2b | DataTable; Tag cells |
| components/dashboard/MargenTable.vue | 1c | DataTable |
| components/maestros/MaestroForm.vue | 2a, 4a | InputText/Select/Dialog; Toast |
| components/maestros/MaestrosTable.vue | 1c, 2b | DataTable; Tag/Button cells |
| components/omisiones/OmisionesTable.vue | 1c, 2b | DataTable; Button cells |
| components/inventario/ComprasForm.vue | 2a, 4a | Select/InputNumber/Dialog; Toast |
| components/inventario/InsumosTable.vue | 1b, 2b | DataTable (adapter); Tag/Button cells |
| components/inventario/InsumoForm.vue | 2a, 4a | InputText/InputNumber/Select/Dialog; Toast |
| components/inventario/ComprasTable.vue | 1c, 2b | DataTable (adapter); Tag/Button cells |
| components/usuarios/UsuariosTable.vue | 1c, 2b | DataTable; Tag/Button cells |
| components/usuarios/UsuarioForm.vue | 2a, 4a | InputText/Select/Dialog; Toast |
| components/productos/CostoTree.vue | 3a | v-loading→Skeleton/overlay |
| components/productos/BomProductosTable.vue | 1c, 2b | DataTable; Button cells |
| components/productos/BomProductoForm.vue | 2a, 4a | InputNumber/Select/Dialog; Toast |
| components/productos/BomInsumosTable.vue | 1c, 2b | DataTable; Button cells |
| components/productos/BomInsumoForm.vue | 2a, 4a | InputNumber/Select/Dialog; Toast |
| components/productos/ProductosTable.vue | 1c, 2b | DataTable (@sort); Tag/Button cells |
| components/productos/ProductoForm.vue | 2a, 4a | InputText/InputNumber/Select/Dialog/DatePicker; Toast |
| components/productos/VarianteForm.vue | 2a, 4a | InputText/InputNumber/Select/Dialog; Toast |
| components/productos/VariantesTable.vue | 1c, 2b | DataTable; Button cells |

Named in tasks above (5): `App.vue` (S0-T6), `VentasTable.vue` (S1-T3), `AppLayout.vue` (S0-T7 pilot + S3-T4), `SidebarMenu.vue` (S3-T4), `LoginView.vue` (S3-T5).

## Per-PR Verification Gates

| PR | Focused specs (frontend) | Full gate |
|---|---|---|
| 0 | layout.spec, App.spec | `npm test` (55) + build baseline B |
| 1a | table-filters, ventas-table, ventas-view | `npm test` |
| 1b | insumos/movimientos/socios/devoluciones tables+views | `npm test` |
| 1c | compras/productos/variantes/bom/maestros/omisiones/usuarios/dashboard | `npm test` |
| 2a | all form specs + dashboard-panels | `npm test` |
| 2b | productos/inventario/finanzas/maestros/usuarios/omisiones/dashboard views | `npm test` |
| 3a | audited empty/alert/loading specs | `npm test` |
| 3b | layout, login | `npm test` |
| 4a | client-403 + message specs | `npm test` |
| 4b | full suite + QA sign-off | `npm test` + dark-mode QA |
| 5 | full suite (55) + zero EP refs | `npm test` + S ≤ B×1.10 |