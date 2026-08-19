# Proposal: Frontend Migration Element Plus → PrimeVue 4.x (MIT)

## Intent

The ERP's operational core — ventas, compras, insumos, movimientos — runs on 21 `el-table` / 107 `el-table-column` (47 .vue files, 518 `<el-*>` tags). Element Plus has hit its table ceiling: no native row expansion with nested detail tables, no sticky/frozen columns, no virtual scroll, no CSV export, no richer filter/sort state. PrimeVue's DataTable covers all of these, and the user chose PrimeVue 4.x MIT (frozen, last MIT release) over licensed v5. This change migrates the frontend UI framework only — behavior, theme, and tests preserved, sliced so the suite stays green.

## Scope

### In Scope
- Frontend-only swap: `primevue@4.5.5` (exact pin, last MIT), `@primeuix/themes`, `primeicons`
- 47 .vue files + `frontend/src/main.ts` + `frontend/src/styles/main.css` (110 `--el-*` vars) + 32 test specs (21 with `.el-*` selectors)
- 6 slices: 0 foundations, 1 tables, 2 1:1 components, 3 no-clean-equivalent, 4 messages+theme, 5 cleanup
- License consequence documented and accepted: 4.5.5 is frozen forever (no patches)

### Out of Scope
- No backend/API changes
- No PrimeVue 5 / PrimeUI licensing (decided — not reopened)
- No Tailwind / unstyled mode
- No new DataTable features beyond current specs (Q8 guard: CSV export, virtual scroll, sticky, pin stay out unless a spec requires them)
- No Element Plus removal before slice 5

## Capabilities

**None** — pure framework refactor; no spec-level behavior change (frontend has no existing capability specs; server-side filter/sort semantics preserved per Q7).

## Approach

- **Hybrid dual-registration**: keep `app.use(ElementPlus)` through slice 4; add `app.use(PrimeVue, { theme: definePreset(Aura) + darkModeSelector, locale: esCO })` in slice 0
- **Per-slice green suite**: each slice independently mergeable; components imported per-file (no full-bundle)
- **Tests**: per-component imports (drop `plugins: [ElementPlus]`); `attachTo` for Teleport (Dialog/Toast/ConfirmDialog); `.el-*` → `.p-*` selectors in lockstep
- **Theme**: custom `definePreset(Aura)` mapping the 110 `--el-*` vars onto `--p-*` tokens, driven by existing `--arpia-*` brand vars (slice 4; slices 0–3 on Aura defaults + thin compat layer)
- **Messages**: Toast/ConfirmDialog singleton hosts in App.vue; `src/utils/toast.ts` service for the axios 403 interceptor (`frontend/src/api/client.ts`)
- **Locale**: es-CO plain object (~40 keys: paginator/datepicker/filter/aria) replacing `app.use(ElementPlus, { locale: es })`
- **LoginView**: el-form rules engine → manual validation with inline error states (matches the 13 existing forms; no new dependency)

## Key Decisions & Tradeoffs

| Decision | Choice | Tradeoff |
|---|---|---|
| Version/license | PrimeVue 4.5.5 MIT, pinned | Frozen, no future patches (accepted) vs v5 PrimeUI cost/eligibility/key |
| Migration strategy | Hybrid dual-registration | Bundle bloat during 0–4 vs big-bang 4–6-week unreviewable branch |
| Theming | `definePreset(Aura)` + `--arpia-*` | Token inventory work (slice 4) vs double `.el-*`/`.p-*` CSS debt |
| Test strategy | Per-component imports | Spec rewrites unavoidable (selectors) |
| Form validation | Manual LoginView port | No rules engine; parity with 13 manual forms |

## Risks

| Risk | Sev | Mitigation |
|---|---|---|
| Test suite rewrites: 32 specs + 21 selector files; Teleport in jsdom | HIGH | Lockstep per-slice; slice-0 pilot; ResizeObserver polyfill exists |
| Theme fidelity: 110 vars → preset, no mechanical path | MED-HIGH | Dedicated slice 4; `--arpia-*`-driven; visual QA |
| DataTable payload/slot deltas; `parseColumnFilter` (9 callers) | MED | Slice-1 adapter + updated unit tests |
| LoginView validation port | MED | Manual inline error states |
| Frozen 4.5.5: no security patches ever | LOW-MED (accepted) | Pin exact; monitor community fork landscape |
| Dual-framework bloat; `el-*`/`p-*` mixing | LOW-MED | Slice-5 cleanup; review discipline |
| Build size delta; es-CO parity; v-tooltip rework | LOW | Measure slice 0 vs 5; authored locale; ventas-table.spec |

## Open Questions (spec/design — non-blocking)

1. 16px baseline vs `-compat` 14px presets (root font-size; EP is 14px-era)
2. Aura vs Lara as `definePreset` base
3. App.vue `el-container` → CSS grid visual acceptance
4. Toast/ConfirmDialog host placement + singleton API shape
5. es-CO locale key inventory vs current EP es labels
6. Server-side filter semantics parity (DataTable `lazy` `@filter`/`@sort`, funnel UX)
7. Bundle budget baseline in slice 0 (e.g. ≤ current +10%)

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/main.ts` | Modified | Dual registration → slice-5 removal |
| `frontend/src/styles/main.css` | Modified | `--el-*` → `--p-*` preset (slice 4) |
| `frontend/src/api/client.ts` | Modified | 403 interceptor → Toast singleton (slice 4) |
| `frontend/src/utils/table-filters.ts` | Modified | EP filter payload → typed emit adapter (slice 1) |
| 47 `.vue` files | Modified | `el-*` → `p-*` (slices 0–4) |
| `frontend/tests/**` (32 specs) | Modified | Plugins removal, selectors, attachTo |

## Rollback Plan

- Each slice ships as its own PR in the feature chain → revert the offending slice's PR; EP stays functional through slice 4 via dual registration
- Abort = stop chain at current head; EP fully intact (only additive changes before slice 5)
- Slice 5 (EP removal) is the only destructive step — gate on full green suite + visual QA before merge

## Dependencies

- `primevue@4.5.5` (exact pin), `@primeuix/themes` (v2.x), `primeicons`

## Success Criteria

- [ ] Suite green at every slice; 21 `.el-*` selector specs migrated
- [ ] Zero `el-*`/`element-plus` references after slice 5
- [ ] Dark editorial theme visually matches (slice-4 QA)
- [ ] 403 Toast message works from `client.ts`
- [ ] Build size ≤ baseline +10% (slice 0 measure, slice 5 verify)
- [ ] No backend changes (diff isolated to `frontend/`)

## Review Workload Forecast

| Slice | Est. changed lines (add+del) | 800-line budget risk |
|---|---|---|
| 0 Foundations | ~350–450 | Low |
| 1 Tables | ~900–1,200 | **High** → split into 2–3 PRs |
| 2 1:1 components | ~600–800 | Medium → split if needed |
| 3 No-clean-equivalent | ~400–600 | Medium |
| 4 Messages+theme | ~800–1,000 | **High** → split messages vs theme |
| 5 Cleanup | ~150–250 | Low |
| **Total** | **~3,200–4,300** | **High overall** |

- **Decision needed before apply: Yes** (resolved: PrimeVue 4.5.5 MIT)
- **Chained PRs recommended: Yes** (auto-chain; stacked-to-main per preflight #509)
- **800-line budget risk: High** (overall; slices 1 and 4 exceed on their own)
- Slice→PR mapping: 0→1 PR; 1→3 PRs (Ventas incl. nested expand, Insumos/Movimientos, Compras); 2→2 PRs (batch A forms/views, batch B); 3→2 PRs (empty/alert/loading, layout+LoginView); 4→2 PRs (messages sweep, theme); 5→1 PR