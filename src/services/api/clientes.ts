/**
 * Clientes API service — typed CRUD via shared axios client.
 * Base path: /clientes (client baseURL is /api/v1).
 * Mirrors backend schemas/cliente.py (ClienteCreate/Update/Read).
 */
import { client } from '@/api/client'

export interface ClienteRead {
  id: number
  nombre: string
  documento_identidad?: string | null
  email?: string | null
  telefono?: string | null
  ciudad?: string | null
  direccion?: string | null
  tipo?: string | null
  talla_habitual?: string | null
  talla_superior?: string | null
  talla_inferior?: string | null
  categoria_preferida?: string | null
  tipo_producto_frecuente?: string | null
  notas?: string | null
  medidas?: Record<string, unknown> | null
  created_at: string
}

export interface ClienteCreatePayload {
  nombre: string
  documento_identidad?: string | null
  email?: string | null
  telefono?: string | null
  ciudad?: string | null
  direccion?: string | null
  tipo?: string | null
  talla_habitual?: string | null
  talla_superior?: string | null
  talla_inferior?: string | null
  categoria_preferida?: string | null
  tipo_producto_frecuente?: string | null
  notas?: string | null
  medidas?: Record<string, unknown> | null
}

export type ClienteUpdatePayload = Partial<ClienteCreatePayload>

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListClientesParams {
  q?: string
  tipo?: string
  ciudad?: string
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export async function listClientes(params: ListClientesParams = {}): Promise<Paginated<ClienteRead>> {
  const { data } = await client.get<Paginated<ClienteRead>>('/clientes', { params })
  return data
}

export async function getCliente(id: number): Promise<ClienteRead> {
  const { data } = await client.get<ClienteRead>(`/clientes/${id}`)
  return data
}

export async function createCliente(payload: ClienteCreatePayload): Promise<ClienteRead> {
  const { data } = await client.post<ClienteRead>('/clientes', payload)
  return data
}

export async function updateCliente(id: number, payload: ClienteUpdatePayload): Promise<ClienteRead> {
  const { data } = await client.put<ClienteRead>(`/clientes/${id}`, payload)
  return data
}

export async function deleteCliente(id: number): Promise<void> {
  await client.delete(`/clientes/${id}`)
}
