import { client } from '@/api/client'

export interface ProductoRead {
  id: number
  nombre: string
  tipo_producto_id: number
  requiere_fabricacion: boolean
  precio_venta_sugerido: number | string
  costos_operativos_fijos: number | string
  codigo?: string | null
  categoria?: string | null
  linea?: string | null
  descripcion?: string | null
  tiempo_confeccion_min?: number | null
  costo_insumos?: number | string | null
  mano_obra?: number | string | null
  cif_energia?: number | string | null
  markup_pct?: number | string | null
  recomendaciones_taller?: string | null
  fases?: unknown | null
}

export interface ProductoCreate {
  tipo_producto_id: number
  nombre: string
  requiere_fabricacion?: boolean
  precio_venta_sugerido?: number | string
  costos_operativos_fijos?: number | string
  codigo?: string | null
  categoria?: string | null
  linea?: string | null
  descripcion?: string | null
  tiempo_confeccion_min?: number | null
  costo_insumos?: number | string | null
  mano_obra?: number | string | null
  cif_energia?: number | string | null
  markup_pct?: number | string | null
  recomendaciones_taller?: string | null
  fases?: unknown | null
}

export interface ProductoUpdate {
  tipo_producto_id?: number
  nombre?: string
  requiere_fabricacion?: boolean
  precio_venta_sugerido?: number | string
  costos_operativos_fijos?: number | string
  codigo?: string | null
  categoria?: string | null
  linea?: string | null
  descripcion?: string | null
  tiempo_confeccion_min?: number | null
  costo_insumos?: number | string | null
  mano_obra?: number | string | null
  cif_energia?: number | string | null
  markup_pct?: number | string | null
  recomendaciones_taller?: string | null
  fases?: unknown | null
}

export interface TipoProductoRead {
  id: number
  nombre: string
}

export interface Paginated<T> { items: T[]; total: number }

export interface ListProductosParams {
  q?: string
  tipo_producto_id?: number
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export async function listProductos(params?: ListProductosParams): Promise<Paginated<ProductoRead>> {
  const { data } = await client.get<Paginated<ProductoRead>>('/productos', { params })
  return data
}

export async function getProducto(id: number): Promise<ProductoRead> {
  const { data } = await client.get<ProductoRead>(`/productos/${id}`)
  return data
}

export async function createProducto(payload: ProductoCreate): Promise<ProductoRead> {
  const { data } = await client.post<ProductoRead>('/productos', payload)
  return data
}

export async function updateProducto(id: number, payload: ProductoUpdate): Promise<ProductoRead> {
  const { data } = await client.put<ProductoRead>(`/productos/${id}`, payload)
  return data
}

export async function deleteProducto(id: number): Promise<void> {
  await client.delete(`/productos/${id}`)
}

export async function listTiposProducto(params?: { q?: string; limit?: number; offset?: number }): Promise<Paginated<TipoProductoRead>> {
  const { data } = await client.get<Paginated<TipoProductoRead>>('/tipos-producto', { params })
  return data
}
