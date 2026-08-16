/**
 * Column-header filter helpers (native el-table filters, FE header filters).
 *
 * el-table's `filter-change` emits `Record<columnKey, unknown[]>` where each
 * array holds the SELECTED filter values (the raw `value` of the options —
 * verified against Element Plus 2.9: `updateFilters` maps `columnKey ->
 * values`), and an EMPTY array means the column filter was cleared. These
 * helpers normalize one column's array to a single value so the views can map
 * it onto their existing server-side filter refs.
 *
 * PrimeVue DataTable (lazy mode) emits a different shape: `@filter` carries
 * `Record<columnKey, { value, matchMode } | { value, matchMode }[]>`. The
 * `parsePrimeVueFilters`/`parsePrimeVueSort` adapters below normalize those
 * payloads back to the shapes the rest of the app already consumes, so the
 * `parseColumnFilter` semantics (first-selected-value, `{text,value}` unwrap,
 * empty/cleared → null) survive untouched for all existing callers.
 */

/** A value a column-header filter can carry (enum string, numeric id, bool). */
export type ColumnFilterValue = string | number | boolean

/** A single constraint emitted by a PrimeVue DataTable `@filter` payload. */
export interface PrimeVueFilterConstraint {
  value: unknown
  matchMode?: string
}

/**
 * Normalize a PrimeVue DataTable `@filter` payload to the el-table column
 * array shape: `Record<col, unknown[]>` of raw constraint values. Each column
 * keeps its values (single constraint or array) verbatim — a `{ value: null }`
 * constraint becomes `[null]` and a `{ text, value }` option value stays
 * wrapped so the existing `parseColumnFilter` unwrap/empty semantics apply
 * unchanged downstream.
 */
export function parsePrimeVueFilters(
  filters: Record<string, PrimeVueFilterConstraint | PrimeVueFilterConstraint[]>,
): Record<string, unknown[]> {
  const normalized: Record<string, unknown[]> = {}
  for (const [field, constraint] of Object.entries(filters)) {
    normalized[field] = Array.isArray(constraint)
      ? constraint.map((c) => c.value)
      : [constraint.value]
  }
  return normalized
}

/**
 * Normalize a PrimeVue DataTable `@sort` payload to the view sort shape:
 * `{ prop, order }` where order is 'asc' | 'desc' | null. PrimeVue emits
 * `sortOrder` 1 (asc), -1 (desc), 0/null (no sort).
 */
export function parsePrimeVueSort(s: {
  sortField?: string
  sortOrder?: number
}): { prop: string; order: 'asc' | 'desc' | null } {
  const order = s.sortOrder === 1 ? 'asc' : s.sortOrder === -1 ? 'desc' : null
  return { prop: s.sortField ?? '', order }
}

/**
 * Normalize the `filter-change` payload for one column to a single value:
 * take the first selected value (raw option `value`), or null when the filter
 * is empty/cleared. Older payloads that pass the full `{text, value}` option
 * objects are tolerated too by unwrapping a leading `.value`.
 */
export function parseColumnFilter(values: unknown): ColumnFilterValue | null {
  if (!Array.isArray(values) || values.length === 0) return null
  const first = values[0] as unknown
  if (typeof first === 'object' && first !== null && 'value' in first) {
    return parseColumnFilter([(first as { value: unknown }).value])
  }
  return typeof first === 'string' || typeof first === 'number' || typeof first === 'boolean'
    ? first
    : null
}
