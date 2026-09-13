/**
 * useSocios — REAL-only adapter over /api/v1/socios.
 *
 * Every operation delegates to src/services/api/socios.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/socios'

export interface UseSociosReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListSociosParams) => Promise<api.Paginated<api.SociaRead>>
  get: (id: number) => Promise<api.SociaRead | null>
  create: (payload: api.SociaCreatePayload) => Promise<api.SociaRead>
  update: (id: number, payload: api.SociaUpdatePayload) => Promise<api.SociaRead | null>
  remove: (id: number) => Promise<void>
}

export function useSocios(): UseSociosReturn {
  const { isMock, mode } = useMode()

  async function list(params: api.ListSociosParams = {}) {
    return api.listSocios(params)
  }

  async function get(id: number) {
    try {
      return await api.getSocia(id)
    } catch {
      return null
    }
  }

  async function create(payload: api.SociaCreatePayload) {
    return api.createSocia(payload)
  }

  async function update(id: number, payload: api.SociaUpdatePayload) {
    return api.updateSocia(id, payload)
  }

  async function remove(id: number): Promise<void> {
    return api.deleteSocia(id)
  }

  return { isMock, mode, list, get, create, update, remove }
}
