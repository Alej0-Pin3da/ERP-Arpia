/**
 * Prorrateo de costos reales de un lote a valores unitarios de producto.
 *
 * /produccion registra totales reales por pedido (mano de obra + energía +
 * minutos, derivados de los TiempoFase). /productos muestra valores unitarios
 * manuales (Producto.mano_obra / cif_energia / tiempo_confeccion_min).
 * Esta función convierte totales del lote → por-unidad para el PUT explícito
 * "Aplicar costos al producto" (acción del usuario, nunca automática).
 */

export interface TotalesLote {
  manoObra: number | string | null | undefined
  energia: number | string | null | undefined
  minutos: number | string | null | undefined
}

export interface CostosUnitarios {
  /** $/ud, 2 decimales — va a Producto.mano_obra. */
  mano_obra: number
  /** $/ud, 2 decimales — va a Producto.cif_energia. */
  cif_energia: number
  /** min/ud, entero — va a Producto.tiempo_confeccion_min. */
  tiempo_confeccion_min: number
}

function num(v: number | string | null | undefined): number {
  const x = Number(v)
  return Number.isFinite(x) ? x : 0
}

function round2(v: number): number {
  return Math.round(v * 100) / 100
}

/**
 * Totales del lote / N unidades → costos por unidad.
 * Devuelve null cuando N no es un entero positivo (0, negativo, NaN,
 * null/undefined): el llamador deshabilita el botón en ese caso.
 */
export function calcularCostosUnitarios(
  totales: TotalesLote,
  unidades: number | string | null | undefined,
): CostosUnitarios | null {
  const n = Number(unidades)
  if (!Number.isFinite(n) || n <= 0) return null
  return {
    mano_obra: round2(num(totales.manoObra) / n),
    cif_energia: round2(num(totales.energia) / n),
    tiempo_confeccion_min: Math.round(num(totales.minutos) / n),
  }
}
