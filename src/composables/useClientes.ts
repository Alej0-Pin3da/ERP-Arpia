/**
 * useClientes — adapter that selects Pinia mock or real API based on useMode.
 *
 * When isMock is true, operations run against src/stores/atelier.ts (in-memory).
 * Otherwise they delegate to src/services/api/clientes.ts (FastAPI + Postgres).
 * The interface is promise-based in both paths so callers can await uniformly.
 * *.vue templates remain intact — only the data source switches.
 */
import { useAtelierStore, type ClienteCRM } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/clientes'

export interface UseClientesReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListClientesParams) => Promise<api.Paginated<api.ClienteRead> | api.Paginated<ClienteCRM>>
  get: (id: number) => Promise<api.ClienteRead | ClienteCRM | null>
  create: (payload: api.ClienteCreatePayload) => Promise<api.ClienteRead | ClienteCRM>
  update: (id: number, payload: api.ClienteUpdatePayload) => Promise<api.ClienteRead | ClienteCRM | null>
  remove: (id: number) => Promise<void>
}

function toPaginatedClientes(list: ClienteCRM[], params: api.ListClientesParams = {}): api.Paginated<ClienteCRM> {
  let filtered = [...list]
  if (params.tipo) filtered = filtered.filter((c) => c.tipo === params.tipo)
  if (params.ciudad) filtered = filtered.filter((c) => c.ciudad === params.ciudad)
  if (params.q) {
    const q = params.q.toLowerCase()
    filtered = filtered.filter(
      (c) =>
        c.nombre.toLowerCase().includes(q) ||
        (c.ciudad && c.ciudad.toLowerCase().includes(q)) ||
        (c.direccion && c.direccion.toLowerCase().includes(q)),
    )
  }
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function useClientes(): UseClientesReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function list(params: api.ListClientesParams = {}) {
    if (isMock.value) {
      return toPaginatedClientes(atelier.clientes as unknown as ClienteCRM[], params)
    }
    return api.listClientes(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return (atelier.clientes.find((c) => c.id === id) as unknown as ClienteCRM) ?? null
    }
    return api.getCliente(id)
  }

  async function create(payload: api.ClienteCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.clientes.map((c) => c.id)) + 1
      const now = new Date().toISOString()
      const nuevo: ClienteCRM = {
        id: nextId,
        nombre: payload.nombre,
        tipo: (payload.tipo as string) ?? 'Clienta Habitual',
        telefono: (payload.telefono as string) ?? '',
        email: (payload.email as string) ?? '',
        ciudad: (payload.ciudad as string) ?? undefined,
        direccion: (payload.direccion as string) ?? undefined,
        pedidos_count: 0,
        total_compras: 0,
        talla_habitual: (payload.talla_habitual as string) ?? 'M',
        talla_superior: payload.talla_superior as string | undefined,
        talla_inferior: payload.talla_inferior as string | undefined,
        categoria_preferida: (payload.categoria_preferida as string) ?? 'Corsetería & Tops',
        tipo_producto_frecuente: payload.tipo_producto_frecuente as ClienteCRM['tipo_producto_frecuente'],
        notas: payload.notas as string | undefined,
        medidas: payload.medidas as ClienteCRM['medidas'],
        // keep extra fields for compatibility
        ...(payload as unknown as Record<string, unknown>),
      } as unknown as ClienteCRM
      // Store expects ClienteCRM; push and return
      atelier.clientes.unshift(nuevo as unknown as typeof atelier.clientes[number])
      void now
      return nuevo
    }
    return api.createCliente(payload)
  }

  async function update(id: number, payload: api.ClienteUpdatePayload) {
    if (isMock.value) {
      const idx = atelier.clientes.findIndex((c) => c.id === id)
      if (idx === -1) return null
      const current = atelier.clientes[idx] as unknown as Record<string, unknown>
      Object.assign(current, payload)
      return current as unknown as ClienteCRM
    }
    return api.updateCliente(id, payload)
  }

  async function remove(id: number): Promise<void> {
    if (isMock.value) {
      const idx = atelier.clientes.findIndex((c) => c.id === id)
      if (idx !== -1) atelier.clientes.splice(idx, 1)
      return
    }
    return api.deleteCliente(id)
  }

  return { isMock, mode, list, get, create, update, remove }
}
