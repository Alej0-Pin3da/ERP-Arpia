/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * useProduccion — adapter that selects Pinia mock or real API based on useMode.
 *
 * When isMock is true, operations run against src/stores/atelier.ts (in-memory).
 * Otherwise they delegate to src/services/api/pedidos-produccion.ts (FastAPI + Postgres).
 * The interface is promise-based in both paths so callers can await uniformly.
 */
import { useAtelierStore, type PedidoProduccion } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/pedidos-produccion'

export interface UseProduccionReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListPedidosProduccionParams) => Promise<api.Paginated<api.PedidoProduccionRead> | api.Paginated<PedidoProduccion>>
  get: (id: number) => Promise<api.PedidoProduccionRead | PedidoProduccion | null>
  create: (payload: api.PedidoProduccionCreatePayload) => Promise<api.PedidoProduccionRead | PedidoProduccion>
  update: (id: number, payload: api.PedidoProduccionUpdatePayload) => Promise<api.PedidoProduccionRead | PedidoProduccion | null>
  remove: (id: number) => Promise<void>
}

function toPaginatedPedidos(list: PedidoProduccion[], params: api.ListPedidosProduccionParams = {}): api.Paginated<PedidoProduccion> {
  let filtered = [...list]
  if (params.estado) {
    filtered = filtered.filter((p) => p.estado?.toLowerCase() === params.estado?.toLowerCase())
  }
  if (params.q) {
    const q = params.q.toLowerCase()
    filtered = filtered.filter(
      (p) =>
        p.codigo.toLowerCase().includes(q) ||
        p.cliente_nombre.toLowerCase().includes(q) ||
        p.prenda_nombre.toLowerCase().includes(q),
    )
  }
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function useProduccion(): UseProduccionReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function list(params: api.ListPedidosProduccionParams = {}) {
    if (isMock.value) {
      return toPaginatedPedidos(atelier.pedidos as unknown as PedidoProduccion[], params)
    }
    return api.listPedidosProduccion(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return (atelier.pedidos.find((p) => p.id === id) as unknown as PedidoProduccion) ?? null
    }
    return api.getPedidoProduccion(id)
  }

  async function create(payload: api.PedidoProduccionCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.pedidos.map((p) => p.id)) + 1
      const created: PedidoProduccion = {
        id: nextId,
        codigo: `ORD-${nextId}`,
        cliente_id: 1,
        cliente_nombre: 'Clienta General',
// eslint-disable-next-line @typescript-eslint/no-explicit-any
        prenda_nombre: `Producto ${payload.producto_id}`,
        estado: (payload.estado as any) || 'COTIZADO',
        precio_venta: 100000,
        costo_produccion: 50000,
        utilidad_neta: 50000,
        margen_pct: 50,
        fecha: payload.fecha_pedido || new Date().toISOString().split('T')[0],
        observaciones: payload.observaciones || undefined,
      }
      atelier.pedidos.unshift(created)
      return created
    }
    return api.createPedidoProduccion(payload)
  }

  async function update(id: number, payload: api.PedidoProduccionUpdatePayload) {
    if (isMock.value) {
      const idx = atelier.pedidos.findIndex((p) => p.id === id)
      if (idx === -1) return null
      const existing = atelier.pedidos[idx]
// eslint-disable-next-line @typescript-eslint/no-explicit-any
      const updated: PedidoProduccion = {
        ...existing,
        estado: (payload.estado as any) || existing.estado,
        observaciones: payload.observaciones ?? existing.observaciones,
      }
      atelier.pedidos[idx] = updated
      return updated
    }
    return api.updatePedidoProduccion(id, payload)
  }

  async function remove(id: number) {
    if (isMock.value) {
      const idx = atelier.pedidos.findIndex((p) => p.id === id)
      if (idx !== -1) atelier.pedidos.splice(idx, 1)
      return
    }
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
