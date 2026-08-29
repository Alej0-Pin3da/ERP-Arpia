import { client } from '@/api/client'

export interface ProductoRead {
  id: number
  nombre: string
  tipo_producto_id?: number | null
  requiere_fabricacion?: boolean
  precio_venta_sugerido?: number
  costos_operativos_fijos?: number
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
