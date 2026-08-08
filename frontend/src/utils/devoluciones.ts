/**
 * Devoluciones module mappers (task 2.3, spec MOD-2).
 *
 * Pure functions over the devoluciones module:
 *  - `buildDevolucionRows`: DevolucionRead.items carry only product IDs —
 *    names are joined client-side (GET /productos?limit=1000) with the shared
 *    `Producto #{id}` fallback; null motivo degrades to '—'. Unlike /ventas
 *    the list IS paginated server-side (limit<=500, default 100), so no
 *    client slice is needed.
 *  - Form model -> payload: `buildDevolucionPayload` produces the
 *    DevolucionCreate POST body. tipo 'total' omits items entirely (spec:
 *    total without items -> 201); tipo 'parcial' requires at least one
 *    complete line (server 422 otherwise — the client blocks it too).
 *    `precio_unitario` stays in the payload because the schema requires it,
 *    but it is NEVER trusted: the backend prices every return from the
 *    sale-time `precio_unitario_aplicado` snapshot (backend
 *    app/services/devoluciones.py) and ignores the client value.
 */
import type { components } from '@/types/api.d'
import { buildProductosById, productoNombre } from './lookup'

type DevolucionRead = components['schemas']['DevolucionRead']
type ProductoRead = components['schemas']['ProductoRead']
export type DevolucionCreate = components['schemas']['DevolucionCreate']

export type DevolucionTipo = 'total' | 'parcial'

/** Selectable return types (DevolucionCreate.tipo enum). */
export const TIPO_DEVOLUCION: readonly DevolucionTipo[] = ['total', 'parcial']

/** List filter model bound by the view (GET /devoluciones query). */
export interface DevolucionFilters {
  venta_id: number | null
  /** ISO dates (YYYY-MM-DD) from el-date-picker; '' = unset. */
  fecha_desde: string
  fecha_hasta: string
}

/**
 * MOD-2: map the filter model to the GET /devoluciones query, omitting unset
 * filters so the server keeps its defaults (limit<=500, offset 0).
 */
export function buildDevolucionListParams(filters: DevolucionFilters): {
  venta_id?: number
  fecha_desde?: string
  fecha_hasta?: string
} {
  return {
    ...(filters.venta_id !== null ? { venta_id: filters.venta_id } : {}),
    ...(filters.fecha_desde !== '' ? { fecha_desde: filters.fecha_desde } : {}),
    ...(filters.fecha_hasta !== '' ? { fecha_hasta: filters.fecha_hasta } : {}),
  }
}

const TIPO_LABELS: Record<string, string> = {
  total: 'Total',
  parcial: 'Parcial',
}

/** es-CO label for a return type; unknown values pass through. */
export function tipoLabel(tipo: string): string {
  return TIPO_LABELS[tipo] ?? tipo
}

/** el-tag type per tipo: total danger (cancels the sale), parcial warning. */
export function tipoTagType(tipo: string): 'success' | 'warning' | 'danger' | 'info' {
  if (tipo === 'total') return 'danger'
  if (tipo === 'parcial') return 'warning'
  return 'info'
}

/** A list-row item joined with its product label (MOD-2). */
export interface DevolucionItemRow {
  producto_id: number
  variante_id: number | null
  /** Product name, or `Producto #{id}` when the product is gone. */
  nombre: string
  /** Raw Decimal-as-string snapshot values (formatted at render time). */
  cantidad: string
  subtotal: string
}

/** A list-row devolución with joined item labels (MOD-2). */
export interface DevolucionRow {
  id: number
  venta_id: number
  /** Raw ISO datetime (formatted at render time). */
  fecha: string
  tipo: string
  /** Motivo, or an em dash when the return has none. */
  motivo: string
  /** Raw Decimal-as-string refund (formatted at render time). */
  monto_reembolsado: string
  items: DevolucionItemRow[]
}

/**
 * MOD-2: join devoluciones with product names, degrading gracefully:
 * missing product -> `Producto #{id}`, null motivo -> '—'. Preserves the
 * input order (backend already orders by id).
 */
export function buildDevolucionRows(
  devoluciones: DevolucionRead[],
  productos: ProductoRead[],
): DevolucionRow[] {
  const productosById = buildProductosById(productos)

  return devoluciones.map((d) => ({
    id: d.id,
    venta_id: d.venta_id,
    fecha: d.fecha,
    tipo: d.tipo,
    motivo: d.motivo ?? '—',
    monto_reembolsado: d.monto_reembolsado,
    items: d.items.map((item) => ({
      producto_id: item.producto_id,
      variante_id: item.variante_id,
      nombre: productoNombre(productosById, item.producto_id),
      cantidad: item.cantidad,
      subtotal: item.subtotal,
    })),
  }))
}

/** One dynamic line item of the create form. */
export interface DevolucionFormItem {
  producto_id: number | null
  variante_id: number | null
  cantidad: number
  /**
   * Required by the schema but ignored server-side (snapshot pricing) — the
   * backend always prices from the sale-time price. Kept for the payload.
   */
  precio_unitario: number
}

/** The create form model (maps to DevolucionCreate via buildDevolucionPayload). */
export interface DevolucionPayloadInput {
  /** Required — the form blocks submission until a venta is chosen. */
  venta_id: number
  tipo: DevolucionTipo
  motivo: string
  items: DevolucionFormItem[]
}

/** A fresh empty line item for the create form (each call a new object). */
export function createDevolucionItemRow(): DevolucionFormItem {
  return { producto_id: null, variante_id: null, cantidad: 1, precio_unitario: 0 }
}

/** MOD-2: parcial requires at least one complete line (product + cantidad > 0). */
export function hasValidDevolucionItems(items: DevolucionFormItem[]): boolean {
  return items.some((i) => i.producto_id !== null && i.cantidad > 0)
}

/**
 * MOD-2: map the form model to the DevolucionCreate POST body.
 *  - tipo 'total': items are OMITTED (the backend ignores them anyway).
 *  - tipo 'parcial': items REQUIRED; incomplete rows are dropped; `variante_id`
 *    is omitted (not null) when absent; `precio_unitario` always included
 *    (schema-required, server-ignored snapshot).
 *  - motivo is included only when non-empty (trimmed).
 */
export function buildDevolucionPayload(form: DevolucionPayloadInput): DevolucionCreate {
  const payload: DevolucionCreate = {
    venta_id: form.venta_id,
    tipo: form.tipo,
  }

  const motivo = form.motivo.trim()
  if (motivo !== '') {
    payload.motivo = motivo
  }

  if (form.tipo === 'parcial') {
    payload.items = form.items
      .filter((i) => i.producto_id !== null && i.cantidad > 0)
      .map((i) => ({
        producto_id: i.producto_id as number,
        ...(i.variante_id !== null ? { variante_id: i.variante_id } : {}),
        cantidad: i.cantidad,
        precio_unitario: i.precio_unitario,
      }))
  }

  return payload
}
