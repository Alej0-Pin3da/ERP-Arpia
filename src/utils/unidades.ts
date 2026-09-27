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

/** Una línea con >50 m normalizados es casi seguro un error de unidad. */
export const UMBRAL_LINEA_SOSPECHOSA_M = 50

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

/** Mínimo estructural de una línea de material (compatible con InsumoCotizacionLinea). */
export interface LineaMaterial {
  cantidad: number
  unidad_medida?: string | null
  precio_unitario?: number | null
  desperdicio_pct?: number | null
  esTela?: boolean
}

/** Redondeo financiero HALF_UP a centavos (positivos): igual que el backend. */
export function redondearCentavos(v: number): number {
  return Math.round(Number(v) * 100) / 100
}

/** Subtotal de una línea: cantidad × (1 + desp/100) × precio, en unidad original. */
export function subtotalLineaMaterial(l: LineaMaterial): number {
  return (
    Number(l.cantidad ?? 0) *
    (1 + Number(l.desperdicio_pct ?? 0) / 100) *
    Number(l.precio_unitario ?? 0)
  )
}

/** Σ líneas con redondeo final a centavos — misma fórmula que _calcular. */
export function subtotalMateriales(lineas: LineaMaterial[]): number {
  return redondearCentavos(lineas.reduce((acc, l) => acc + subtotalLineaMaterial(l), 0))
}

/** Metros REALES de tela/forro para la heurística de hilos. */
export function metrosTelaDeLineas(lineas: LineaMaterial[]): number {
  return lineas
    .filter((l) => l.esTela !== false)
    .reduce((acc, l) => acc + (normalizarAMetros(Number(l.cantidad ?? 0), l.unidad_medida ?? '') ?? 0), 0)
}

/** ¿La línea supera lo razonable para una sola prenda? (posible cm cargados como m). */
export function esLineaSospechosa(l: LineaMaterial): boolean {
  return (normalizarAMetros(Number(l.cantidad ?? 0), l.unidad_medida ?? '') ?? 0) > UMBRAL_LINEA_SOSPECHOSA_M
}
