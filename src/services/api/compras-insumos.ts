import { client } from '@/api/client'

export interface CompraInsumoRead {
  id: number
  insumo_id: number
  cantidad_comprada: number
  precio_unitario_compra: number
}

export interface CompraInsumoCreatePayload {
  insumo_id: number
  cantidad_comprada: number
  precio_unitario_compra: number
  costo_total?: number
  modo?: string
  factura?: string | null
  proveedor_id?: number | null
}

export interface Paginated<T> { items: T[]; total: number }

export async function createCompraInsumo(payload: CompraInsumoCreatePayload): Promise<CompraInsumoRead> {
  const { data } = await client.post<CompraInsumoRead>('/compras-insumos', payload)
  return data
}

export async function listComprasInsumos(params?: Record<string, unknown>): Promise<Paginated<CompraInsumoRead>> {
  const { data } = await client.get<Paginated<CompraInsumoRead>>('/compras-insumos', { params })
  return data
}
