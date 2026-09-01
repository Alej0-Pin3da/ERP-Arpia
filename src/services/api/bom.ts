import { client } from '@/api/client'

export interface BomInsumoRead {
  id: number
  producto_id: number
  insumo_id: number
  variante_id: number | null
  cantidad_requerida: number | string
  porcentaje_desperdicio: number | string
  fases?: unknown | null
  tiempo_estimado_minutos?: number | null
  markup_porcentual?: number | string | null
}

export interface BomInsumoCreate {
  insumo_id: number
  variante_id?: number | null
  cantidad_requerida: number | string
  porcentaje_desperdicio?: number | string
  fases?: unknown | null
  tiempo_estimado_minutos?: number | null
  markup_porcentual?: number | string | null
}

export interface CostoLineaRead {
  tipo: string
  id: number
  nombre: string
  cantidad: number | string
  costo_unitario: number | string
  costo_total: number | string
}

export interface CostoProduccionRead {
  total: number | string
  lineas: CostoLineaRead[]
}

export async function listBomInsumos(productoId: number): Promise<BomInsumoRead[]> {
  const { data } = await client.get<BomInsumoRead[]>(`/productos/${productoId}/bom/insumos`)
  return data
}

export async function createBomInsumo(productoId: number, payload: BomInsumoCreate): Promise<BomInsumoRead> {
  const { data } = await client.post<BomInsumoRead>(`/productos/${productoId}/bom/insumos`, payload)
  return data
}

export async function updateBomInsumo(productoId: number, lineaId: number, payload: Partial<BomInsumoCreate>): Promise<BomInsumoRead> {
  const { data } = await client.put<BomInsumoRead>(`/productos/${productoId}/bom/insumos/${lineaId}`, payload)
  return data
}

export async function deleteBomInsumo(productoId: number, lineaId: number): Promise<void> {
  await client.delete(`/productos/${productoId}/bom/insumos/${lineaId}`)
}

export async function getCostoProduccion(productoId: number, varianteId?: number | null): Promise<CostoProduccionRead> {
  const params: Record<string, unknown> = {}
  if (varianteId != null) params.variante_id = varianteId
  const { data } = await client.get<CostoProduccionRead>(`/productos/${productoId}/costo`, { params })
  return data
}
