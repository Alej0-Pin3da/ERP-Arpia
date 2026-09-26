/**
 * useCotizaciones — REAL-only adapter over /api/v1/cotizaciones.
 *
 * Quotes snapshot the Cotizador inputs server-side (the server recomputes
 * costo_total/precio_sugerido/ganancia_neta with the same math), so the
 * priced number survives beyond WhatsApp and can feed the product's
 * precio_venta_sugerido.
 */
import { client } from '@/api/client'

export type EstadoCotizacion = 'borrador' | 'enviada' | 'aprobada' | 'descartada'

export interface CotizacionCreatePayload {
  cliente_id?: number | null
  producto_id?: number | null
  nombre_prenda: string
  metros_tela?: number
  precio_metro_tela?: number
  metros_forro?: number
  precio_metro_forro?: number
  costo_avios?: number
  costo_empaque?: number
  tiempo_confeccion_min?: number
  tarifa_hora?: number
  costo_cif?: number
  margen_pct?: number
  desperdicio_pct?: number
  costo_hilo_m?: number
  metros_hilo?: number
  observaciones?: string | null
}

export interface CotizacionRead {
  id: number
  codigo?: string | null
  fecha: string
  cliente_id: number | null
  producto_id: number | null
  nombre_prenda: string
  metros_tela: string | number
  precio_metro_tela: string | number
  metros_forro: string | number
  precio_metro_forro: string | number
  costo_avios: string | number
  costo_empaque: string | number
  tiempo_confeccion_min: number
  tarifa_hora: string | number
  costo_cif: string | number
  margen_pct: string | number
  desperdicio_pct: string | number
  costo_hilo_m: string | number
  metros_hilo: string | number
  costo_total: string | number
  precio_sugerido: string | number
  ganancia_neta: string | number
  estado: string
  observaciones?: string | null
  creado_en: string
}

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface ListCotizacionesParams {
  cliente_id?: number
  producto_id?: number
  estado?: string
  q?: string
  limit?: number
  offset?: number
}

export async function listCotizaciones(params: ListCotizacionesParams = {}): Promise<Paginated<CotizacionRead>> {
  const { data } = await client.get<Paginated<CotizacionRead>>('/cotizaciones', { params })
  return data
}

export async function getCotizacion(id: number): Promise<CotizacionRead> {
  const { data } = await client.get<CotizacionRead>(`/cotizaciones/${id}`)
  return data
}

export async function createCotizacion(payload: CotizacionCreatePayload): Promise<CotizacionRead> {
  const { data } = await client.post<CotizacionRead>('/cotizaciones', payload)
  return data
}

export async function updateCotizacionEstado(id: number, estado: EstadoCotizacion): Promise<CotizacionRead> {
  const { data } = await client.patch<CotizacionRead>(`/cotizaciones/${id}/estado`, { estado })
  return data
}
