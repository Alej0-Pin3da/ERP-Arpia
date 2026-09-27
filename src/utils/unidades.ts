/**
 * Unit normalization for textile lengths (V6 thread-bug fix).
 *
 * The BOM stores quantities in the master insumo's own unit (cm, m, mm,
 * un, ...). Money math always stays in original units; only the thread
 * heuristic needs REAL meters, so every length funnels through
 * {@link normalizarAMetros}. Non-length units (un, doc, kg, ...) return
 * null: they never count as fabric meters.
 */

const CM = new Set(['cm', 'centimetro', 'centimetros', 'centímetro', 'centímetros'])
const MM = new Set(['mm', 'milimetro', 'milimetros', 'milímetro', 'milímetros'])
const M = new Set(['m', 'mt', 'mts', 'metro', 'metros'])
const YARDAS = new Set(['yarda', 'yardas', 'yd', 'yrd'])

export const METROS_POR_YARDA = 0.9144

export function normalizarAMetros(cantidad: number, unidad: string | null | undefined): number | null {
  const n = Number(cantidad)
  if (!Number.isFinite(n)) return null
  const u = (unidad ?? '').trim().toLowerCase()
  if (CM.has(u)) return n / 100
  if (MM.has(u)) return n / 1000
  if (M.has(u)) return n
  if (YARDAS.has(u)) return n * METROS_POR_YARDA
  return null
}
