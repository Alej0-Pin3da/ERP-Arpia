/**
 * Ventas module mappers (tasks 2.1+2.2, spec MOD-1).
 *
 * Pure functions over the ventas module:
 *  - `sliceVentas`: GET /ventas is UNBOUNDED server-side (no pagination
 *    params — verified against the prod OpenAPI + backend route), so the
 *    client slices to the most recent N and pagination stays out of scope
 *    this phase (design "Ventas list: paginate client-side").
 *  - `buildVentaRows`: VentaRead.detalles carry only product/variant IDs —
 *    names are joined client-side (GET /productos?limit=1000 + variantes +
 *    /clientes) with graceful fallbacks, mirroring buildMargenRows.
 *  - Form model -> payload: `buildVentaPayload` produces the VentaCreate POST
 *    body; `computeTotalPreview` mirrors the server total
 *    (sum(cantidad*precio) * (1 - descuento/100), backend services/inventory).
 */
import type { components } from '@/types/api.d'
import { parseDecimal } from './format'

type VentaRead = components['schemas']['VentaRead']
type DetalleVentaRead = components['schemas']['DetalleVentaRead']
type ProductoRead = components['schemas']['ProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']
type ClienteRead = components['schemas']['ClienteRead']
export type VentaCreate = components['schemas']['VentaCreate']

/** Client-side cap for the unbounded GET /ventas list (most recent N). */
export const VENTAS_LIST_LIMIT = 100

export type CanalVenta = 'web' | 'whatsapp' | 'instagram' | 'feria'

/** Selectable sales channels (VentaCreate.canal_venta enum). */
export const CANAL_VENTAS: readonly CanalVenta[] = ['web', 'whatsapp', 'instagram', 'feria']

const CANAL_LABELS: Record<string, string> = {
  web: 'Web',
  whatsapp: 'WhatsApp',
  instagram: 'Instagram',
  feria: 'Feria',
}

const ESTADO_LABELS: Record<string, string> = {
  completada: 'Completada',
  anulada: 'Anulada',
}

/** es-CO label for a sales channel; unknown values pass through. */
export function canalLabel(canal: string): string {
  return CANAL_LABELS[canal] ?? canal
}

/** es-CO label for a venta estado; unknown values pass through. */
export function estadoLabel(estado: string): string {
  return ESTADO_LABELS[estado] ?? estado
}

/** A list-row detalle joined with its product/variant labels (MOD-1). */
export interface VentaDetalleRow {
  producto_id: number
  variante_id: number | null
  /** Product name, or `Producto #{id}` when the product is gone. */
  nombre: string
  /** Variant label, '(base)' for the base product, or `Variante #{id}`. */
  variante: string
  /** Raw Decimal-as-string snapshot values (formatted at render time). */
  cantidad: string
  precio_unitario_aplicado: string
}

/** A list-row venta joined with cliente name + labeled details (MOD-1). */
export interface VentaRow {
  id: number
  /** Raw ISO datetime (formatted at render time). */
  fecha: string
  canal_venta: string
  estado: string
  /** Raw Decimal-as-string total (formatted at render time). */
  total_venta: string
  /** Cliente name, or an em dash when the venta has no cliente. */
  cliente: string
  detalle_count: number
  detalles: VentaDetalleRow[]
}

/** One dynamic line item of the register form. */
export interface VentasFormDetalle {
  producto_id: number | null
  variante_id: number | null
  cantidad: number
  precio_unitario: number
}

/** The register form model (maps to VentaCreate via buildVentaPayload). */
export interface VentasFormModel {
  cliente_id: number | null
  canal_venta: CanalVenta
  descuento_porcentaje: number
  detalles: VentasFormDetalle[]
}

/**
 * MOD-1: slice the unbounded ventas list to the most recent `limit` entries.
 * The backend orders by id ascending, so "most recent" = highest ids; the
 * result is ordered newest-first for display.
 */
export function sliceVentas(ventas: VentaRead[], limit: number = VENTAS_LIST_LIMIT): VentaRead[] {
  return [...ventas].sort((a, b) => b.id - a.id).slice(0, limit)
}

/**
 * MOD-1: join ventas with product/variant/cliente names, degrading
 * gracefully: missing product -> `Producto #{id}`, null variante -> '(base)',
 * missing variante -> `Variante #{id}`, missing cliente -> '—'. Preserves the
 * input order.
 */
export function buildVentaRows(
  ventas: VentaRead[],
  productos: ProductoRead[],
  variantes: VarianteProductoRead[],
  clientes: ClienteRead[],
): VentaRow[] {
  const productosById = new Map(productos.map((p) => [p.id, p]))
  const variantesById = new Map(variantes.map((v) => [v.id, v]))
  const clientesById = new Map(clientes.map((c) => [c.id, c]))

  return ventas.map((v) => {
    const cliente = v.cliente_id === null ? null : clientesById.get(v.cliente_id)
    const detalles = v.detalles.map((d: DetalleVentaRead) => {
      const producto = productosById.get(d.producto_id)
      const variante = d.variante_id === null ? null : variantesById.get(d.variante_id)
      return {
        producto_id: d.producto_id,
        variante_id: d.variante_id,
        nombre: producto ? producto.nombre : `Producto #${d.producto_id}`,
        variante:
          d.variante_id === null
            ? '(base)'
            : variante
              ? variante.nombre_variante
              : `Variante #${d.variante_id}`,
        cantidad: d.cantidad,
        precio_unitario_aplicado: d.precio_unitario_aplicado,
      }
    })
    return {
      id: v.id,
      fecha: v.fecha,
      canal_venta: v.canal_venta,
      estado: v.estado,
      total_venta: v.total_venta,
      cliente: cliente ? cliente.nombre : '—',
      detalle_count: detalles.length,
      detalles,
    }
  })
}

/** A fresh empty line item for the register form (each call a new object). */
export function createDetalleRow(): VentasFormDetalle {
  return { producto_id: null, variante_id: null, cantidad: 1, precio_unitario: 0 }
}

/** MOD-1: at least one complete line item (product chosen AND cantidad > 0). */
export function hasValidDetalles(detalles: VentasFormDetalle[]): boolean {
  return detalles.some((d) => d.producto_id !== null && d.cantidad > 0)
}

/** Sum of cantidad * precio_unitario over the form rows (unparseable price = 0). */
export function ventaSubtotal(detalles: VentasFormDetalle[]): number {
  return detalles.reduce((sum, d) => {
    const precio = parseDecimal(d.precio_unitario) ?? 0
    const cantidad = typeof d.cantidad === 'number' && Number.isFinite(d.cantidad) ? d.cantidad : 0
    return sum + precio * cantidad
  }, 0)
}

/**
 * MOD-1: client-side total preview mirroring the server calculation
 * `sum(cantidad*precio) * (1 - descuento/100)`. Descuento is clamped to
 * [0,100] and the result is rounded to 2 decimals (Decimal precision).
 */
export function computeTotalPreview(detalles: VentasFormDetalle[], descuento: number): number {
  const subtotal = ventaSubtotal(detalles)
  const discount = Math.min(Math.max(descuento, 0), 100)
  return Math.round(subtotal * (1 - discount / 100) * 100) / 100
}

/**
 * MOD-1: map the form model to the VentaCreate POST body. Rows without a
 * product are dropped; `variante_id` and `cliente_id` are omitted (not null)
 * when absent; quantities/prices stay numbers.
 */
export function buildVentaPayload(form: VentasFormModel): VentaCreate {
  const detalles = form.detalles
    .filter((d) => d.producto_id !== null && d.cantidad > 0)
    .map((d) => ({
      producto_id: d.producto_id as number,
      ...(d.variante_id !== null ? { variante_id: d.variante_id } : {}),
      cantidad: d.cantidad,
      precio_unitario: d.precio_unitario,
    }))

  return {
    ...(form.cliente_id !== null ? { cliente_id: form.cliente_id } : {}),
    canal_venta: form.canal_venta,
    descuento_porcentaje: form.descuento_porcentaje,
    detalles,
  }
}
