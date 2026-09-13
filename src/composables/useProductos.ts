/**
 * useProductos — REAL-only adapter over /api/v1/productos.
 *
 * Every operation delegates to src/services/api/productos.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/productos'

export interface UseProductosReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListProductosParams) => Promise<api.Paginated<api.ProductoRead>>
  get: (id: number) => Promise<api.ProductoRead | null>
  create: (payload: api.ProductoCreate) => Promise<api.ProductoRead>
  update: (id: number, payload: api.ProductoUpdate) => Promise<api.ProductoRead | null>
  remove: (id: number) => Promise<void>
}

export function useProductos(): UseProductosReturn {
  const { isMock, mode } = useMode()

  async function list(params: api.ListProductosParams = {}) {
    return api.listProductos(params)
  }

  async function get(id: number) {
    return api.getProducto(id)
  }

  async function create(payload: api.ProductoCreate) {
    return api.createProducto(payload)
  }

  async function update(id: number, payload: api.ProductoUpdate) {
    return api.updateProducto(id, payload)
  }

  async function remove(id: number): Promise<void> {
    return api.deleteProducto(id)
  }

  return { isMock, mode, list, get, create, update, remove }
}
