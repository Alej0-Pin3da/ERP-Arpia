/**
 * Central es-CO formatters (spec SHELL-2).
 *
 * The backend serializes every Decimal as a JSON string ("12345.67"), so all
 * money/quantity display MUST go through Intl.NumberFormat("es-CO") — one
 * parser, one formatter, no per-component drift.
 */

// NumberFormat WITHOUT currency symbol: es-CO grouping (.) + comma decimal.
// The "$" prefix is added manually — `currency: 'COP'` renders "COP 1.234,56"
// and `narrowSymbol` inserts a non-breaking space. Design: "$12.345,68".
const moneyFormatter = new Intl.NumberFormat('es-CO', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const dateFormatter = new Intl.DateTimeFormat('es-CO', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  timeZone: 'UTC',
})

/**
 * Normalize a Decimal-as-string (or comma-separated input) to a plain number.
 * Returns null when the input is not numeric.
 */
export function parseDecimal(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null
  if (typeof value === 'number') return Number.isFinite(value) ? value : null

  const trimmed = value.trim()
  if (trimmed === '') return null

  // Disambiguate the separator:
  //  - "1.234,56"  (es-CO client input) -> decimal = ","
  //  - "1234.5678" (API Decimal-as-string) -> no comma, dot IS the decimal
  let normalized = trimmed
  if (trimmed.includes(',') && trimmed.includes('.')) {
    // Last separator wins as the decimal point; the other is the thousands sep.
    normalized = trimmed.replace(/\./g, '').replace(',', '.')
  } else if (trimmed.includes(',')) {
    normalized = trimmed.replace(/,/g, '.')
  }

  const parsed = Number.parseFloat(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

/**
 * Format a money value as es-CO ("$12.345,68"). null/undefined/'' -> "$0,00".
 */
export function formatMoney(value: string | number | null | undefined): string {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? moneyWithSign(value) : '$0,00'
  }
  if (value === null || value === undefined || value.trim() === '') {
    return '$0,00'
  }
  const parsed = parseDecimal(value)
  return parsed === null ? '$0,00' : moneyWithSign(parsed)
}

/** "$1.234,50" / "-$250,50" — the sign goes before the currency symbol. */
function moneyWithSign(value: number): string {
  const formatted = moneyFormatter.format(Math.abs(value))
  return value < 0 ? `-$${formatted}` : `$${formatted}`
}

// Quantity formatter: es-CO grouping, 0-2 decimals, NO currency symbol
// (stocks, counts). Money is formatMoney's job; this keeps the two apart.
const qtyFormatter = new Intl.NumberFormat('es-CO', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

/**
 * Format a quantity (stock, counts) as es-CO ("1.234,5"). null/undefined/
 * empty/non-numeric -> "0". Never renders a currency symbol.
 */
export function formatQty(value: string | number | null | undefined): string {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? qtyFormatter.format(value) : '0'
  }
  if (value === null || value === undefined || value.trim() === '') {
    return '0'
  }
  const parsed = parseDecimal(value)
  return parsed === null ? '0' : qtyFormatter.format(parsed)
}

/**
 * Format an ISO date ("2026-08-07" or full datetime) as es-CO dd/mm/yyyy.
 * null/undefined/invalid -> null.
 */
export function formatDate(value: string | null | undefined): string | null {
  if (value === null || value === undefined || value === '') return null

  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
  if (!match) return null

  const [, year, month, day] = match
  const date = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day)))
  if (Number.isNaN(date.getTime())) return null
  return dateFormatter.format(date)
}

/** Alias for formatDate — timestamps render as es-CO date (no time shown). */
export function formatDateTime(value: string | null | undefined): string | null {
  return formatDate(value)
}
