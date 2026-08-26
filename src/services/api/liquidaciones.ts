/**
 * Liquidaciones API service — typed CRUD via shared axios client.
 * Base path: /finanzas/liquidaciones (client baseURL is /api/v1).
 * Mirrors backend schemas/finanzas.py Liquidacion* + LIQ-1/2/3.
 */
import { client } from '@/api/client'

export interface LiquidacionDistribucionRead {
  id: number
  liquidacion_id: number
  socia_id: number
  socia_nombre?: string | null
  porcentaje: number | string
  monto_bruto: number | string
  deduccion_anticipos: number | string
  monto_neto: number | string
  estado_pago: string
}

export interface LiquidacionRead {
  id: number
  codigo: string
  periodo: string
  fecha_cierre: string
  total_ventas_brutas: number | string
  costo_taller_insumos: number | string
  gastos_operativos: number | string
  utilidad_neta_total: number | string
  fondo_reinversion_monto: number | string
  utilidad_repartible: number | string
  estado: string
  observaciones?: string | null
  distribucion: LiquidacionDistribucionRead[]
  warnings: string[]
}

export interface LiquidacionCreatePayload {
  periodo: string
  fecha_cierre: string
  total_ventas_brutas: number | string
  costo_taller_insumos: number | string
  gastos_operativos: number | string
  utilidad_neta_total: number | string
  fondo_reinversion_monto: number | string
  utilidad_repartible: number | string
  observaciones?: string | null
}

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListLiquidacionesParams {
  estado?: 'BORRADOR' | 'APROBADA' | 'PAGADA'
  periodo?: string
  limit?: number
  offset?: number
}

export async function listLiquidaciones(
  params: ListLiquidacionesParams = {},
): Promise<Paginated<LiquidacionRead>> {
  const { data } = await client.get<Paginated<LiquidacionRead>>('/finanzas/liquidaciones', { params })
  return data
}

export async function getLiquidacion(id: number): Promise<LiquidacionRead> {
  const { data } = await client.get<LiquidacionRead>(`/finanzas/liquidaciones/${id}`)
  return data
}

export async function createLiquidacion(payload: LiquidacionCreatePayload): Promise<LiquidacionRead> {
  const { data } = await client.post<LiquidacionRead>('/finanzas/liquidaciones/crear', payload)
  return data
}

export async function transitionLiquidacion(
  id: number,
  payload: { estado: 'BORRADOR' | 'APROBADA' | 'PAGADA' },
): Promise<LiquidacionRead> {
  const { data } = await client.patch<LiquidacionRead>(`/finanzas/liquidaciones/${id}/estado`, payload)
  return data
}

export async function deleteLiquidacion(id: number): Promise<void> {
  await client.delete(`/finanzas/liquidaciones/${id}`)
}
