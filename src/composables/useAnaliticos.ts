/**
 * useAnaliticos — thin adapter over src/services/api/analiticos.ts.
 *
 * The analiticos endpoints are read-only server aggregations with no mock
 * equivalent: in mock mode the views compute KPIs locally from atelier lists,
 * so every getter resolves to `null` when isMock is true. In REAL mode each
 * getter delegates to the backend and rejects on error, letting the caller
 * fall back to its local computation.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/analiticos'

export interface PeriodoParams {
  desde?: string
  hasta?: string
}

export interface UseAnaliticosReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  getResumen: (params?: PeriodoParams) => Promise<api.AnaliticosResumen | null>
  getVentasMensuales: (params?: PeriodoParams) => Promise<api.VentasMensuales[] | null>
  getInsumosBajoStock: () => Promise<api.InsumoBajoStock[] | null>
  getMargenPorProducto: () => Promise<unknown>
  getTopProductos: () => Promise<unknown>
  getTopInsumos: (params?: PeriodoParams) => Promise<unknown>
  getFinanzasMensuales: (params?: PeriodoParams) => Promise<unknown>
}

export function useAnaliticos(): UseAnaliticosReturn {
  const { isMock, mode } = useMode()

  async function getResumen(params?: PeriodoParams) {
    if (isMock.value) return null
    return api.getResumen(params)
  }

  async function getVentasMensuales(params?: PeriodoParams) {
    if (isMock.value) return null
    return api.getVentasMensuales(params) as Promise<api.VentasMensuales[]>
  }

  async function getInsumosBajoStock() {
    if (isMock.value) return null
    return api.getInsumosBajoStock()
  }

  async function getMargenPorProducto() {
    if (isMock.value) return null
    return api.getMargenPorProducto()
  }

  async function getTopProductos() {
    if (isMock.value) return null
    return api.getTopProductos()
  }

  async function getTopInsumos(params?: PeriodoParams) {
    if (isMock.value) return null
    return api.getTopInsumos(params)
  }

  async function getFinanzasMensuales(params?: PeriodoParams) {
    if (isMock.value) return null
    return api.getFinanzasMensuales(params)
  }

  return {
    isMock, mode,
    getResumen, getVentasMensuales, getInsumosBajoStock,
    getMargenPorProducto, getTopProductos, getTopInsumos, getFinanzasMensuales,
  }
}
