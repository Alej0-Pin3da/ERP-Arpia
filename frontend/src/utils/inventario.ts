/**
 * Inventario module mappers (PR9, spec MOD-4).
 *
 * Pure functions over the inventario module:
 *  - `buildInsumosById` + `insumoNombre`: CompraInsumoRead rows carry only
 *    insumo_id — the display name is joined client-side against GET /insumos
 *    with an `Insumo #{id}` fallback when the insumo no longer exists.
 *  - `compraCostoTotal` + `buildCompraRows`: the backend CompraInsumoRead has
 *    NO costo_total field (verified against the prod OpenAPI and backend
 *    routes/compras_insumos.py), so the total is computed client-side as
 *    cantidad_comprada x precio_unitario_compra over the Decimal-as-string
 *    values; unparseable values degrade to null. Rows render newest first
 *    (the backend lists id ASC — same ledger ordering as finanzas/ventas).
 *  - `buildCompraPayload`: compra form -> CompraInsumoCreate body. The schema
 *    field names are `cantidad_comprada` / `precio_unitario_compra`.
 *  - `buildInsumoPayload` / `buildInsumoUpdatePayload`: admin insumo master
 *    form -> InsumoCreate / InsumoUpdate bodies (POST requires all fields;
 *    PUT sends the full editable set — the backend update schema marks every
 *    field optional but accepts the full body).
 *  - `buildComprasListParams`: the optional GET /compras-insumos?insumo_id
 *    filter, omitted from the query when unset.
 */
import type { components } from '@/types/api.d'
import { parseDecimal } from './format'

type InsumoRead = components['schemas']['InsumoRead']
type CompraInsumoRead = components['schemas']['CompraInsumoRead']
export type CompraInsumoCreate = components['schemas']['CompraInsumoCreate']
export type InsumoCreate = components['schemas']['InsumoCreate']
export type InsumoUpdate = components['schemas']['InsumoUpdate']

/** Map of insumo id -> InsumoRead for O(1) client-side joins. */
export function buildInsumosById(insumos: InsumoRead[]): Map<number, InsumoRead> {
  return new Map(insumos.map((i) => [i.id, i]))
}

/**
 * Insumo display name for a compra join. Degrades gracefully when the insumo
 * no longer exists: `Insumo #{id}` (design "Missing joins MUST degrade").
 */
export function insumoNombre(insumosById: Map<number, InsumoRead>, insumoId: number): string {
  return insumosById.get(insumoId)?.nombre ?? `Insumo #${insumoId}`
}

/**
 * MOD-4: compra line total = cantidad_comprada x precio_unitario_compra over
 * the Decimal-as-string fields (the backend CompraInsumoRead carries no
 * costo_total). Unparseable values degrade to null — the table then renders
 * "$0,00" via formatMoney.
 */
export function compraCostoTotal(cantidad: string, precioUnitario: string): number | null {
  const qty = parseDecimal(cantidad)
  const price = parseDecimal(precioUnitario)
  if (qty === null || price === null) return null
  return qty * price
}

/** A compra list row with its joined insumo label and computed total (MOD-4). */
export interface CompraRow {
  id: number
  /** Raw ISO datetime (formatted at render time). */
  fecha: string
  /** Insumo name, or `Insumo #{id}` when the insumo is gone. */
  insumo: string
  /** Raw Decimal-as-string quantity (formatted at render time). */
  cantidad: string
  /** Raw Decimal-as-string unit price (formatted at render time). */
  precio_unitario: string
  /** cantidad x price; null when either value is unparseable. */
  costo_total: number | null
}

/**
 * MOD-4: join compras with insumo names, compute the line total, and render
 * newest first (the backend lists id ASC — a purchase log reads better
 * top-down).
 */
export function buildCompraRows(
  compras: CompraInsumoRead[],
  insumos: InsumoRead[],
): CompraRow[] {
  const insumosById = buildInsumosById(insumos)

  return [...compras]
    .sort((a, b) => b.id - a.id)
    .map((c) => ({
      id: c.id,
      fecha: c.fecha_compra,
      insumo: insumoNombre(insumosById, c.insumo_id),
      cantidad: c.cantidad_comprada,
      precio_unitario: c.precio_unitario_compra,
      costo_total: compraCostoTotal(c.cantidad_comprada, c.precio_unitario_compra),
    }))
}

/** Compra register form model (PR2: modo TOTAL|UNIT + factura, REQ-CI-001 + REQ-WAC-003). */
export interface CompraPayloadInput {
  insumo_id: number | null
  /** Quantity > 0 (el-input-number value). */
  cantidad: number | null
  /** Unit price >=0 when modo UNIT (InputNumber value). */
  precio_unitario: number | null
  /** Total cost >0 when modo TOTAL (InputNumber value). */
  costo_total?: number | null
  /** TOTAL | UNIT — default UNIT for backward compat. */
  modo?: 'TOTAL' | 'UNIT'
  /** Optional invoice ref ≤100 chars (REQ-CI-001). */
  factura?: string | null
  /** Optional proveedor id (nullable, no FK constraint in this slice). */
  proveedor_id?: number | null
}

/**
 * MOD-4+PR2: compra form -> CompraInsumoCreate body.
 * TOTAL branch derives `precio_unitario_compra = costo_total / qty` (display parity
 * only; backend re-derives authoritatively in Decimal). The schema names are
 * `cantidad_comprada` / `precio_unitario_compra` | `costo_total`.
 */
export function buildCompraPayload(form: CompraPayloadInput): CompraInsumoCreate {
  const modo = form.modo ?? 'UNIT'
  const base: Record<string, unknown> = {
    insumo_id: form.insumo_id as number,
    cantidad_comprada: form.cantidad as number,
  }
  // Only emit modo when caller set it explicitly — preserves MOD-4 tests while
  // supporting TOTAL branch; backend defaults to UNIT when absent.
  if (form.modo !== undefined) base.modo = modo
  if (form.factura?.trim()) base.factura = form.factura.trim()
  if (form.proveedor_id != null) base.proveedor_id = form.proveedor_id
  if (modo === 'TOTAL') {
    base.costo_total = form.costo_total as number
  } else {
    base.precio_unitario_compra = form.precio_unitario as number
  }
  return base as unknown as CompraInsumoCreate
}

/** CSV header required by REQ-CI-003 SCN-CI-005 (exact order, no spaces). */
export const CSV_HEADER = 'fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura'

/** Row shape for CSV export — mirrors HistorialDrawer columns. */
export interface HistorialCsvRow {
  fecha: string
  cantidad: string | number
  prevStock: string | number
  newStock: string | number
  prevCost: string | number
  newCost: string | number
  total: string | number
  factura: string | null | undefined
}

function csvEscape(value: string): string {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`
  }
  return value
}

/**
 * REQ-CI-003: build CSV string from historial rows (header + rows).
 * Values are stringified and CSV-escaped; empty factura renders as "".
 */
export function buildHistorialCsv(rows: HistorialCsvRow[]): string {
  const lines = [CSV_HEADER]
  for (const r of rows) {
    const cols = [
      csvEscape(String(r.fecha ?? '')),
      csvEscape(String(r.cantidad ?? '')),
      csvEscape(String(r.prevStock ?? '')),
      csvEscape(String(r.newStock ?? '')),
      csvEscape(String(r.prevCost ?? '')),
      csvEscape(String(r.newCost ?? '')),
      csvEscape(String(r.total ?? '')),
      csvEscape(String(r.factura ?? '')),
    ]
    lines.push(cols.join(','))
  }
  return lines.join('\n')
}

/** The admin insumo master form model (create + edit). */
export interface InsumoPayloadInput {
  nombre: string
  categoria_id: number | null
  unidad_medida: string
  stock_actual: number | null
  stock_minimo: number | null
  costo_promedio_actual: number | null
}

/** MOD-4: admin create form -> InsumoCreate body (POST /insumos). */
export function buildInsumoPayload(form: InsumoPayloadInput): InsumoCreate {
  return {
    categoria_id: form.categoria_id as number,
    nombre: form.nombre.trim(),
    unidad_medida: form.unidad_medida.trim(),
    stock_actual: form.stock_actual as number,
    stock_minimo: form.stock_minimo as number,
    costo_promedio_actual: form.costo_promedio_actual as number,
  }
}

/** MOD-4: admin edit form -> InsumoUpdate body (PUT /insumos, full set). */
export function buildInsumoUpdatePayload(form: InsumoPayloadInput): InsumoUpdate {
  return buildInsumoPayload(form)
}

/** The compras list filter state (optional GET /compras-insumos?insumo_id). */
export interface ComprasFilter {
  insumo_id: number | null
}

/** MOD-4: filter state -> query params; the insumo filter is omitted when unset. */
export function buildComprasListParams(filter: ComprasFilter): { insumo_id?: number } {
  return filter.insumo_id === null ? {} : { insumo_id: filter.insumo_id }
}
