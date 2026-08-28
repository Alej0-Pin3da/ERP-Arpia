/**
 * Prendas Confeccionadas API service — typed CRUD via shared axios client.
 * Base path: /prendas-confeccionadas (client baseURL is /api/v1).
 * Mirrors backend schemas/produccion.py (PrendaConfeccionadaCreate/Update/Read).
 */
import { client } from '@/api/client'

export interface PrendaRead {
  id: number
  variante_id: number
  talla?: string | null
  estado: string
  ubicacion?: string | null
  costo_real?: number | null
  precio_venta?: number | null
  fecha_confeccion?: string | null
  pedido_id?: number | null
  created_at: string
  updated_at: string
  nombre_producto?: string | null
  nombre_variante?: string | null
}

export interface PrendaCreatePayload {
  variante_id: number
  talla?: string | null
  estado?: string
  ubicacion?: string | null
  costo_real?: number | null
  precio_venta?: number | null
  fecha_confeccion?: string | null
  pedido_id?: number | null
}

export type PrendaUpdatePayload = Partial<PrendaCreatePayload>

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListPrendasParams {
  q?: string
  variante_id?: number
  estado?: string
  talla?: string
  ubicacion?: string
  pedido_id?: number
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export async function listPrendas(params?: ListPrendasParams): Promise<Paginated<PrendaRead>> {
  const { data } = await client.get<Paginated<PrendaRead>>('/prendas-confeccionadas', { params })
  return data
}

export async function getPrenda(id: number): Promise<PrendaRead> {
  const { data } = await client.get<PrendaRead>(`/prendas-confeccionadas/${id}`)
  return data
}

export async function createPrenda(payload: PrendaCreatePayload): Promise<PrendaRead> {
  const { data } = await client.post<PrendaRead>('/prendas-confeccionadas', payload)
  return data
}

export async function updatePrenda(id: number, payload: PrendaUpdatePayload): Promise<PrendaRead> {
  const { data } = await client.patch<PrendaRead>(`/prendas-confeccionadas/${id}`, payload)
  return data
}

export async function deletePrenda(id: number): Promise<void> {
  await client.delete(`/prendas-confeccionadas/${id}`)
}
