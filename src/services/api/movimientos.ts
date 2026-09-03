import { client } from '@/api/client'

/** Mirrors `backend/app/schemas/finanzas.py` MovimientoRead (read-only + state). */
export interface MovimientoRead {
  id: number
  fecha: string
  tipo: string
  descripcion: string
  monto: number | string
  socio_id: number | null
  estado: string
  liquidacion_id: string | null
}

export interface ListMovimientosParams {
  tipo?: 'Gasto' | 'Inversion' | 'Retiro'
  estado?: 'draft' | 'confirmed' | 'cancelled' | 'reversed'
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export interface Paginated<T> { items: T[]; total: number }

export interface MovimientoStateTransition {
  estado: 'draft' | 'confirmed' | 'cancelled' | 'reversed'
  motivo?: string | null
}

/**
 * List financial movements (`GET /finanzas/movimientos`).
 * Backend returns `{ items, total }`; supports `tipo`/`estado` filters.
 * NOTE: backend has no date-range filter — date filtering is client-side only.
 */
export async function listMovimientos(params?: ListMovimientosParams): Promise<Paginated<MovimientoRead>> {
  const { data } = await client.get<Paginated<MovimientoRead>>('/finanzas/movimientos', { params })
  return data
}

export async function transitionMovimiento(
  id: number,
  payload: MovimientoStateTransition,
): Promise<MovimientoRead> {
  const { data } = await client.patch<MovimientoRead>(`/finanzas/movimientos/${id}/state`, payload)
  return data
}
