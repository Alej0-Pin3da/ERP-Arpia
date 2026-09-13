/**
 * useClientes — REAL-only adapter over /api/v1/clientes.
 *
 * Every operation delegates to src/services/api/clientes.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/clientes'

export interface UseClientesReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListClientesParams) => Promise<api.Paginated<api.ClienteRead>>
  get: (id: number) => Promise<api.ClienteRead | null>
  create: (payload: api.ClienteCreatePayload) => Promise<api.ClienteRead>
  update: (id: number, payload: api.ClienteUpdatePayload) => Promise<api.ClienteRead | null>
  remove: (id: number) => Promise<void>
}

export function useClientes(): UseClientesReturn {
  const { isMock, mode } = useMode()

  async function list(params: api.ListClientesParams = {}) {
    return api.listClientes(params)
  }

  async function get(id: number) {
    return api.getCliente(id)
  }

  async function create(payload: api.ClienteCreatePayload) {
    return api.createCliente(payload)
  }

  async function update(id: number, payload: api.ClienteUpdatePayload) {
    return api.updateCliente(id, payload)
  }

  async function remove(id: number): Promise<void> {
    return api.deleteCliente(id)
  }

  return { isMock, mode, list, get, create, update, remove }
}
