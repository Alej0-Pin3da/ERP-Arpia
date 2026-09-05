/**
 * Insumos API service — typed CRUD via shared axios client.
 * Base path: /insumos (client baseURL is /api/v1).
 * Mirrors backend schemas/insumo.py (InsumoCreate/Update/Read).
 */
import { client } from '@/api/client'

export interface InsumoRead {
  id: number
  categoria_id: number
  nombre: string
  unidad_medida: string
  codigo?: string | null
  descripcion?: string | null
  tipo?: string | null
  ubicacion?: string | null
  stock_actual: number | string
  stock_minimo: number | string
  costo_promedio_actual: number | string
  nombre_categoria?: string | null
}

export interface InsumoCreatePayload {
  categoria_id: number
  nombre: string
  unidad_medida: string
  codigo?: string | null
  descripcion?: string | null
  tipo?: string | null
  ubicacion?: string | null
  stock_actual?: number
  stock_minimo?: number
  costo_promedio_actual?: number
}

export type InsumoUpdatePayload = Partial<InsumoCreatePayload>

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListInsumosParams {
  q?: string
  categoria_id?: number
  tipo?: string
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export async function listInsumos(params?: ListInsumosParams): Promise<Paginated<InsumoRead>> {
  const { data } = await client.get<Paginated<InsumoRead>>('/insumos', { params })
  return data
}

export async function getInsumo(id: number): Promise<InsumoRead> {
  const { data } = await client.get<InsumoRead>(`/insumos/${id}`)
  return data
}

export async function createInsumo(payload: InsumoCreatePayload): Promise<InsumoRead> {
  const { data } = await client.post<InsumoRead>('/insumos', payload)
  return data
}

export async function updateInsumo(id: number, payload: InsumoUpdatePayload): Promise<InsumoRead> {
  const { data } = await client.patch<InsumoRead>(`/insumos/${id}`, payload)
  return data
}

export async function deleteInsumo(id: number): Promise<void> {
  await client.delete(`/insumos/${id}`)
}
