/**
 * Ventas API service — typed CRUD via shared axios client.
 * Base path: /ventas (client baseURL is /api/v1).
 * Mirrors backend schemas/venta.py (VentaCreate/Read).
 */
import { client } from '@/api/client'

export type CanalVenta = 'web' | 'whatsapp' | 'instagram' | 'feria' | 'showroom_pereira'
export type MetodoPago = 'efectivo' | 'transferencia' | 'tarjeta' | 'contraentrega'
// P1-6 (0024): canal/metodo accept any maestro-defined codigo, not just the
// canonical unions above — backend validates membership + FK enforces it.
export type CanalVentaInput = CanalVenta | string
export type MetodoPagoInput = MetodoPago | string

export interface DetalleVentaCreate {
  producto_id: number
  variante_id?: number | null
  cantidad: number | string
  precio_unitario: number | string
}

export interface VentaCreatePayload {
  cliente_id?: number | null
  canal_venta: CanalVentaInput
  metodo_pago?: MetodoPagoInput | null
  descuento_porcentaje?: number | string
  es_regalo?: boolean
  detalles: DetalleVentaCreate[]
}

export interface DetalleVentaRead {
  id: number
  producto_id: number
  variante_id: number | null
  cantidad: string | number
  precio_unitario_aplicado: string | number
  costo_unitario_aplicado: string | number
  nombre_prenda?: string | null
  talla?: string | null
  nombre_variante?: string | null
  color?: string | null
  subtotal?: string | number | null
  costo_subtotal?: string | number | null
}

export interface VentaRead {
  id: number
  fecha: string
  cliente_id: number | null
  cliente_nombre?: string | null
  codigo?: string | null
  canal_venta: string
  metodo_pago: string | null
  descuento_porcentaje: string | number
  estado: string
  total_venta: string | number
  subtotal?: string | number | null
  costo_total?: string | number | null
  ganancia_neta?: string | number | null
  margen_pct?: string | number | null
  reinversion_40?: string | number | null
  margarita_30?: string | number | null
  valqui_30?: string | number | null
  es_regalo: boolean
  detalles: DetalleVentaRead[]
}

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListVentasParams {
  canal_venta?: CanalVentaInput
  estado?: string
  producto_id?: number
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
}

export async function listVentas(params: ListVentasParams = {}): Promise<Paginated<VentaRead>> {
  const { data } = await client.get<Paginated<VentaRead>>('/ventas', { params })
  return data
}

export async function getVenta(id: number): Promise<VentaRead> {
  const { data } = await client.get<VentaRead>(`/ventas/${id}`)
  return data
}

export async function createVenta(payload: VentaCreatePayload): Promise<VentaRead> {
  const { data } = await client.post<VentaRead>('/ventas', payload)
  return data
}

export async function updateVenta(id: number, payload: VentaCreatePayload): Promise<VentaRead> {
  const { data } = await client.put<VentaRead>(`/ventas/${id}`, payload)
  return data
}

export async function anularVenta(id: number): Promise<VentaRead> {
  const { data } = await client.delete<VentaRead>(`/ventas/${id}`)
  return data
}
