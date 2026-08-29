import { client } from '@/api/client'

export interface DevolucionRead {
  id: number
  venta_id: number
  motivo?: string | null
  estado?: string | null
}

export interface Paginated<T> { items: T[]; total: number }

export async function listDevoluciones(params?: Record<string, unknown>): Promise<Paginated<DevolucionRead>> {
  const { data } = await client.get<Paginated<DevolucionRead>>('/devoluciones', { params })
  return data
}
