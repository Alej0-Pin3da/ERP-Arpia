/**
 * Shared client-side lookup helpers for list joins (PR7).
 *
 * List payloads (VentaRead.detalles, DevolucionRead.items, margen rows) carry
 * only product/variant IDs — display names are joined client-side against
 * GET /productos. This module centralizes the map-building + graceful
 * fallback used by the ventas and devoluciones modules (and the dashboard
 * margen join, which follows the same `Producto #{id}` convention).
 */
import type { components } from '@/types/api.d'

type ProductoRead = components['schemas']['ProductoRead']

/** Map of producto id -> ProductoRead for O(1) client-side joins. */
export function buildProductosById(productos: ProductoRead[]): Map<number, ProductoRead> {
  return new Map(productos.map((p) => [p.id, p]))
}

/**
 * Product display name for a list join. Degrades gracefully when the product
 * no longer exists: `Producto #{id}` (design "Missing joins MUST degrade").
 */
export function productoNombre(productosById: Map<number, ProductoRead>, productoId: number): string {
  return productosById.get(productoId)?.nombre ?? `Producto #${productoId}`
}
