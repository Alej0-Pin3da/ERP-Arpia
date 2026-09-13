/**
 * useProduccion — REAL-only adapter over /api/v1/pedidos-produccion.
 *
 * Every operation delegates to src/services/api/pedidos-produccion.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/pedidos-produccion'

export interface UseProduccionReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListPedidosProduccionParams) => Promise<api.Paginated<api.PedidoProduccionRead>>
  get: (id: number) => Promise<api.PedidoProduccionRead | null>
  create: (payload: api.PedidoProduccionCreatePayload) => Promise<api.PedidoProduccionRead>
  update: (id: number, payload: api.PedidoProduccionUpdatePayload) => Promise<api.PedidoProduccionRead | null>
  remove: (id: number) => Promise<void>
}

export function useProduccion(): UseProduccionReturn {
  const { isMock, mode } = useMode()

  async function list(params: api.ListPedidosProduccionParams = {}) {
    return api.listPedidosProduccion(params)
  }

  async function get(id: number) {
    return api.getPedidoProduccion(id)
  }

  async function create(payload: api.PedidoProduccionCreatePayload) {
    return api.createPedidoProduccion(payload)
  }

  async function update(id: number, payload: api.PedidoProduccionUpdatePayload) {
    return api.updatePedidoProduccion(id, payload)
  }

  async function remove(id: number) {
    return api.deletePedidoProduccion(id)
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
