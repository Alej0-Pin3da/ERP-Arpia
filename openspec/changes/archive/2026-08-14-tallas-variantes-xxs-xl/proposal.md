# Proposal: Tallas de variantes (XXS–XL)

## Intent

User wants size variants **XXS–XL** on sized garments and the historical VENTAS/PRENDAS sizes wired into catalog + sales migration. Today `Variantes_Producto` is empty and sizes are silently dropped. Once variants exist, 2 size-less sale rows would hard-fail F5 and re-runs would duplicate the 21 sales. This change seeds variants, adds the missing Set Celeno product, hardens F5 (omit+report, idempotency), and tightens the ventas UX.

## Scope

### In Scope
- Seed **6 sizes (XXS..XL)** for Set Aelo, Set Ocipete, Set Celeno, Blusa Manga Larga, Blusa Manga Corta → 30 variants, `precio_venta` NULL (sizes share product price).
- Add **Set Celeno** product @75000 (Decision 1).
- F5 **omit + report** the 2 size-less rows (SET OCIPETE 28/3, BLUSA MANGA LARGA 5/8).
- F5 **idempotency**: NULL-variant matching in `_contar_existentes`.
- VentasForm: variant select **REQUIRED** when product has variants; combos stay single-line NULL-variant.
- Tests: catalog count 13→14, variant counts, sales omit + idempotency.

### Out of Scope
Stock by size · per-component combo sizes (documented limitation) · Set Celeno BOM recipe (no source sheet) + Caja combo truth-wiring · PRENDAS migration · schema change (no Alembic).

## Capabilities

### New Capabilities
- `migracion-catalogos`: variant seeding via PRODUCTOS_CATALOGO tuples, Set Celeno entry, F5 omit+report policy, F5 idempotency fix.
- `ventas-variantes`: VentasForm variant-required UX for sized products.

### Modified Capabilities
None — `productos` Variante_Producto CRUD unchanged; no API/spec behavior change.

## Approach

Catalog-data + migration wiring + frontend hardening. No schema change: `Variantes_Producto`, schemas, routes, admin CRUD all exist. Seeding reuses `upsert_producto`. F5 gains an omit+report path **before** the explosion root guard and NULL-matching idempotency.

## Decisions Locked

1. **Set Celeno: ADD @75000** — real product (combo cost 129388 matches WITH it); 75000 matches PRENDAS "Conjunto bicolor" @75000 (exploration 2.7); 65000 appears once in CAJAS bottom (discount/mis-entry). No BOM/combo wiring this change.
2. **Size domain: all six (XXS..XL)** — user explicitly asked "desde la XXS hasta la XL"; extra extremes free to seed, future-proof.
3. **F5 omit+report**: skip the 2 rows, report (product, date, qty, reason); never invent a default variant (VTA-4/EXM-2).
4. **Idempotency: NULL-matching** in `_contar_existentes` — treat NULL-variant DB row as matching when the plan line resolves a variant; self-contained, no row-identity loss. Delete+reinsert rejected.
5. **Combo component sizes: documented limitation** — one `variante_id` per detail; `BomProducto.variante_id` out of scope.

## First-Slice Boundaries

- **Slice 1 (this change)**: variant seeding, Set Celeno, F5 omit+report + idempotency, VentasForm hardening, tests.
- **Later**: Celeno BOM recipe + Caja combo truth; canonical size display ordering; per-member combo sizes; stock-by-size.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/migrate/catalog.py` | Modified | `variantes` tuples; Set Celeno entry |
| `backend/migrate/sales.py` | Modified | omit+report; idempotency |
| `backend/migrate/validate.py` | Modified | N7 aware of omitted rows |
| `backend/tests/test_migrate_catalog.py` | Modified | count 13→14; variant counts |
| `backend/tests/test_migrate_sales.py` | Modified | omit + idempotency tests |
| `frontend/src/components/ventas/VentasForm.vue` | Modified | variant required for sized products |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| F5 hard-fail on size-less rows | High (today) | omit+report |
| Duplicate sales on re-run | High | NULL-matching idempotency |
| Catalog-count test breaks | Certain | Intentional 13→14 update |
| Celeno price inconsistency | Certain | Locked 75000, documented |
| Combo sizes lost | Certain | Documented limitation |

## Rollback Plan

Data-only: remove Set Celeno + its variants (no FK refs — no BOM/combo wiring yet); re-seed variants by re-running F1 (idempotent); omit+report gated behind a fail-fast toggle if needed.

## Dependencies

None external. Sources: VENTAS CSV, workbook, PRODUCTOS_CATALOGO.

## Success Criteria

- [ ] F1 seeds 30 variants across 5 sized products, `precio_venta` NULL
- [ ] Set Celeno in catalog @75000; `conteo_productos == 14`
- [ ] F5 completes: 2 rows omitted + reported, no DomainValidationError, re-run yields no duplicates
- [ ] VentasForm requires variant on sized products; combos remain single-line NULL-variant
- [ ] `pytest backend/tests -q` green