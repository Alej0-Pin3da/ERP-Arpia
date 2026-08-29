import { client } from '@/api/client'

export interface OmisionRead {
  id: number
  mensaje: string
  fase?: string | null
  nivel?: string | null
  hoja?: string | null
  resuelta?: boolean
  creado_en?: string
}

export interface Paginated<T> { items: T[]; total: number }

export async function listOmisiones(params?: Record<string, unknown>): Promise<Paginated<OmisionRead>> {
  const { data } = await client.get<Paginated<OmisionRead>>('/omisiones', { params })
  return data
}
