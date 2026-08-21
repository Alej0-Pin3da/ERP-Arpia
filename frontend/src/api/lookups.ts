/**
 * Lookup helpers (UX slice 1, TASK-040 partial).
 *
 * Every list view needs a full lookup set for client-side joins (product
 * names in ventas/devoluciones, insumo names in compras, socio names in
 * finanzas). The backend has no dedicated `/lookup` endpoint, so views today
 * fetch the full set with `limit: 1000` against the paginated list endpoint.
 *
 * ## Risk
 * - `limit:1000` is a stop-gap: if a table grows beyond 1000 rows the join
 *   degrades to `Producto #id` / `Insumo #id` fallbacks and filter dropdowns
 *   truncate. The correct fix is a backend lookup endpoint (small payload,
 *   `id + nombre` only, no pagination) — tracked as TODO below.
 * - Until then these helpers CENTRALIZE the `limit:1000` so the debt is
 *   visible in one place and views don't duplicate the magic number.
 * - If a lookup genuinely needs more than 1000 rows, use the paginated
 *   `fetchAllPaginated` helper (sequential pages) or client-side virtual
 *   scrolling in the Select — don't bump the limit blindly.
 */

import { categoriasInsumosApi, clientesApi, finanzasApi, insumosApi, productosApi } from '@/api/endpoints'
import type { components } from '@/types/api.d'

type InsumoRead = components['schemas']['InsumoRead']
type ProductoRead = components['schemas']['ProductoRead']
type SocioRead = components['schemas']['SocioConfiguracionRead']
type ClienteRead = components['schemas']['ClienteRead']
type CategoriaInsumoRead = components['schemas']['CategoriaInsumoRead']

// TODO: backend lookup endpoint — e.g. GET /productos/lookup, /insumos/lookup,
// GET /finanzas/socios/lookup returning id+nombre only, no pagination. Replace
// the limit:1000 calls below when available.

/** Fetch all productos for joins/filters (limit:1000 stop-gap). */
export async function fetchProductosLookup(): Promise<ProductoRead[]> {
  // TODO: backend lookup endpoint — GET /productos/lookup
  const page = await productosApi.list({ limit: 1000 })
  return page.items
}

/** Fetch all insumos for joins/filters (limit:1000 stop-gap). */
export async function fetchInsumosLookup(): Promise<InsumoRead[]> {
  // TODO: backend lookup endpoint — GET /insumos/lookup
  const page = await insumosApi.list({ limit: 1000 })
  return page.items
}

/** Fetch all socios for joins/filters (limit:1000 stop-gap). */
export async function fetchSociosLookup(): Promise<SocioRead[]> {
  // TODO: backend lookup endpoint — GET /finanzas/socios/lookup
  const page = await finanzasApi.listSocios({ limit: 1000 })
  return page.items as unknown as SocioRead[]
}

/** Fetch all clientes for joins/filters (limit:1000 stop-gap). */
export async function fetchClientesLookup(): Promise<ClienteRead[]> {
  // TODO: backend lookup endpoint — GET /clientes/lookup
  const page = await clientesApi.list({ limit: 1000 })
  return page.items
}

/** Fetch all categorias for filters (backend default limit is 100). */
export async function fetchCategoriasLookup(): Promise<CategoriaInsumoRead[]> {
  // TODO: backend lookup endpoint — GET /categorias-insumos/lookup
  const page = await categoriasInsumosApi.list({ limit: 1000 })
  return page.items
}

/**
 * Generic paginated fetch-all: sequentially loads pages until `total` is
 * reached. Use only when a lookup is expected to exceed 1000 rows before the
 * backend lookup endpoint exists. Prefers the lookup endpoint when available.
 */
export async function fetchAllPaginated<T>(
  fetcher: (params: { limit: number; offset: number }) => Promise<{ items: T[]; total: number }>,
  pageSize = 500,
): Promise<T[]> {
  const first = await fetcher({ limit: pageSize, offset: 0 })
  const all: T[] = [...first.items]
  let offset = pageSize
  while (all.length < first.total) {
    const page = await fetcher({ limit: pageSize, offset })
    all.push(...page.items)
    offset += pageSize
    if (page.items.length === 0) break
  }
  return all
}
