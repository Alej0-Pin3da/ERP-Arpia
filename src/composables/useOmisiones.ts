/**
 * useOmisiones — adapter that selects local mock or real API based on useMode.
 *
 * When isMock is true, operations run against a module-scoped in-memory list
 * (the atelier store has no omisiones collection; OmisionesView kept a
 * per-view seed before this adapter). Otherwise they delegate to
 * src/services/api/omisiones.ts (FastAPI + Postgres).
 */
import { useMode } from './useMode'
import * as api from '@/services/api/omisiones'

export interface MockOmision {
  id: number
  fecha: string
  usuario: string
  evento: string
  impacto: string
  resuelta?: boolean
}

function seedMock(): MockOmision[] {
  return [
    {
      id: 1,
      fecha: '2026-08-20 14:30',
      usuario: 'Camila Modista',
      evento: 'Descuento manual de merma en encaje Chantilly por falla de estiramiento',
      impacto: '-0.35m Tela',
      resuelta: false,
    },
    {
      id: 2,
      fecha: '2026-08-18 10:15',
      usuario: 'Valeria Arpía',
      evento: 'Ajuste de precio de cotización especial para clienta VIP',
      impacto: 'Descuento $40.000 COP',
      resuelta: false,
    },
  ]
}

// Module-scoped so every consumer sees the same mock board (single view).
const mockRows: MockOmision[] = seedMock()

export interface UseOmisionesReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: Record<string, unknown>) => Promise<api.Paginated<api.OmisionRead> | api.Paginated<MockOmision>>
  resolve: (id: number, resuelta?: boolean) => Promise<api.OmisionRead | MockOmision | null>
}

export function useOmisiones(): UseOmisionesReturn {
  const { isMock, mode } = useMode()

  async function list(params: Record<string, unknown> = {}) {
    if (isMock.value) {
      let rows = [...mockRows]
      const q = typeof params.q === 'string' ? params.q.toLowerCase() : ''
      if (q) rows = rows.filter((o) => o.evento.toLowerCase().includes(q))
      const total = rows.length
      const offset = typeof params.offset === 'number' ? params.offset : 0
      const limit = typeof params.limit === 'number' ? params.limit : 50
      return { items: rows.slice(offset, offset + limit), total }
    }
    return api.listOmisiones(params)
  }

  async function resolve(id: number, resuelta = true) {
    if (isMock.value) {
      const row = mockRows.find((o) => o.id === id)
      if (!row) return null
      row.resuelta = resuelta
      return row
    }
    return api.resolveOmision(id, resuelta)
  }

  return { isMock, mode, list, resolve }
}
