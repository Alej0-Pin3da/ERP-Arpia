/**
 * usePrendas — REAL-only adapter over /api/v1/prendas.
 *
 * Every operation delegates to src/services/api/prendas.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/prendas'

export interface UsePrendasReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListPrendasParams) => Promise<api.Paginated<api.PrendaRead>>
  get: (id: number) => Promise<api.PrendaRead | null>
  create: (payload: api.PrendaCreatePayload) => Promise<api.PrendaRead>
  update: (id: number, payload: api.PrendaUpdatePayload) => Promise<api.PrendaRead | null>
  remove: (id: number) => Promise<void>
}

export function usePrendas(): UsePrendasReturn {
  const { isMock, mode } = useMode()

  async function list(params: api.ListPrendasParams = {}) {
    return api.listPrendas(params)
  }

  async function get(id: number) {
    return api.getPrenda(id)
  }

  async function create(payload: api.PrendaCreatePayload) {
    return api.createPrenda(payload)
  }

  async function update(id: number, payload: api.PrendaUpdatePayload) {
    return api.updatePrenda(id, payload)
  }

  async function remove(id: number) {
    return api.deletePrenda(id)
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
