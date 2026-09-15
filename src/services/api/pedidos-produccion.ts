/**
 * Pedidos de Producción API service — typed CRUD via shared axios client.
 * Base path: /pedidos-produccion (client baseURL is /api/v1).
 * Mirrors backend schemas/produccion.py (PedidoProduccionCreate/Update/Read).
 */
import { client } from '@/api/client'

export interface PedidoProduccionRead {
  id: number
  producto_id: number
  // Clienta que realiza el pedido (migración 0026, nullable).
  cliente_id?: number | null
  variante_id?: number | null
  cantidad: number
  cantidad_producida: number
  // Workshop phase (migración 0030, lote slice): corte → costura → acabados → calidad → listo.
  fase: string
  estado: string
  prioridad: string
  fecha_pedido: string
  fecha_entrega_estimada?: string | null
  observaciones?: string | null
  created_at: string
  updated_at: string
  // Unit-cost snapshot taken once at lot completion (null until then).
  costo_unitario_snapshot?: number | string | null
  // Real labor/energy cost derived at read time from TiempoFase rows x
  // global rates (null/undefined while no tiempos are logged — "no data").
  mano_obra_real?: number | string | null
  energia_real?: number | string | null
  nombre_producto?: string | null
  nombre_variante?: string | null
  cliente_nombre?: string | null
}

export interface PedidoProduccionCreatePayload {
  producto_id: number
  cliente_id?: number | null
  variante_id?: number | null
  cantidad: number
  cantidad_producida?: number
  fase?: string
  estado?: string
  prioridad?: string
  fecha_pedido?: string
  fecha_entrega_estimada?: string | null
  observaciones?: string | null
}

export type PedidoProduccionUpdatePayload = Partial<PedidoProduccionCreatePayload> & {
  cliente_id?: number | null
}

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListPedidosProduccionParams {
  q?: string
  producto_id?: number
  variante_id?: number
  estado?: string
  fase?: string
  prioridad?: string
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

/** Canonical workshop order — mirrors backend FASES_PRODUCCION_ORDEN (migración 0030). */
export const FASES_PRODUCCION: readonly string[] = [
  'corte',
  'costura',
  'acabados',
  'calidad',
  'listo',
]

/** Next phase after `fase`, or undefined when already at 'listo'. */
export function siguienteFase(fase: string | null | undefined): string | undefined {
  const idx = FASES_PRODUCCION.indexOf(fase ?? '')
  if (idx < 0 || idx >= FASES_PRODUCCION.length - 1) return undefined
  return FASES_PRODUCCION[idx + 1]
}

/**
 * Extract the backend error detail string as-is (400 skip/back, 422 unknown
 * fase, 409 shortage with per-insumo detail). FastAPI may return `detail` as
 * a string or a validation-error array — both are surfaced verbatim.
 */
export function extractApiDetail(e: unknown): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const response = (e as any)?.response
  const detail = response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const parts = detail.map((d: any) =>
      typeof d === 'string' ? d : (d?.msg ?? JSON.stringify(d)),
    )
    if (parts.length) return parts.join('; ')
  }
  if (e instanceof Error && e.message) return e.message
  return 'Error desconocido'
}

export async function listPedidosProduccion(
  params?: ListPedidosProduccionParams
): Promise<Paginated<PedidoProduccionRead>> {
  const { data } = await client.get<Paginated<PedidoProduccionRead>>('/pedidos-produccion', {
    params,
  })
  return data
}

export async function getPedidoProduccion(id: number): Promise<PedidoProduccionRead> {
  const { data } = await client.get<PedidoProduccionRead>(`/pedidos-produccion/${id}`)
  return data
}

export async function createPedidoProduccion(
  payload: PedidoProduccionCreatePayload
): Promise<PedidoProduccionRead> {
  const { data } = await client.post<PedidoProduccionRead>('/pedidos-produccion', payload)
  return data
}

export async function updatePedidoProduccion(
  id: number,
  payload: PedidoProduccionUpdatePayload
): Promise<PedidoProduccionRead> {
  const { data } = await client.patch<PedidoProduccionRead>(`/pedidos-produccion/${id}`, payload)
  return data
}

export async function deletePedidoProduccion(id: number): Promise<void> {
  await client.delete(`/pedidos-produccion/${id}`)
}

/**
 * Real-time logging (backend FASES_TIEMPO_ORDEN, migración 0031): one row per
 * (pedido, fase). `listo` closes the lot and is never logged. Money
 * (costo_mano_obra/costo_energia) is derived at read time, never stored.
 */
export const FASES_TIEMPO: readonly string[] = [
  'corte',
  'costura',
  'acabados',
  'calidad',
]

export interface TiempoFaseRead {
  id: number
  pedido_id: number
  fase: string
  operaria: string
  minutos_reales: number | string
  fecha: string
  costo_mano_obra?: number | string | null
  costo_energia?: number | string | null
}

export interface TiemposListRead {
  items: TiempoFaseRead[]
  total_minutos: number | string
  total_mano_obra: number | string
  total_energia: number | string
}

export interface TiempoFaseCreatePayload {
  fase: string
  operaria: string
  minutos_reales: number
  fecha?: string
}

export interface TiempoFaseUpdatePayload {
  operaria?: string
  minutos_reales?: number
}

export async function listTiemposPedido(pedidoId: number): Promise<TiemposListRead> {
  const { data } = await client.get<TiemposListRead>(`/pedidos-produccion/${pedidoId}/tiempos`)
  return data
}

export async function createTiempoPedido(
  pedidoId: number,
  payload: TiempoFaseCreatePayload,
): Promise<TiempoFaseRead> {
  const { data } = await client.post<TiempoFaseRead>(
    `/pedidos-produccion/${pedidoId}/tiempos`,
    payload,
  )
  return data
}

export async function updateTiempoPedido(
  pedidoId: number,
  tiempoId: number,
  payload: TiempoFaseUpdatePayload,
): Promise<TiempoFaseRead> {
  const { data } = await client.patch<TiempoFaseRead>(
    `/pedidos-produccion/${pedidoId}/tiempos/${tiempoId}`,
    payload,
  )
  return data
}
