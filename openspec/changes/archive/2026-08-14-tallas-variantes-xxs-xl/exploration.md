# Exploration: Tallas de variantes (XXS–XL)

Status: `explored` · Next: `propose`

## 1. Problem framing

The ERP catalog (13 products) has an empty `Variantes_Producto` table. The user
wants size variants from **XXS to XL**. The historical data (VENTAS CSV,
INVENTARIO OCT25 PRENDAS section) carries sizes that today are silently dropped.
This exploration maps: (a) which products carry sizes, (b) how the historical
data maps to variants, (c) how the migration pipeline (backend/migrate/) must be
wired, (d) risks and constraints (tests, idempotency, combo explosion).

## 2. Key findings

### 2.1 Which products carry sizes (data-backed)

Observed size domain in data: **XS, S, M, L** (VENTAS CSV uses letters; PRENDAS
uses bra sizes `32 (XS)`, `34 (S)`, `36 (M)`, `38 (L)`). User requests the
canonical range **XXS, XS, S, M, L, XL** — the extra extremes have no historical
data but are cheap to seed.

| Product | VENTAS CSV | PRENDAS OCT25 | Verdict |
|---|---|---|---|
| Set Aelo (2) | S, XS | Corset encaje rojo pastel 34(S)/36(M)/38(L) @110000 | **VARIANTS** |
| Set Ocipete (3) | S | Bustier encaje negro 34(S)/36(M)/38(L) @95000 | **VARIANTS** |
| Set Celeno — **NOT in catalog** | combo col D (S) | Conjunto bicolor S:3/M:3/L:2 @75000 | **VARIANTS + NEW PRODUCT** |
| Blusa Manga Larga (6) | M | Blusa maya...larga XS/S/M/L @90000 | **VARIANTS** |
| Blusa Manga Corta (7) | — | Blusa maya...corta XS:2/S:2/M:3/L:1 @80000 | **VARIANTS** (no sales) |
| Corset Garras (4) | 4× no size | — | no variants |
| Falda Emily (5) | no size | — | no variants |
| Tote Bag Arpia (8) | no size | — | no variants |
| Bralete (1), Artemisia (3), Hypatia (4) | — | — | no variants |
| Combos (11, 12, 13) | bundle row | — | no variants (see 2.3) |

### 2.2 Set Celeno is a real product missing from the catalog

- Appears as VENTAS CSV header col D "Set Celeno (Bicolor)" and as a size column.
- It is a member of **Caja Saca Las Garras** in the CAJAS bottom section (I22:
  costo 12677, precio 65000) and of **Caja Despertar** (E24).
- The VENTAS CSV combo row cost (129388) matches the **bottom** section total
  (129388, incl. Set Celeno + empaques), NOT the top section the migration reads
  (CAJA 3 = 116673.15, no Set Celeno).
- **Conclusion**: the DB combo built from the top CAJAS section is incomplete vs.
  what was actually sold. Adding Set Celeno to the catalog is a catalog-data
  change (new PRODUCTOS_CATALOGO entry + BOM) and optionally to the combo.

### 2.3 Combo handling (CAJA SACA LAS GARRAS, S,S,S,XS)

- The CSV combo row carries **4 sizes, one per component** (Set Ocipete S, Set
  Aelo S, Set Celeno S, Blusa ML XS). The model allows ONE `variante_id` per
  `DetalleVenta` and `BomProducto` has NO `variante_id` column.
- The combo **price (295000) is NOT the sum** of components (360000) — it is a
  bundle price, so splitting into 4 detail lines cannot allocate price faithfully.
- **Recommendation**: combos do NOT get variants. The sale stays ONE detail row
  (combo, variante NULL). Explosion of a combo passes `variante_id=None` to
  children; `_lineas_insumo_efectivas(rows, None)` selects only NULL-variant base
  lines — correct as today. The 4 component sizes are **documented as lost**
  (current model cannot express per-member sizes; a BomProducto.variante_id
  schema change is out of scope). If the user wants them preserved, that is a
  separate change (multi-variant sales / component-level detail lines).
- `_variante_de_fila` takes the FIRST non-empty size column ("S") — for the combo
  row that resolves against the combo product which has no variants → NULL → OK.

### 2.4 CRITICAL: sized products sold WITHOUT size (F5 fails today)

- 2 of 21 sales rows lack a size for a sized product: `SET OCIPETE` (28/3) and
  `BLUSA ARPIA MANGA LARGA` (5/8).
- Once those products have variants, `explosion_materiales(db, id, None, n)`
  hits the root guard (`inventory.py:61-62`) → `DomainValidationError` 400 →
  `session_scope` rolls back the whole F5 phase (EXM-4).
- **Decision needed in spec**: omit + report (consistent with VTA-4 SCOPE OUT /
  EXM-2 "never invent") vs. default variant. Recommendation: **omit + report**
  (2 rows, 5 units). This keeps fidelity and avoids inventing data.

### 2.5 CRITICAL: idempotency of re-run after adding variants

- The natural key of `Detalle_Ventas` includes `variante_id`. The 21 existing
  rows were inserted with `variante_id NULL`.
- After F1 seeds variants, a re-run resolves the CSV size → new key → the existing
  NULL rows are NOT matched → the 21 sales get **re-inserted (duplicates)**.
- **Mitigation options** (for spec/design): (a) backfill UPDATE of existing
  detail rows' `variante_id` derived from the CSV before re-running sales; (b)
  make `_contar_existentes` treat NULL-variant DB rows as matching when the plan
  line resolves a variant; (c) delete + reinsert detail rows. Recommendation: (b)
  or (c) — keep the migration self-contained; document in `test_migrate_sales.py`.

### 2.6 Stock by size — OUT OF SCOPE

- The ERP has NO finished-goods stock: only `Insumo.stock_actual`; products are
  exploded into insumos. PRENDAS (INICIAL/VENTAS/FINAL, all VENTAS=0) is a
  baseline for a product-stock concept that does not exist.
- PRENDAS rows 30-35 (Blusa corta 36/38, Blusa larga) fall OUTSIDE the current
  SHEET_BOUNDS (9,29) — even reading it needs bound extension.
- **Recommendation**: this change seeds variants only. Product/variant stock is a
  separate change. `test_migrate_stock.py` (asserts PRENDAS "never read") stays
  green.

### 2.7 Naming resolution (PRENDAS → catalog)

PRENDAS names differ from catalog names; resolvable via the workbook note column
+ price:
- "Conjunto bicolor" → **Set Celeno** (note Celeno; 75000 = CAJAS Set Celeno precio)
- "Bustier encaje negro" → Set Ocipete (note Ocípete; 95000 = SET OCIPETE VENTA)
- "Corset encaje rojo pastel" → Set Aelo (note Aelo; 110000 = SET AELO VENTA)
- "Blusa maya estampada garra manga corta" → Blusa Manga Corta (80000 = BLUSAS right)
- "Blusa maya estampada garra manga larga" → Blusa Manga Larga (90000 = BLUSAS left)
- "tanga encaje negro / rojo pastel" → **no catalog product** (ghost right blocks
  of SET AELO/SET OCIPETE sheets, deliberately skipped by BLOQUES_BOM)

For this change the map is only needed to justify which products get variants;
PRENDAS itself stays unread (2.6).

### 2.8 Frontend

- `VentasForm.vue` already loads variants per product lazily and offers a select
  per line — works once variants exist.
- `VarianteForm.vue` + `VariantesTable.vue` already exist (admin CRUD) — XXS–XL
  can be created today.
- **Gap**: the variant select is optional; once a product HAS variants the
  backend 400 guard fires without a variant → the ventas form must require the
  variant when the product has variants (UX + validation). Optional: canonical
  ordered size list (XXS < XS < S < M < L < XL) for display ordering.

## 3. Impacted files

- `backend/migrate/catalog.py` — PRODUCTOS_CATALOGO entries gain `variantes`
  tuples; new Set Celeno product entry.
- `backend/migrate/sales.py` — missing-size policy (omit + report); idempotency
  handling for NULL→variant transition.
- `backend/migrate/validate.py` — N7 checks may need to account for the 2 omitted
  rows / variant resolution.
- `backend/tests/test_migrate_catalog.py` — `conteo_productos == len(PRODUCTOS_CATALOGO)`
  breaks if Set Celeno is added (count changes); also may assert variant counts.
- `backend/tests/test_migrate_sales.py` — idempotency / variant resolution tests.
- `frontend/src/components/ventas/VentasForm.vue` — require variant when product
  has variants.
- Optional: `backend/app/models/productos.py` (BomProducto.variante_id — OUT of
  scope), `backend/migrate/stock.py` (OUT of scope).

## 4. Risks

1. **F5 hard-fail** on 2 size-less sale rows once products have variants (2.4).
2. **Duplicate sales on re-run** (NULL → variant key transition) (2.5).
3. **test_migrate_catalog.py** product-count assertions break if Set Celeno added.
4. **Combo component sizes lost** — explicit limitation; separate change needed
   for per-member sizes.
5. Workbook internal inconsistency (top vs bottom CAJAS totals; Set Celeno price
   65000 vs 75000) — decisions must be documented, not "fixed" silently.

## 5. Recommended scope (for propose)

- Seed variants XXS..XL for: Set Aelo, Set Ocipete, Blusa Manga Larga, Blusa
  Manga Corta (variant name = letter; precio_venta NULL — sizes share product price).
- Add **Set Celeno** product (decide price: 65000 vs 75000; BOM recipe needs a
  sheet — does not exist → design decision) and optionally add it to the Caja
  Saca Las Garras combo (bottom section truth) — or defer combo change.
- Combos: no variants; single detail; document component-size loss.
- F5: omit+report size-less rows of sized products; idempotency fix.
- Stock-by-size: out of scope.
- Frontend: require variant on sized products in VentasForm.