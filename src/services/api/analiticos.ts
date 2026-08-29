import { client as apiClient } from '@/api/client'

export interface VentasMensuales { mes: string; total: number; count: number }
export interface InsumoBajoStock { id: number; nombre: string; stock_actual: number; stock_minimo: number }

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
export async function getFinanzasMensuales(params?: { desde?: string; hasta?: string }) {
  const { data } = await apiClient.get('/analiticos/finanzas-mensuales', { params })
  return data
}
