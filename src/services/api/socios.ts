/**
 * Socios API service — typed CRUD via shared axios client.
 * Base path: /finanzas/socios (client baseURL is /api/v1).
 * Mirrors backend schemas/finanzas.py (SocioConfiguracionCreate/Read) + SOC-2/3.
 */
import { client } from '@/api/client'

export interface SociaRead {
  id: number
  nombre: string
  porcentaje_participacion: number | string
  rol?: string | null
  banco?: string | null
  es_fondo_taller?: boolean | null
  telefono?: string | null
  email?: string | null
  tipo_cuenta?: string | null
  numero_cuenta?: string | null
  titular_cuenta?: string | null
  activo?: boolean | null
  notas?: string | null
}

export interface SociaCreatePayload {
  nombre: string
  porcentaje_participacion: number | string
  rol?: string | null
  banco?: string | null
  es_fondo_taller?: boolean
  telefono?: string | null
  email?: string | null
  tipo_cuenta?: 'AHORROS' | 'CORRIENTE' | 'OTRA' | null
  numero_cuenta?: string | null
  titular_cuenta?: string | null
  activo?: boolean
  notas?: string | null
}

export type SociaUpdatePayload = Partial<SociaCreatePayload>

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListSociosParams {
  activo?: boolean
  es_fondo_taller?: boolean
  rol?: string
  q?: string
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export async function listSocios(params: ListSociosParams = {}): Promise<Paginated<SociaRead>> {
  const { data } = await client.get<Paginated<SociaRead>>('/finanzas/socios', { params })
  return data
}

export async function getSocia(id: number): Promise<SociaRead> {
  const { data } = await client.get<SociaRead>(`/finanzas/socios/${id}`)
  return data
}

export async function createSocia(payload: SociaCreatePayload): Promise<SociaRead> {
  const { data } = await client.post<SociaRead>('/finanzas/socios', payload)
  return data
}

export async function updateSocia(id: number, payload: SociaUpdatePayload): Promise<SociaRead> {
  const { data } = await client.patch<SociaRead>(`/finanzas/socios/${id}`, payload)
  return data
}

export async function deleteSocia(id: number): Promise<void> {
  await client.delete(`/finanzas/socios/${id}`)
}
