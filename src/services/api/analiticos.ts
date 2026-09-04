import { client as apiClient } from '@/api/client'

export interface VentasMensuales { mes: string; total: number; count: number }
export interface InsumoBajoStock { id: number; nombre: string; stock_actual: number; stock_minimo: number }

export interface AnaliticosResumen {
  desde: string
  hasta: string
  ventas_total: number
  cantidad_ventas: number
  unidades_vendidas: number
  ticket_promedio: number
  margen_total: number
  gastos_total: number
  resultado_neto: number
}

export async function getResumen(params?: { desde?: string; hasta?: string }) {
  const { data } = await apiClient.get('/analiticos/resumen', { params })
  return data as AnaliticosResumen
}
export async function getVentasMensuales(params?: { desde?: string; hasta?: string }) {
  const { data } = await apiClient.get('/analiticos/ventas-mensuales', { params })
  return data
}
export async function getInsumosBajoStock() {
  const { data } = await apiClient.get('/analiticos/insumos-bajo-stock')
  return data as InsumoBajoStock[]
}
export async function getMargenPorProducto() {
  const { data } = await apiClient.get('/analiticos/margen-por-producto')
  return data
}
export async function getTopProductos() {
  const { data } = await apiClient.get('/analiticos/top-productos')
  return data
}
// P2-8: minimal — mirrors GET /analiticos/top-insumos.
export async function getTopInsumos(params?: { desde?: string; hasta?: string }) {
  const { data } = await apiClient.get('/analiticos/top-insumos', { params })
  return data
}
export async function getFinanzasMensuales(params?: { desde?: string; hasta?: string }) {
  const { data } = await apiClient.get('/analiticos/finanzas-mensuales', { params })
  return data
}
