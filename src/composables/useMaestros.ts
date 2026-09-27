/**
 * useMaestros — REAL-only adapter over /api/v1/maestros with SWR/TTL Caching.
 * Every operation delegates to src/services/api/maestros.ts
 * (FastAPI + Postgres).
 *
 * Implements SWR/TTL caching for master catalogs (canales, metodos, categorias, etc.)
 * with automatic invalidation on mutations (create/update/delete).
 */
import { useMode } from './useMode'
import * as api from '@/services/api/maestros'

interface CacheEntry<T> {
  data: T
  timestamp: number
}

// In-memory cache shared across composable instances
const maestrosCache = new Map<string, CacheEntry<unknown>>()
const DEFAULT_TTL_MS = 60_000 // 60 seconds

export function clearMaestrosCache(domain?: string) {
  if (!domain) {
    maestrosCache.clear()
    return
  }
  const prefix = `${domain}:`
  for (const key of maestrosCache.keys()) {
    if (key.startsWith(prefix)) {
      maestrosCache.delete(key)
    }
  }
}

async function fetchWithCache<T>(
  domain: string,
  params: Record<string, unknown>,
  fetcher: () => Promise<T>,
  ttlMs = DEFAULT_TTL_MS,
  forceRefresh = false
): Promise<T> {
  const cacheKey = `${domain}:${JSON.stringify(params)}`
  const now = Date.now()
  const cached = maestrosCache.get(cacheKey)

  if (!forceRefresh && cached && now - cached.timestamp < ttlMs) {
    return cached.data as T
  }

  const result = await fetcher()
  maestrosCache.set(cacheKey, { data: result, timestamp: now })
  return result
}

export function useMaestros() {
  const { isMock, mode } = useMode()

  // Proveedores
  async function listProveedores(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('proveedores', params, () => api.listProveedores(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createProveedor(payload: Record<string, unknown>) {
    const res = await api.createProveedor(payload)
    clearMaestrosCache('proveedores')
    return res
  }
  async function updateProveedor(id: number, payload: Record<string, unknown>) {
    const res = await api.updateProveedor(id, payload)
    clearMaestrosCache('proveedores')
    return res
  }
  async function removeProveedor(id: number) {
    const res = await api.deleteProveedor(id)
    clearMaestrosCache('proveedores')
    return res
  }

  // Categorias
  async function listCategorias(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('categorias', params, () => api.listCategorias(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createCategoria(payload: Record<string, unknown>) {
    const res = await api.createCategoria(payload)
    clearMaestrosCache('categorias')
    return res
  }
  async function updateCategoria(id: number, payload: Record<string, unknown>) {
    const res = await api.updateCategoria(id, payload)
    clearMaestrosCache('categorias')
    return res
  }
  async function removeCategoria(id: number) {
    const res = await api.deleteCategoria(id)
    clearMaestrosCache('categorias')
    return res
  }

  // Ubicaciones
  async function listUbicaciones(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('ubicaciones', params, () => api.listUbicaciones(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createUbicacion(payload: Record<string, unknown>) {
    const res = await api.createUbicacion(payload)
    clearMaestrosCache('ubicaciones')
    return res
  }
  async function updateUbicacion(id: number, payload: Record<string, unknown>) {
    const res = await api.updateUbicacion(id, payload)
    clearMaestrosCache('ubicaciones')
    return res
  }
  async function removeUbicacion(id: number) {
    const res = await api.deleteUbicacion(id)
    clearMaestrosCache('ubicaciones')
    return res
  }

  // Canales
  async function listCanales(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('canales', params, () => api.listCanales(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createCanal(payload: Record<string, unknown>) {
    const res = await api.createCanal(payload)
    clearMaestrosCache('canales')
    return res
  }
  async function updateCanal(id: number, payload: Record<string, unknown>) {
    const res = await api.updateCanal(id, payload)
    clearMaestrosCache('canales')
    return res
  }
  async function removeCanal(id: number) {
    const res = await api.deleteCanal(id)
    clearMaestrosCache('canales')
    return res
  }

  // Metodos
  async function listMetodosPago(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('metodos', params, () => api.listMetodosPago(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createMetodo(payload: Record<string, unknown>) {
    const res = await api.createMetodo(payload)
    clearMaestrosCache('metodos')
    return res
  }
  async function updateMetodo(id: number, payload: Record<string, unknown>) {
    const res = await api.updateMetodo(id, payload)
    clearMaestrosCache('metodos')
    return res
  }
  async function removeMetodo(id: number) {
    const res = await api.deleteMetodo(id)
    clearMaestrosCache('metodos')
    return res
  }

  // Tallas
  async function listTallas(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('tallas', params, () => api.listTallas(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createTalla(payload: Record<string, unknown>) {
    const res = await api.createTalla(payload)
    clearMaestrosCache('tallas')
    return res
  }
  async function updateTalla(id: number, payload: Record<string, unknown>) {
    const res = await api.updateTalla(id, payload)
    clearMaestrosCache('tallas')
    return res
  }
  async function removeTalla(id: number) {
    const res = await api.deleteTalla(id)
    clearMaestrosCache('tallas')
    return res
  }

  // Productos sin talla
  async function listProductosSinTalla(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('sintalla', params, () => api.listProductosSinTalla(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createProductoSinTalla(payload: Record<string, unknown>) {
    const res = await api.createProductoSinTalla(payload)
    clearMaestrosCache('sintalla')
    return res
  }
  async function updateProductoSinTalla(id: number, payload: Record<string, unknown>) {
    const res = await api.updateProductoSinTalla(id, payload)
    clearMaestrosCache('sintalla')
    return res
  }
  async function removeProductoSinTalla(id: number) {
    const res = await api.deleteProductoSinTalla(id)
    clearMaestrosCache('sintalla')
    return res
  }

  // Categorias de producto (master Categoría/Línea de la Ficha, 0037)
  async function listCategoriasProducto(params: api.ListParams = {}, forceRefresh = false) {
    return fetchWithCache('catprod', params, () => api.listCategoriasProducto(params), DEFAULT_TTL_MS, forceRefresh)
  }
  async function createCategoriaProducto(payload: Record<string, unknown>) {
    const res = await api.createCategoriaProducto(payload)
    clearMaestrosCache('catprod')
    return res
  }
  async function updateCategoriaProducto(id: number, payload: Record<string, unknown>) {
    const res = await api.updateCategoriaProducto(id, payload)
    clearMaestrosCache('catprod')
    return res
  }
  async function removeCategoriaProducto(id: number) {
    const res = await api.deleteCategoriaProducto(id)
    clearMaestrosCache('catprod')
    return res
  }

  // Parametros singleton
  async function getParametros(forceRefresh = false) {
    return fetchWithCache('parametros', {}, () => api.getParametros(), DEFAULT_TTL_MS, forceRefresh)
  }
  async function updateParametros(payload: Record<string, unknown>) {
    const res = await api.updateParametros(payload)
    clearMaestrosCache('parametros')
    return res
  }

  return {
    isMock,
    mode,
    clearCache: clearMaestrosCache,
    // proveedores
    listProveedores,
    createProveedor,
    updateProveedor,
    removeProveedor,
    // categorias
    listCategorias,
    createCategoria,
    updateCategoria,
    removeCategoria,
    // categorias de producto
    listCategoriasProducto,
    createCategoriaProducto,
    updateCategoriaProducto,
    removeCategoriaProducto,
    // ubicaciones
    listUbicaciones,
    createUbicacion,
    updateUbicacion,
    removeUbicacion,
    // canales
    listCanales,
    createCanal,
    updateCanal,
    removeCanal,
    // metodos
    listMetodosPago,
    createMetodo,
    updateMetodo,
    removeMetodo,
    // tallas
    listTallas,
    createTalla,
    updateTalla,
    removeTalla,
    // sin talla
    listProductosSinTalla,
    createProductoSinTalla,
    updateProductoSinTalla,
    removeProductoSinTalla,
    // parametros
    getParametros,
    updateParametros,
  }
}
