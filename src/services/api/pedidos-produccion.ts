/**
 * Pedidos de Producción API service — typed CRUD via shared axios client.
 * Base path: /pedidos-produccion (client baseURL is /api/v1).
 * Mirrors backend schemas/produccion.py (PedidoProduccionCreate/Update/Read).
 */
import { client } from '@/api/client'

export interface PedidoProduccionRead {
  id: number
  producto_id: number
  variante_id?: number | null
  cantidad: number
  cantidad_producida: number
  estado: string
  prioridad: string
  fecha_pedido: string
  fecha_entrega_estimada?: string | null
  observaciones?: string | null
  created_at: string
  updated_at: string
  nombre_producto?: string | null
  nombre_variante?: string | null
}

export interface PedidoProduccionCreatePayload {
  producto_id: number
  variante_id?: number | null
  cantidad: number
  cantidad_producida?: number
  estado?: string
  prioridad?: string
  fecha_pedido?: string
  fecha_entrega_estimada?: string | null
  observaciones?: string | null
}

export type PedidoProduccionUpdatePayload = Partial<PedidoProduccionCreatePayload>

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListPedidosProduccionParams {
  q?: string
  producto_id?: number
  variante_id?: number
  estado?: string
  prioridad?: string
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
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
