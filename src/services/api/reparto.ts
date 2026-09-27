/**
 * Automatic profit-split API service (V6 M2).
 * Live informational balances — the official settlement stays liquidación.
 */
import { client } from '@/api/client'

export interface ReglaRead {
  id: number
  cuenta_destino: string
  porcentaje: number | string
  activo: boolean
}

export interface SaldoRead {
  cuenta: string
  saldo: number | string
  actualizado_en: string
}

export interface RepartoVentaRead {
  venta_id: number
  cuenta: string
  monto: number | string
}

export async function listSaldos(): Promise<SaldoRead[]> {
  const { data } = await client.get<SaldoRead[]>('/reparto/saldos')
  return data
}

export async function listReglas(): Promise<ReglaRead[]> {
  const { data } = await client.get<ReglaRead[]>('/reparto/reglas')
  return data
}

export async function createRegla(payload: { cuenta_destino: string; porcentaje: number | string }): Promise<ReglaRead> {
  const { data } = await client.post<ReglaRead>('/reparto/reglas', payload)
  return data
}

export async function updateRegla(id: number, payload: { cuenta_destino?: string; porcentaje?: number | string; activo?: boolean }): Promise<ReglaRead> {
  const { data } = await client.patch<ReglaRead>(`/reparto/reglas/${id}`, payload)
  return data
}
