/**
 * Column-header filter helpers (native el-table filters, FE header filters).
 *
 * el-table's `filter-change` emits `Record<columnKey, unknown[]>` where each
 * array holds the SELECTED filter values (the raw `value` of the options —
 * verified against Element Plus 2.9: `updateFilters` maps `columnKey ->
 * values`), and an EMPTY array means the column filter was cleared. These
 * helpers normalize one column's array to a single value so the views can map
 * it onto their existing server-side filter refs.
 */

/** A value a column-header filter can carry (enum string, numeric id, bool). */
export type ColumnFilterValue = string | number | boolean

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
