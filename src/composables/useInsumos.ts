/**
 * useInsumos — REAL-only adapter over /api/v1/insumos.
 *
 * Every operation delegates to src/services/api/insumos.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/insumos'

export interface UseInsumosReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListInsumosParams) => Promise<api.Paginated<api.InsumoRead>>
  get: (id: number) => Promise<api.InsumoRead | null>
  create: (payload: api.InsumoCreatePayload) => Promise<api.InsumoRead>
  update: (id: number, payload: api.InsumoUpdatePayload) => Promise<api.InsumoRead | null>
  remove: (id: number) => Promise<void>
}

export function useInsumos(): UseInsumosReturn {
  const { isMock, mode } = useMode()

  async function list(params: api.ListInsumosParams = {}) {
    return api.listInsumos(params)
  }

  async function get(id: number) {
    return api.getInsumo(id)
  }

  async function create(payload: api.InsumoCreatePayload) {
    return api.createInsumo(payload)
  }

  async function update(id: number, payload: api.InsumoUpdatePayload) {
    return api.updateInsumo(id, payload)
  }

  async function remove(id: number) {
    return api.deleteInsumo(id)
  }

  return {
    isMock,
    mode,
    list,
    get,
    create,
    update,
    remove,
  }
}
