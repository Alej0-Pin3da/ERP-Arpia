# Exploration — migracion-primevue (ERP-Arpia)

**Change**: `migracion-primevue`
**Date**: 2026-08-15
**Phase**: sdd-explore
**Baseline**: census observation #507 (2026-08-14) — spot-checked against current code, still accurate (HEAD `a2cdee6`, unchanged since census).

---

## Executive Summary

Migrating the ERP-Arpia frontend from Element Plus 2.9.3 (full-bundle global registration) to PrimeVue is **viable but HIGH effort and now carries a licensing decision that did not exist when the migration was first discussed**. PrimeTek archived the primevue GitHub repo (2026-06-28) and moved PrimeVue 5.x under the **PrimeUI license** (commercial $599/dev launch price, or a free Community license with strict eligibility and annual renewal); **only PrimeVue ≤ 4.5.5 remains MIT forever**. This forces a version decision (frozen MIT 4.5.5 vs licensed 5.0.1) that the user must make before any proposal work. The technical migration itself is a ~4–6 week, 6-slice effort centered on three hard focuses: el-table → DataTable (18 files, 107 columns), the dark editorial theme (110 `--el-*` var references in main.css → a custom `@primeuix/themes` preset), and ElMessage/ElMessageBox (~104 call sites in 24 files, including the axios 403 interceptor). A dual-framework transition (both registered until the final slice) is the recommended path because it keeps the suite green at every slice and allows the test suite to migrate in lockstep.

**Verdict**: conditionally viable — proceed to proposal ONLY after the user resolves the PrimeVue version/license question and accepts the theme/table/test rewrite scope.

---

## 1. Current-State Analysis (verified against code, 2026-08-15)

### 1.1 Stack (frontend/package.json — verified)
- `vue ^3.5.13`, `vue-router ^4.5.0`, `pinia ^3.0.1`, `axios ^1.19.0`
- `element-plus ^2.9.3` (full bundle), `echarts ^5.6.0` + `vue-echarts ^7.0.3`
- `vite ^6.0.7`, `vitest ^3.0.5`, `@vue/test-utils ^2.4.6`, `jsdom ^25.0.1`, `typescript ~5.7.3`
- Vite config: vitest environment `jsdom`, `globals: true`, setup file `tests/setup.ts`, alias `@ → src`

### 1.2 Element Plus surface (census #507, spot-checked)
- **Registration**: `frontend/src/main.ts` — `app.use(ElementPlus, { locale: es })` + `import 'element-plus/dist/index.css'` (full-bundle global registration; NO auto-import, NO `@element-plus/icons-vue`).
- **Template surface**: 47 `.vue` files, **518 `<el-*>` tags**, 30 distinct components. Tag census (recounted): el-table-column **107**, el-button 67, el-form-item 45, el-option 38, el-col 37, el-select 28, el-input 22, el-table **21**, el-input-number 21, el-empty 20, el-form 14, el-row 13, el-dialog 12, el-tab-pane 11, el-alert 11, el-tag 11, el-pagination 10, el-card 7, el-tabs 6, el-date-picker 3, el-skeleton 3, el-container 2, el-switch 2, 1 each: el-main, el-menu, el-menu-item, el-header, el-aside, el-progress, el-tooltip.
- **Messages**: 24 files use `ElMessage`/`ElMessageBox`; 104 `ElMessage` calls (36 error / 35 success / 33 warning) + 18 `ElMessageBox` references.
- **Tests**: 32 specs mount with `global: { plugins: [ElementPlus] }`; 21 spec files use `.el-*` class selectors (e.g. `.el-table__row`). `tests/setup.ts` already polyfills `ResizeObserver` (framework-agnostic — reusable for PrimeVue).

### 1.3 Key patterns (verified via codegraph + reads)
- **Server-side table filtering/sorting**: `parseColumnFilter` (`frontend/src/utils/table-filters.ts`) normalizes el-table `filter-change` payloads (`Record<columnKey, unknown[]>` → single value); **9 callers across 4 tables** (VentasTable, InsumosTable, MovimientosTable, ComprasTable) + its own unit test (`tests/unit/table-filters.spec.ts`). `onSortChange` normalizes el-table `sort-change` (`ascending/descending/null` → `asc/desc/null`) and is duplicated in 3+ tables.
- **Nested-table peak complexity**: `VentasTable.vue` — `el-table type="expand"` containing a **nested `el-table`** of detalles, header funnel filters (canal/estado), sortable columns, emoji gift button wrapped in `el-tooltip`, row-conditional actions, `#empty` slot with `el-empty`.
- **Form validation**: ONLY `LoginView.vue` uses the el-form **rules engine** (`FormRules` + `formRef.validate()`, email type + required, blur triggers, `el-alert` inline error). The other 13 forms validate manually with `ElMessage.warning`.
- **Out-of-component messaging**: `frontend/src/api/client.ts` axios response interceptor calls `ElMessage.error(FORBIDDEN_MESSAGE)` on 403 — the one ElMessage call site **outside a component context** (no reactive scope; needs a singleton-style service in PrimeVue).
- **Theme**: `frontend/src/styles/main.css` — **343 lines**, **110 `--el-*` var references**, 17 `.el-*` overrides; dark editorial brand (gold accent, brand gradients, `--arpia-*` custom vars also present). Scoped `.el-*` references exist in components too (e.g. `.venta-detail-table` uses `--el-fill-color-lighter`).
- **Layout**: `App.vue` shell uses `el-container/el-header/el-aside/el-main` + `el-menu`; LoginView has a bespoke layout (`.login-page`/`.login-card`).

---

## 2. PrimeVue Landscape (2026-08-15 — current facts)

### 2.1 Version & licensing (CRITICAL NEW FACT)
| | PrimeVue 4.5.5 | PrimeVue 5.0.1 |
|---|---|---|
| Released | 2026-04-08 | 2026-07-15 (5.0.1: 2026-08-13) |
| License | **MIT, forever** | **PrimeUI license — NOT open source** |
| Maintenance | Frozen (repo archived 2026-06-28; no patches) | Active under PrimeUI (primevue.dev) |
| Cost | Free | Commercial $599/dev (launch through 2026, then $799; renewals $399/dev/yr) OR Community (free for <$1M revenue, <5 devs, <10 employees, <$3M VC; **annual renewal**; license key required; missing/invalid key → license notice) |
| Docs | primevue.org (v4 docs still live) | primevue.dev |

### 2.2 Theming (PrimeVue 4/5 styled mode)
- Styled mode is the fit: this app has **no Tailwind**, so unstyled mode + `tailwindcss-primeui` is out of scope.
- `app.use(PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: '.my-app-dark', cssVariables: true } } })`.
- Presets from **`@primeuix/themes`** (v2.x): Aura, Lara, Nora, Material (+ `-compat` 14px variants). Customization via **`definePreset(Aura, {...})`** token overrides — this is the mechanical home for the current `--el-*` palette → `--p-*` tokens.
- Dark mode is class-selector driven (`.my-app-dark`) — matches this app's class-based dark editorial theme.
- Locale is a plain object: `app.use(PrimeVue, { locale: { accept: 'Aceptar', ... } })` or `usePrimeVue().config.locale`. **No bundled es locale** — a custom es-CO object (~40 keys: paginator, datepicker, filter operators, aria) must be authored. Direct 1:1 replacement for `app.use(ElementPlus, { locale: es })`.

### 2.3 Component registration & packages
- **No full-bundle global registration** in PrimeVue: `app.use(PrimeVue)` only installs config/theme. Components are imported per-file (tree-shaking) or auto-imported via `unplugin-vue-components` + `@primevue/auto-import-resolver`.
- Required packages: `primevue` (+ `@primeuix/themes` + `primeicons` with `import 'primeicons/primeicons.css'`).
- This changes the test strategy: the `plugins: [ElementPlus]` pattern disappears — components resolve from SFC imports, so specs mount views with only router/pinia plugins as needed.

### 2.4 Key component mappings (validated against v4 docs)
| EP | PrimeVue 4 | Delta |
|---|---|---|
| el-table / el-table-column | **DataTable / Column** | `#default`→`#body` slots; filter API (`v-model:filters`, `filterDisplay`, `filterMatchMode`); sort via `sortable` + `@sort`/`lazy`; expand via `<Column expander>` + `#expansion` template + `v-model:expandedRows` (nested DataTable in expansion works natively); `rowClass`/`rowStyle`; `scrollable` + frozen (sticky) columns; `virtualScroller`; `exportCSV`; `paginator` |
| el-tag | Tag | `type` → `severity` mapping |
| el-button | Button | `type/plain/link` → `severity/text/link` mapping |
| el-input / el-input-number | InputText / InputNumber | API close; InputNumber keydown semantics differ |
| el-select / el-option | Select / SelectOption | Options API differs; groups via `optionGroup` |
| el-dialog | Dialog | Close; Teleport-based |
| el-tabs / el-tab-pane | Tabs / TabList / TabPanel | **API differs significantly** (v4 structure) |
| el-pagination | Paginator | `page-size/current-page` vs `rows/first` |
| el-date-picker | DatePicker | v4 naming; locale-driven |
| el-skeleton | Skeleton | Near 1:1 |
| el-card | Card | Near 1:1 |
| el-switch | ToggleSwitch | v4 rename of InputSwitch |
| el-progress | ProgressBar | Close |
| el-tooltip | **v-tooltip directive** | EP component → PrimeVue **directive**; VentasTable wrapper pattern must be reworked |
| el-message / ElMessage | **Toast service** (`useToast()` + `<Toast />` host) | Service pattern; host component must be mounted (App.vue) |
| ElMessageBox | **ConfirmDialog service** (`useConfirm()` + `<ConfirmDialog />` host) | Service pattern |
| el-form / el-form-item | **NONE (no validation engine)** | Manual validation + error states |
| el-empty | **NONE** | DataTable `#empty` template / custom markup |
| el-alert | **Message** component | Close visual port |
| v-loading | **None direct** | DataTable `:loading` / BlockUI / Skeleton |
| el-container/header/aside/main | **NONE** | Plain CSS grid/layout replacement |

### 2.5 Test strategy for PrimeVue in vitest+jsdom
- Components imported in SFCs resolve without global plugins — specs simplify (drop `plugins: [ElementPlus]`).
- Teleport-based components (Dialog, Toast, ConfirmDialog, Tooltip, DatePicker overlay) need `attachTo: document.body` or Teleport stubs in jsdom.
- `ResizeObserver` polyfill already present in `tests/setup.ts` (DataTable needs it too).
- Selector rewrite: `.el-table__row` → `.p-datatable-row` (and `.el-*` → `.p-*` throughout).

---

## 3. Approaches Considered

### 3.1 Migration strategy: full replacement vs hybrid transition
| | Full replacement (big-bang) | Hybrid dual-registration (recommended) |
|---|---|---|
| Pros | Single cleanup; no bundle bloat period | Every slice is independently green/mergeable; tests migrate in lockstep; real user feedback after each slice; the 403 interceptor keeps working until slice 4 |
| Cons | Huge single PR; 4-6 weeks without a reviewable delivery; high risk of long-lived broken branch | Both frameworks in the bundle during transition (~1–2 MB extra JS/CSS, acceptable for an internal tool); discipline needed to not mix `el-*`/`p-*` in one file |
| Effort | High | Medium per slice, same total |

**Recommendation**: hybrid, sliced. This also aligns with the preflight decision `delivery_strategy=auto-chain` and the 800-line review budget.

### 3.2 Version/license: PrimeVue 4.5.5 (MIT frozen) vs 5.0.1 (PrimeUI)
| | 4.5.5 MIT | 5.0.1 PrimeUI |
|---|---|---|
| Pros | Free, MIT forever, docs complete, all census advantages validated against v4, zero procurement | Active development, future fixes/features, 16px baseline presets (v5) |
| Cons | Frozen: no security patches ever; community fork risk (PrimeNG already forked); aging against Vue/browser updates | **License cost or eligibility + annual renewal + license key in CI/CD**; v5 is 2 days old (docs/migration tooling immature); `-compat` 14px presets only maintained until 2027 (v5 sizing change) |

**Recommendation**: decision deferred to the user (open question Q1). Technical exploration favors **4.5.5** (MIT, feature-complete, all mappings verified against v4) unless the org values active maintenance enough to pay/qualify for PrimeUI. If 5.x is chosen, the design must include the 16px baseline change (currently EP assumes 14px-era sizing) and license-key handling.

### 3.3 Theming: preset strategy
| | Custom `definePreset(Aura)` (recommended) | Keep `.el-*` overrides and add `.p-*` on top | Unstyled + Tailwind |
|---|---|---|---|
| Pros | Single token source; dark via `darkModeSelector`; mechanical mapping for the 110 vars | Least upfront work | Max flexibility |
| Cons | Requires full token inventory of the editorial palette | Double CSS maintenance; specificity battles | App has no Tailwind; new dependency + rewrite of all component styles |
| Effort | Medium | Low (but debt) | High |

**Recommendation**: custom `definePreset(Aura, ...)` — map the 110 `--el-*` vars onto `--p-*` tokens in one preset file, driven by the existing `--arpia-*` brand vars (gold, gradients, surfaces). Slice 4 owns this; slices 0–3 run on Aura defaults + a thin compatibility layer so visuals stay acceptable mid-migration.

### 3.4 Test strategy
| | Per-component imports (recommended) | Stub all PrimeVue components | Keep EP plugin + add PrimeVue plugin |
|---|---|---|---|
| Pros | Mirrors production; simpler mounts; tree-shaking-consistent | Fast specs | Smallest diff per spec |
| Cons | Requires spec rewrites (already needed for `.el-*` selectors anyway) | Masks real rendering (nested tables, expand) | Duplicates full-bundle cost in tests; EP and PV can't both own `plugins` cleanly |
| Effort | Medium | Low | Low (but wrong) |

**Recommendation**: per-component imports, `attachTo` for Teleport components, selectors migrated `.el-*` → `.p-*` in lockstep with each slice.

### 3.5 Form validation (LoginView)
PrimeVue has **no form rules engine**. Options: (a) manual validation with inline error states (matches the 13 existing forms — lowest risk), (b) bring a validation lib (VeeValidate — new dependency). **Recommendation**: (a) manual validation ported into LoginView with visible error text, preserving the `el-alert` inline error via a Message/inline div. Keeps the no-new-dependency posture.

---

## 4. Suggested Slice / PR Breakdown (validated against code)

Validated against the census and codegraph blast radius. Delivery: auto-chain (per preflight #509), ~800-line review budget per slice; each slice independently green.

- **Slice 0 — Foundations** (PR): add `primevue@4.5.5`, `@primeuix/themes`, `primeicons`; dual registration in `main.ts` (keep EP + `app.use(PrimeVue, { theme, locale-esCO })`); `definePreset(Aura)` skeleton + es-CO locale object; mount `<Toast />`/`<ConfirmDialog />` hosts in App.vue; build-size baseline measurement; pilot: migrate ONE spec + ONE simple component (e.g. a Button usage) to prove the test strategy. **Decision needed before apply: yes** (version/license).
- **Slice 1 — Tables** (PRs, highest risk): `table-filters.ts` adapter (PrimeVue filter payload → typed emit) replacing `parseColumnFilter` usage across the 4 tables; migrate 18 table files to DataTable (VentasTable nested expand, InsumosTable `rowClass`, header funnels, `#empty`); tests `.el-table__row` → `.p-datatable-row` + sort/filter payload specs.
- **Slice 2 — 1:1 components** (PRs): el-button/input/input-number/tag/dialog/tabs/skeleton/card/switch/progress/tooltip → Button/InputText/InputNumber/Tag/Dialog/Tabs/Skeleton/Card/ToggleSwitch/ProgressBar/v-tooltip across views/forms; per-file `el-*` → `p-*` selector updates.
- **Slice 3 — No-clean-equivalent** (PRs): el-empty (19 files), el-form/el-form-item (14), el-alert (11), v-loading (17), el-container layout (App.vue shell → CSS grid), LoginView manual validation port.
- **Slice 4 — Messages + theme** (PRs): sweep remaining `ElMessage`/`ElMessageBox` (24 files) → toast/confirm services (incl. `client.ts` 403 interceptor singleton); main.css `--el-*`/`.el-*` → `--p-*` preset tokens; full dark-editorial visual QA.
- **Slice 5 — Cleanup** (PR): remove `element-plus` dep + main.ts registration + `element-plus/dist/index.css`; strip `plugins: [ElementPlus]` from the last specs; typecheck/lint/prettier; final build-size comparison; docs.

Order rationale: tables first (biggest risk, longest lead) while the theme still tolerates defaults; messages last because the dual-registration keeps the interceptor safe until then; theme after the component surface is settled so the preset covers the final component set.

---

## 5. Open Questions / Unknowns (for proposal phase)

1. **PrimeVue version + license — USER DECISION, blocks proposal**: 4.5.5 (MIT, frozen) vs 5.0.1 (PrimeUI commercial/Community+annual renewal+key). If 5.x: does ERP-Arpia qualify for Community (revenue/dev/employee/VC thresholds)? Who owns the license key and CI/CD verification?
2. **16px baseline**: EP assumes ~14px-era sizing; PrimeVue v4 presets assume 16px (v5 documents this explicitly). Confirm the app's root font-size and whether `-compat` 14px presets are needed (v4) or a root-size change is acceptable (v5).
3. **Theme base preset**: Aura (PrimeTek vision) vs Lara (Bootstrap-like) as the `definePreset` base for the editorial dark look — design-phase decision.
4. **Layout replacement**: App.vue `el-container` shell → CSS grid — acceptable visual change? (No PrimeVue equivalent.)
5. **Toast/ConfirmDialog host placement + singleton API**: confirm `src/utils/toast.ts` (or `useToast` usage) as the home for the interceptor's 403 message; group/position conventions.
6. **es-CO locale object**: author ~40 keys (paginator/datepicker/filter/aria) — confirm key inventory matches EP es locale behavior users see today.
7. **Table filtering semantics**: keep server-side filtering (current) — DataTable `lazy` + `@filter`/`@sort` mapping; confirm no behavior change (e.g. funnel UX parity).
8. **Scope guard**: PrimeVue DataTable extras (CSV export, virtual scroll, sticky, pin) are NOT required by any current spec — confirm they stay out of scope.
9. **Bundle budget**: EP full bundle vs tree-shaken PrimeVue — expect a net reduction; set a numeric budget in slice 0 (e.g. ≤ current +10%) and verify in slice 5.

---

## 6. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | **PrimeVue 5 licensing**: commercial cost / Community eligibility + annual renewal + license key; or frozen 4.5.5 with zero future patches (security/feature stagnation, community-fork landscape) | **HIGH** | User decision before proposal; if 5.x, confirm eligibility + key handling; if 4.5.5, accept frozen maintenance window and document it |
| 2 | **Test suite rewrites**: 32 specs (plugins) + 21 spec files (`.el-*` selectors) rewritten; PrimeVue Teleport components need `attachTo`/stubs in jsdom | **HIGH** | Lockstep per-slice spec migration; pilot in slice 0; ResizeObserver polyfill already present |
| 3 | **Theme fidelity**: 110 `--el-*` vars + `.el-*` overrides → custom preset; no mechanical path; visual QA on the dark editorial look | **MEDIUM-HIGH** | Dedicated slice 4; preset driven by existing `--arpia-*` brand vars; screenshots/manual QA |
| 4 | **DataTable payload/slot deltas**: `filter-change` payload shapes, `#default`→`#body`, sort payloads; `parseColumnFilter` (9 callers) needs an adapter | **MEDIUM** | Slice 1 owns an adapter + updated unit tests; codegraph blast radius known |
| 5 | **Forms without validation engine**: LoginView rules → manual validation; visual parity risk on the only rules-based form | **MEDIUM** | Manual port with inline error states (matches other 13 forms); no new dependency |
| 6 | **Dual-framework transition**: bundle bloat during slices 0–4; accidental `el-*`/`p-*` mixing in one file | **LOW-MEDIUM** | Slice-5 cleanup guarantees; review discipline; acceptable for internal tool |
| 7 | **Build size**: unknown delta until measured (EP full bundle ≈ large; PrimeVue base + primeicons + styled tokens) | **LOW** | Measure in slice 0; budget in slice 5 |
| 8 | **Locale parity**: custom es-CO locale object must replicate EP es labels (paginator/datepicker) | **LOW** | Authored in slice 0; QA in slice 4 |
| 9 | **el-tooltip → v-tooltip directive**: VentasTable wrapper pattern rework; aria-label preservation | **LOW** | Slice 2 item; covered by existing ventas-table.spec |
| 10 | **v5 immaturity** (only if 5.x chosen): 5.0.1 is 2 days old; migration tooling/docs still landing | **MEDIUM (if 5.x)** | Prefer 4.5.5 unless active maintenance is valued; freeze pin if 5.x |

---

## Ready for Proposal

**Yes — pending the PrimeVue version/license decision (Q1).** The orchestrator should present the licensing reality (PrimeUI change, July 2026) to the user first: choosing between frozen MIT 4.5.5 and licensed 5.0.1 determines cost, maintenance posture, and the 16px baseline question. Everything else (slices, mappings, test strategy, theming) is resolved enough for proposal, spec, and design work. Note for the proposal: the openspec config's `strict_tdd: true` and backend-oriented testing config apply to backend phases; the frontend migration will need its own frontend test command wired (`npm run test` in frontend/).