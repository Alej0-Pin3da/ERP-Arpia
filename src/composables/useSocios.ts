/**
 * useSocios — adapter that selects Pinia mock or real API based on useMode.
 *
 * When isMock is true, operations run against src/stores/atelier.ts (in-memory).
 * Otherwise they delegate to src/services/api/socios.ts (FastAPI + Postgres).
 * Mirrors useClientes / useVentas pattern; *.vue remain intact.
 */
import { useAtelierStore, type SociaAtelier } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/socios'

export interface UseSociosReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListSociosParams) => Promise<api.Paginated<api.SociaRead> | api.Paginated<SociaAtelier>>
  get: (id: number) => Promise<api.SociaRead | SociaAtelier | null>
  create: (payload: api.SociaCreatePayload) => Promise<api.SociaRead | SociaAtelier>
  update: (id: number, payload: api.SociaUpdatePayload) => Promise<api.SociaRead | SociaAtelier | null>
  remove: (id: number) => Promise<void>
}

function toPaginatedSocias(list: SociaAtelier[], params: api.ListSociosParams = {}): api.Paginated<SociaAtelier> {
  let filtered = [...list]
  if (params.activo !== undefined) filtered = filtered.filter((s) => s.activo === params.activo)
  if (params.es_fondo_taller !== undefined) filtered = filtered.filter((s) => Boolean(s.es_fondo_taller) === params.es_fondo_taller)
  if (params.rol) filtered = filtered.filter((s) => s.rol === params.rol)
  if (params.q) {
    const q = params.q.toLowerCase()
    filtered = filtered.filter(
      (s) =>
        s.nombre.toLowerCase().includes(q) ||
        (s.email && s.email.toLowerCase().includes(q)) ||
        (s.telefono && s.telefono.toLowerCase().includes(q)),
    )
  }
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function useSocios(): UseSociosReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function list(params: api.ListSociosParams = {}) {
    if (isMock.value) {
      return toPaginatedSocias(atelier.socias as unknown as SociaAtelier[], params)
    }
    return api.listSocios(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return (atelier.socias.find((s) => s.id === id) as unknown as SociaAtelier) ?? null
    }
    try {
      return await api.getSocia(id)
    } catch {
      return null
    }
  }

  async function create(payload: api.SociaCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.socias.map((s) => s.id)) + 1
      const nuevo: SociaAtelier = {
        id: nextId,
        nombre: payload.nombre,
        rol: (payload.rol as string) ?? 'Socia Atelier',
        porcentaje: Number(payload.porcentaje_participacion),
        es_fondo_taller: payload.es_fondo_taller ?? false,
        telefono: (payload.telefono as string) ?? undefined,
        email: (payload.email as string) ?? undefined,
        banco: (payload.banco as string) ?? undefined,
        tipo_cuenta: payload.tipo_cuenta as string | undefined,
        numero_cuenta: payload.numero_cuenta as string | undefined,
        titular_cuenta: payload.titular_cuenta as string | undefined,
        activo: payload.activo ?? true,
        notas: payload.notas as string | undefined,
      }
      atelier.socias.unshift(nuevo as unknown as typeof atelier.socias[number])
      return nuevo
    }
    return api.createSocia(payload)
  }

  async function update(id: number, payload: api.SociaUpdatePayload) {
    if (isMock.value) {
      const idx = atelier.socias.findIndex((s) => s.id === id)
      if (idx === -1) return null
      const current = atelier.socias[idx] as unknown as Record<string, unknown>
      // map porcentaje_participacion -> porcentaje for atelier shape
      if ('porcentaje_participacion' in payload && payload.porcentaje_participacion !== undefined) {
        ;(current as Record<string, unknown>).porcentaje = Number(payload.porcentaje_participacion)
        const copy = { ...payload } as Record<string, unknown>
        delete copy.porcentaje_participacion
        Object.assign(current, copy)
      } else {
        Object.assign(current, payload)
      }
      return current as unknown as SociaAtelier
    }
    return api.updateSocia(id, payload)
  }

  async function remove(id: number): Promise<void> {
    if (isMock.value) {
      const idx = atelier.socias.findIndex((s) => s.id === id)
      if (idx !== -1) atelier.socias.splice(idx, 1)
      return
    }
    return api.deleteSocia(id)
  }

  return { isMock, mode, list, get, create, update, remove }
}
