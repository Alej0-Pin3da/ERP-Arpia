/**
 * Anticipos API service — typed CRUD via shared axios client.
 * Base path: /finanzas/anticipos (client baseURL is /api/v1).
 * Mirrors backend schemas/finanzas.py Anticipo* + ANT-1/2/3.
 */
import { client } from '@/api/client'

export interface AnticipoRead {
  id: number
  socia_id: number
  socia_nombre?: string | null
  liquidacion_id?: number | null
  monto: number | string
  fecha: string
  estado: string
  concepto?: string | null
  metodo_desembolso?: string | null
  comprobante?: string | null
  observaciones?: string | null
  creado_en?: string | null
}

export interface AnticipoCreatePayload {
  socia_id: number
  monto: number | string
  fecha?: string | null
  concepto?: string | null
  metodo_desembolso?: string | null
  comprobante?: string | null
  observaciones?: string | null
}

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListAnticiposParams {
  socia_id?: number
  estado?: 'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO'
  limit?: number
  offset?: number
}

export async function listAnticipos(params: ListAnticiposParams = {}): Promise<Paginated<AnticipoRead>> {
  const { data } = await client.get<Paginated<AnticipoRead>>('/finanzas/anticipos', { params })
  return data
}

export async function createAnticipo(payload: AnticipoCreatePayload): Promise<AnticipoRead> {
  const { data } = await client.post<AnticipoRead>('/finanzas/anticipos', payload)
  return data
}

export async function descontarAnticipo(id: number, liquidacion_id: number): Promise<AnticipoRead> {
  const { data } = await client.patch<AnticipoRead>(`/finanzas/anticipos/${id}/descuento`, {
    liquidacion_id,
  })
  return data
}

export async function transitionAnticipo(
  id: number,
  payload: { estado: 'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO' },
): Promise<AnticipoRead> {
  const { data } = await client.patch<AnticipoRead>(`/finanzas/anticipos/${id}/estado`, payload)
  return data
}

export async function deleteAnticipo(id: number): Promise<void> {
  await client.delete(`/finanzas/anticipos/${id}`)
}
