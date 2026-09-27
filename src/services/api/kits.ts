/**
 * Kits API service — promotional boxes over live product costs (V6 M1).
 * Every read carries a live cost snapshot; the margin alert is visual.
 */
import { client } from '@/api/client'

export interface KitLineaCreate {
  producto_id: number
  cantidad?: number | string
}

export interface KitLineaRead {
  id: number
  producto_id: number
  producto_nombre?: string | null
  cantidad: number | string
  costo_unitario: number | string
  subtotal: number | string
}

export interface KitRead {
  id: number
  nombre: string
  precio_promocional: number | string
  activo: boolean
  costo_total: number | string
  margen_pct: number | string
  alerta_margen: boolean
  lineas: KitLineaRead[]
}

export interface Paginated<T> {
  items: T[]
  total: number
}

export async function listKits(params: { q?: string; limit?: number; offset?: number } = {}): Promise<Paginated<KitRead>> {
  const { data } = await client.get<Paginated<KitRead>>('/kits', { params })
  return data
}

export async function getKit(id: number): Promise<KitRead> {
  const { data } = await client.get<KitRead>(`/kits/${id}`)
  return data
}

export async function createKit(payload: { nombre: string; precio_promocional: number | string; lineas?: KitLineaCreate[] }): Promise<KitRead> {
  const { data } = await client.post<KitRead>('/kits', payload)
  return data
}

export async function updateKit(id: number, payload: { nombre?: string; precio_promocional?: number | string; activo?: boolean }): Promise<KitRead> {
  const { data } = await client.patch<KitRead>(`/kits/${id}`, payload)
  return data
}

export async function deleteKit(id: number): Promise<void> {
  await client.delete(`/kits/${id}`)
}

export async function addKitLinea(kitId: number, payload: KitLineaCreate): Promise<KitRead> {
  const { data } = await client.post<KitRead>(`/kits/${kitId}/lineas`, payload)
  return data
}

export async function removeKitLinea(kitId: number, lineaId: number): Promise<void> {
  await client.delete(`/kits/${kitId}/lineas/${lineaId}`)
}
