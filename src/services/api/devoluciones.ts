import { client } from '@/api/client'

export interface DevolucionRead {
  id: number
  venta_id: number
  motivo?: string | null
  estado?: string | null
}

export interface DevolucionItemCreate {
  producto_id: number
  variante_id?: number | null
  cantidad: number | string
  precio_unitario: number | string
}

export interface DevolucionCreatePayload {
  venta_id: number
  tipo: 'total' | 'parcial'
  motivo?: string | null
  items?: DevolucionItemCreate[] | null
}

export interface DevolucionStateTransition {
  estado: 'draft' | 'confirmed' | 'cancelled' | 'reversed'
  motivo?: string | null
}

export interface Paginated<T> { items: T[]; total: number }

export async function listDevoluciones(params?: Record<string, unknown>): Promise<Paginated<DevolucionRead>> {
  const { data } = await client.get<Paginated<DevolucionRead>>('/devoluciones', { params })
  return data
}

export async function createDevolucion(payload: DevolucionCreatePayload): Promise<DevolucionRead> {
  const { data } = await client.post<DevolucionRead>('/devoluciones', payload)
  return data
}

export async function transitionDevolucion(id: number, payload: DevolucionStateTransition): Promise<DevolucionRead> {
  const { data } = await client.patch<DevolucionRead>(`/devoluciones/${id}/state`, payload)
  return data
}
