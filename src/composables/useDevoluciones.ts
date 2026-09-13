/**
 * useDevoluciones — REAL-only adapter over /api/v1/devoluciones.
 *
 * Every operation delegates to src/services/api/devoluciones.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 */
import * as api from '@/services/api/devoluciones'

export interface UseDevolucionesReturn {
  list: (params?: Record<string, unknown>) => Promise<api.Paginated<api.DevolucionRead>>
  get: (id: number) => Promise<api.DevolucionRead | null>
  create: (payload: api.DevolucionCreatePayload) => Promise<api.DevolucionRead>
  update: (id: number, payload: api.DevolucionUpdatePayload) => Promise<api.DevolucionRead | null>
  transition: (id: number, payload: api.DevolucionStateTransition) => Promise<api.DevolucionRead | null>
  remove: (id: number) => Promise<void>
}

export function useDevoluciones(): UseDevolucionesReturn {
  async function list(params: Record<string, unknown> = {}) {
    return api.listDevoluciones(params)
  }

  async function get(id: number) {
    return api.getDevolucion(id)
  }

  async function create(payload: api.DevolucionCreatePayload) {
    return api.createDevolucion(payload)
  }

  async function update(id: number, payload: api.DevolucionUpdatePayload) {
    return api.updateDevolucion(id, payload)
  }

  async function transition(id: number, payload: api.DevolucionStateTransition) {
    return api.transitionDevolucion(id, payload)
  }

  async function remove(id: number): Promise<void> {
    return api.deleteDevolucion(id)
  }

  return { list, get, create, update, transition, remove }
}
