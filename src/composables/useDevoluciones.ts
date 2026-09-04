/**
 * useDevoluciones — adapter that selects local mock or real API based on useMode.
 *
 * When isMock is true, operations run against a module-scoped in-memory list
 * (the atelier store has no devoluciones collection; DevolucionesView kept a
 * per-view seed before this adapter). Otherwise they delegate to
 * src/services/api/devoluciones.ts (FastAPI + Postgres).
 */
import { useMode } from './useMode'
import * as api from '@/services/api/devoluciones'

export interface MockDevolucion {
  id: number
  codigo: string
  prenda: string
  cliente: string
  motivo: string
  tipo: string
  estado: string
  fecha: string
}

function seedMock(): MockDevolucion[] {
  return [
    {
      id: 1,
      codigo: 'GAR-001',
      prenda: 'Corset Nocturna Brocado',
      cliente: 'Carolina Gómez',
      motivo: 'Ajuste de varillas laterales por reducción de talle',
      tipo: 'Ajuste a Medida (Garantía Atelier)',
      estado: 'En Modificación',
      fecha: '2026-08-19',
    },
  ]
}

// Module-scoped so every consumer sees the same mock board (single view).
const mockRows: MockDevolucion[] = seedMock()

export interface UseDevolucionesReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: Record<string, unknown>) => Promise<api.Paginated<api.DevolucionRead> | api.Paginated<MockDevolucion>>
  get: (id: number) => Promise<api.DevolucionRead | MockDevolucion | null>
  create: (payload: api.DevolucionCreatePayload) => Promise<api.DevolucionRead | MockDevolucion>
  update: (id: number, payload: api.DevolucionUpdatePayload) => Promise<api.DevolucionRead | MockDevolucion | null>
  transition: (id: number, payload: api.DevolucionStateTransition) => Promise<api.DevolucionRead | MockDevolucion | null>
  remove: (id: number) => Promise<void>
}

export function useDevoluciones(): UseDevolucionesReturn {
  const { isMock, mode } = useMode()

  async function list(params: Record<string, unknown> = {}) {
    if (isMock.value) {
      void params
      return { items: [...mockRows], total: mockRows.length }
    }
    return api.listDevoluciones(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return mockRows.find((d) => d.id === id) ?? null
    }
    return api.getDevolucion(id)
  }

  async function create(payload: api.DevolucionCreatePayload) {
    if (isMock.value) {
      const nextId = mockRows.length ? Math.max(...mockRows.map((d) => d.id)) + 1 : 1
      const row: MockDevolucion = {
        id: nextId,
        codigo: `GAR-${String(nextId).padStart(3, '0')}`,
        prenda: `Venta #${payload.venta_id}`,
        cliente: `Cliente ${payload.venta_id}`,
        motivo: payload.motivo || 'Ajuste Atelier',
        tipo: payload.tipo === 'total' ? 'Devolución total' : 'Devolución parcial',
        estado: 'Registrada',
        fecha: new Date().toISOString().split('T')[0],
      }
      mockRows.unshift(row)
      return row
    }
    return api.createDevolucion(payload)
  }

  async function update(id: number, payload: api.DevolucionUpdatePayload) {
    if (isMock.value) {
      const row = mockRows.find((d) => d.id === id)
      if (!row) return null
      if (payload.motivo !== undefined) row.motivo = payload.motivo ?? row.motivo
      if (payload.estado !== undefined) row.estado = payload.estado ?? row.estado
      return row
    }
    return api.updateDevolucion(id, payload)
  }

  async function transition(id: number, payload: api.DevolucionStateTransition) {
    if (isMock.value) {
      const row = mockRows.find((d) => d.id === id)
      if (!row) return null
      row.estado = payload.estado
      if (payload.motivo) row.motivo = payload.motivo
      return row
    }
    return api.transitionDevolucion(id, payload)
  }

  async function remove(id: number): Promise<void> {
    if (isMock.value) {
      const idx = mockRows.findIndex((d) => d.id === id)
      if (idx !== -1) mockRows.splice(idx, 1)
      return
    }
    return api.deleteDevolucion(id)
  }

  return { isMock, mode, list, get, create, update, transition, remove }
}
