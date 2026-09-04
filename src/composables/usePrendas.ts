/**
 * usePrendas — adapter that selects Pinia mock or real API based on useMode.
 *
 * When isMock is true, operations run against src/stores/atelier.ts (in-memory).
 * Otherwise they delegate to src/services/api/prendas.ts (FastAPI + Postgres).
 * The interface is promise-based in both paths so callers can await uniformly.
 */
import { useAtelierStore, type PrendaConfeccionada } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/prendas'

export interface UsePrendasReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListPrendasParams) => Promise<api.Paginated<api.PrendaRead> | api.Paginated<PrendaConfeccionada>>
  get: (id: number) => Promise<api.PrendaRead | PrendaConfeccionada | null>
  create: (payload: api.PrendaCreatePayload) => Promise<api.PrendaRead | PrendaConfeccionada>
  update: (id: number, payload: api.PrendaUpdatePayload) => Promise<api.PrendaRead | PrendaConfeccionada | null>
  remove: (id: number) => Promise<void>
}

function toPaginatedPrendas(list: PrendaConfeccionada[], params: api.ListPrendasParams = {}): api.Paginated<PrendaConfeccionada> {
  let filtered = [...list]
  if (params.q) {
    const q = params.q.toLowerCase()
    filtered = filtered.filter(
      (p) =>
        p.nombre.toLowerCase().includes(q) ||
        (p.codigo && p.codigo.toLowerCase().includes(q)) ||
        (p.categoria && p.categoria.toLowerCase().includes(q)),
    )
  }
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function usePrendas(): UsePrendasReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function list(params: api.ListPrendasParams = {}) {
    if (isMock.value) {
      return toPaginatedPrendas(atelier.prendasListas as unknown as PrendaConfeccionada[], params)
    }
    return api.listPrendas(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return (atelier.prendasListas.find((p) => p.id === id) as unknown as PrendaConfeccionada) ?? null
    }
    return api.getPrenda(id)
  }

  async function create(payload: api.PrendaCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.prendasListas.map((p) => p.id)) + 1
      const created: PrendaConfeccionada = {
        id: nextId,
        codigo: `PRD-${nextId}`,
        nombre: `Prenda ${nextId}`,
        categoria: 'General',
        costo_base: payload.costo_real ?? 0,
        precio_venta: payload.precio_venta ?? 0,
        fisico_total: 1,
        disponible_total: 1,
        variantes: [
          {
            // P2-7: prenda genérica sin variante → id 0 + "Sin talla".
            id: payload.variante_id ?? 0,
            talla: payload.talla || (payload.variante_id == null ? 'Sin talla' : 'M'),
            color: 'Estándar',
            sku: payload.variante_id == null ? 'GENERICA' : `VAR-${payload.variante_id}`,
            stock_fisico: 1,
            reservado: 0,
            disponible: 1,
          },
        ],
      }
      atelier.prendasListas.unshift(created)
      return created
    }
    return api.createPrenda(payload)
  }

  async function update(id: number, payload: api.PrendaUpdatePayload) {
    if (isMock.value) {
      const idx = atelier.prendasListas.findIndex((p) => p.id === id)
      if (idx === -1) return null
      const existing = atelier.prendasListas[idx]
      const updated: PrendaConfeccionada = {
        ...existing,
        precio_venta: payload.precio_venta ?? existing.precio_venta,
        costo_base: payload.costo_real ?? existing.costo_base,
      }
      atelier.prendasListas[idx] = updated
      return updated
    }
    return api.updatePrenda(id, payload)
  }

  async function remove(id: number) {
    if (isMock.value) {
      const idx = atelier.prendasListas.findIndex((p) => p.id === id)
      if (idx !== -1) atelier.prendasListas.splice(idx, 1)
      return
    }
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
