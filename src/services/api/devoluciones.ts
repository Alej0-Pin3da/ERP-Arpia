import { client } from '@/api/client'

export interface DevolucionRead {
  id: number
  venta_id: number
  motivo?: string | null
  estado?: string | null
  // Referencia de venta resuelta por el backend (mapper _devolucion_to_read).
  cliente_nombre?: string | null
  prenda_nombre?: string | null
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

export interface DevolucionUpdatePayload {
  motivo?: string | null
  estado?: 'draft' | 'confirmed' | 'cancelled' | 'reversed'
}

export async function getDevolucion(id: number): Promise<DevolucionRead> {
  const { data } = await client.get<DevolucionRead>(`/devoluciones/${id}`)
  return data
}

export async function updateDevolucion(id: number, payload: DevolucionUpdatePayload): Promise<DevolucionRead> {
  const { data } = await client.put<DevolucionRead>(`/devoluciones/${id}`, payload)
  return data
}

export async function deleteDevolucion(id: number): Promise<void> {
  await client.delete(`/devoluciones/${id}`)
}
