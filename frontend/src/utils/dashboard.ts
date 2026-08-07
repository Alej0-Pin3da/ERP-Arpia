/**
 * Dashboard analytics mappers (task 1.9, spec DASH-1..3).
 *
 * Pure functions that transform the raw analytics payloads into what the
 * dashboard renders:
 *  - DASH-1: `ventas-mensuales` returns ONLY months with sales — the chart
 *    spans first→last month with zeroed gaps; the KPI source is the last row.
 *  - DASH-2: low-stock rows carry Decimal strings — severity is derived from
 *    how far below the minimum the stock is.
 *  - DASH-3: `margen-por-producto` returns IDs only — names and variant
 *    labels are joined client-side (GET /productos + /variantes) with
 *    graceful fallbacks when a product/variant no longer exists.
 */
import type {
  MargenProductoRead,
  ProductoRead,
  VentasMensualesRead,
  VarianteProductoRead,
} from '@/types/api.d'
import { parseDecimal } from './format'

/** One chart bar: a calendar month, zero-filled when the API has no row. */
export interface FilledMonthRow {
  /** 'YYYY-MM' month key (sortable). */
  mes: string
  /** es-CO short label, e.g. 'ene 2026'. */
  label: string
  /** Parsed Decimal total for the month (0 when the API had no row). */
  total: number
  /** Units sold that month. */
  cantidad: number
}

/** KPI source: the most recent month present in the analytics response. */
export interface MonthSummary {
  /** 'YYYY-MM' month key. */
  mes: string
  /** Raw Decimal-as-string total (formatted at render time). */
  total: string
  /** Units sold that month. */
  cantidad: number
}

/** A margen row joined with its product/variant labels (DASH-3). */
export interface MargenRow {
  producto_id: number
  /** Product name, or `Producto #{id}` when the product is gone. */
  nombre: string
  /** Variant label, '(base)' for the base product, or `Variante #{id}`. */
  variante: string
  /** Raw Decimal-as-string margins (formatted at render time). */
  margen_total: string
  margen_promedio: string
}

/** Stock level relative to its minimum — drives the low-stock highlight. */
export type StockSeverity = 'ok' | 'warning' | 'danger'

const MONTH_RE = /^(\d{4})-(\d{2})/

// es-CO short month names (compact chart axis labels — Intl renders
// 'ene de 2026', which is too wide for an axis; this table is deterministic).
const SHORT_MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/** Extract 'YYYY-MM' from an ISO date ('2026-01-01' -> '2026-01'); null when unparseable. */
function monthKey(mes: string): string | null {
  const match = MONTH_RE.exec(mes)
  return match ? `${match[1]}-${match[2]}` : null
}

/** Months since epoch — makes 'YYYY-MM' keys numerically sortable. */
function monthNumber(key: string): number {
  const [year, month] = key.split('-').map(Number)
  return year * 12 + (month - 1)
}

/** es-CO short month label for a 'YYYY-MM' key ('2026-01' -> 'ene 2026'). */
function monthLabel(key: string): string {
  const [year, month] = key.split('-').map(Number)
  return `${SHORT_MONTHS[month - 1]} ${year}`
}

/**
 * DASH-1: fill the gap between the first and last month with zero rows so the
 * chart axis is continuous. Input is sorted ascending; rows with an
 * unparseable `mes` are ignored. Empty input stays empty.
 */
export function fillMissingMonths(rows: VentasMensualesRead[]): FilledMonthRow[] {
  const keyed = rows
    .map((row) => ({ row, key: monthKey(row.mes) }))
    .filter((entry): entry is { row: VentasMensualesRead; key: string } => entry.key !== null)
    .sort((a, b) => monthNumber(a.key) - monthNumber(b.key))

  if (keyed.length === 0) return []

  const start = monthNumber(keyed[0].key)
  const end = monthNumber(keyed[keyed.length - 1].key)
  const byKey = new Map(keyed.map((entry) => [entry.key, entry.row]))

  const filled: FilledMonthRow[] = []
  for (let n = start; n <= end; n++) {
    const key = `${Math.floor(n / 12)}-${String((n % 12) + 1).padStart(2, '0')}`
    const row = byKey.get(key)
    filled.push({
      mes: key,
      label: monthLabel(key),
      total: row ? (parseDecimal(row.total) ?? 0) : 0,
      cantidad: row ? row.cantidad : 0,
    })
  }
  return filled
}

/**
 * DASH-1: the most recent month in the response (max month, independent of
 * input order) — the KPI cards read from this row. null when there is no data.
 */
export function lastMonthSummary(rows: VentasMensualesRead[]): MonthSummary | null {
  const keyed = rows
    .map((row) => ({ row, key: monthKey(row.mes) }))
    .filter((entry): entry is { row: VentasMensualesRead; key: string } => entry.key !== null)

  if (keyed.length === 0) return null

  const latest = keyed.reduce((a, b) => (monthNumber(b.key) > monthNumber(a.key) ? b : a))
  return { mes: latest.key, total: latest.row.total, cantidad: latest.row.cantidad }
}

/**
 * DASH-3: join margen rows (IDs only) with product/variant labels, degrading
 * gracefully: missing product -> `Producto #{id}`, null variante -> '(base)',
 * missing variante -> `Variante #{id}`. Preserves the margen response order.
 */
export function buildMargenRows(
  margenes: MargenProductoRead[],
  productos: ProductoRead[],
  variantes: VarianteProductoRead[],
): MargenRow[] {
  const productosById = new Map(productos.map((p) => [p.id, p]))
  const variantesById = new Map(variantes.map((v) => [v.id, v]))

  return margenes.map((margen) => {
    const producto = productosById.get(margen.producto_id)
    const variante = margen.variante_id === null ? null : variantesById.get(margen.variante_id)
    return {
      producto_id: margen.producto_id,
      nombre: producto ? producto.nombre : `Producto #${margen.producto_id}`,
      variante:
        margen.variante_id === null
          ? '(base)'
          : variante
            ? variante.nombre_variante
            : `Variante #${margen.variante_id}`,
      margen_total: margen.margen_total,
      margen_promedio: margen.margen_promedio,
    }
  })
}

/**
 * DASH-2: how far below the minimum a stock level is — below half the minimum
 * (or zero) is danger, between half and the minimum is warning. Unparseable
 * values never alarm ('ok').
 */
export function stockSeverity(
  stockActual: string | number | null | undefined,
  stockMinimo: string | number | null | undefined,
): StockSeverity {
  const actual = parseDecimal(stockActual)
  const minimo = parseDecimal(stockMinimo)
  if (actual === null || minimo === null) return 'ok'
  if (actual >= minimo) return 'ok'
  if (actual < minimo * 0.5) return 'danger'
  return 'warning'
}
