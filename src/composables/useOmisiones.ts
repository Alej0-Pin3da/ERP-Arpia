/**
 * useOmisiones — REAL-only adapter over /api/v1/omisiones.
 *
 * Every operation delegates to src/services/api/omisiones.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import * as api from '@/services/api/omisiones'

export interface UseOmisionesReturn {
  list: (params?: Record<string, unknown>) => Promise<api.Paginated<api.OmisionRead>>
  resolve: (id: number, resuelta?: boolean) => Promise<api.OmisionRead | null>
}

export function useOmisiones(): UseOmisionesReturn {
  async function list(params: Record<string, unknown> = {}) {
    return api.listOmisiones(params)
  }

  async function resolve(id: number, resuelta = true) {
    return api.resolveOmision(id, resuelta)
  }

  return { list, resolve }
}
