/**
 * useInsumos — adapter that selects Pinia mock or real API based on useMode.
 *
 * When isMock is true, operations run against src/stores/atelier.ts (in-memory).
 * Otherwise they delegate to src/services/api/insumos.ts (FastAPI + Postgres).
 * The interface is promise-based in both paths so callers can await uniformly.
 */
import { useAtelierStore, type InsumoAtelier } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/insumos'

export interface UseInsumosReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListInsumosParams) => Promise<api.Paginated<api.InsumoRead> | api.Paginated<InsumoAtelier>>
  get: (id: number) => Promise<api.InsumoRead | InsumoAtelier | null>
  create: (payload: api.InsumoCreatePayload) => Promise<api.InsumoRead | InsumoAtelier>
  update: (id: number, payload: api.InsumoUpdatePayload) => Promise<api.InsumoRead | InsumoAtelier | null>
  remove: (id: number) => Promise<void>
}

function toPaginatedInsumos(list: InsumoAtelier[], params: api.ListInsumosParams = {}): api.Paginated<InsumoAtelier> {
  let filtered = [...list]
  if (params.tipo) {
    filtered = filtered.filter((i) => i.tipo?.toLowerCase() === params.tipo?.toLowerCase())
  }
  if (params.q) {
    const q = params.q.toLowerCase()
    filtered = filtered.filter(
      (i) =>
        i.nombre.toLowerCase().includes(q) ||
        (i.codigo && i.codigo.toLowerCase().includes(q)) ||
        (i.tipo && i.tipo.toLowerCase().includes(q)) ||
        (i.ubicacion && i.ubicacion.toLowerCase().includes(q)),
    )
  }
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function useInsumos(): UseInsumosReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function list(params: api.ListInsumosParams = {}) {
    if (isMock.value) {
      return toPaginatedInsumos(atelier.insumos as unknown as InsumoAtelier[], params)
    }
    return api.listInsumos(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return (atelier.insumos.find((i) => i.id === id) as unknown as InsumoAtelier) ?? null
    }
    return api.getInsumo(id)
  }

  async function create(payload: api.InsumoCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.insumos.map((i) => i.id)) + 1
      const created: InsumoAtelier = {
        id: nextId,
        codigo: payload.codigo || `INS-${nextId}`,
        nombre: payload.nombre,
        categoria: 'General',
        unidad_medida: payload.unidad_medida,
        tipo: payload.tipo || 'Directo',
        ubicacion: payload.ubicacion || 'Bodega',
        stock_actual: payload.stock_actual ?? 0,
        stock_minimo: payload.stock_minimo ?? 0,
        costo_promedio_actual: payload.costo_promedio_actual ?? 0,
        proveedor: 'Atelier',
        rendimiento_aprox: '1 unidad',
        estado: 'Disponible',
      }
      atelier.insumos.unshift(created)
      return created
    }
    return api.createInsumo(payload)
  }

  async function update(id: number, payload: api.InsumoUpdatePayload) {
    if (isMock.value) {
      const idx = atelier.insumos.findIndex((i) => i.id === id)
      if (idx === -1) return null
      const updated = { ...atelier.insumos[idx], ...payload }
      atelier.insumos[idx] = updated
      return updated
    }
    return api.updateInsumo(id, payload)
  }

  async function remove(id: number) {
    if (isMock.value) {
      const idx = atelier.insumos.findIndex((i) => i.id === id)
      if (idx !== -1) atelier.insumos.splice(idx, 1)
      return
    }
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
