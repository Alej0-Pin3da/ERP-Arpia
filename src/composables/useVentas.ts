/**
 * useVentas — REAL-only adapter over /api/v1/ventas.
 *
 * Every operation delegates to src/services/api/ventas.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/ventas'

export interface UseVentasReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListVentasParams) => Promise<api.Paginated<api.VentaRead>>
  get: (id: number) => Promise<api.VentaRead | null>
  create: (payload: api.VentaCreatePayload) => Promise<api.VentaRead>
  anular: (id: number) => Promise<api.VentaRead | null>
}

export function useVentas(): UseVentasReturn {
  const { isMock, mode } = useMode()

  async function list(params: api.ListVentasParams = {}) {
    return api.listVentas(params)
  }

  async function get(id: number) {
    return api.getVenta(id)
  }

  async function create(payload: api.VentaCreatePayload) {
    return api.createVenta(payload)
  }

  async function anular(id: number) {
    return api.anularVenta(id)
  }

  return { isMock, mode, list, get, create, anular }
}
