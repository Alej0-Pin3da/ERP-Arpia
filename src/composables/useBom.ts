/**
 * useBom — REAL-only adapter over /api/v1/productos/:id/bom.
 *
 * BOM lines are nested under a producto, so every operation takes
 * `productoId` explicitly. Every operation delegates to
 * src/services/api/bom.ts (FastAPI + Postgres).
 * No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/bom'

export interface UseBomReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  listInsumos: (productoId: number) => Promise<api.BomInsumoRead[]>
  createInsumo: (productoId: number, payload: api.BomInsumoCreate) => Promise<api.BomInsumoRead>
  updateInsumo: (productoId: number, lineaId: number, payload: Partial<api.BomInsumoCreate>) => Promise<api.BomInsumoRead | null>
  removeInsumo: (productoId: number, lineaId: number) => Promise<void>
  getCosto: (productoId: number, varianteId?: number | null) => Promise<api.CostoProduccionRead>
  listCombos: (productoId: number) => Promise<api.BomProductoRead[]>
  createCombo: (productoId: number, payload: api.BomProductoCreate) => Promise<api.BomProductoRead>
  updateCombo: (productoId: number, lineaId: number, payload: Partial<api.BomProductoCreate>) => Promise<api.BomProductoRead>
  removeCombo: (productoId: number, lineaId: number) => Promise<void>
}

export function useBom(): UseBomReturn {
  const { isMock, mode } = useMode()

  async function listInsumos(productoId: number) {
    return api.listBomInsumos(productoId)
  }

  async function createInsumo(productoId: number, payload: api.BomInsumoCreate) {
    return api.createBomInsumo(productoId, payload)
  }

  async function updateInsumo(productoId: number, lineaId: number, payload: Partial<api.BomInsumoCreate>) {
    return api.updateBomInsumo(productoId, lineaId, payload)
  }

  async function removeInsumo(productoId: number, lineaId: number): Promise<void> {
    return api.deleteBomInsumo(productoId, lineaId)
  }

  async function getCosto(productoId: number, varianteId?: number | null) {
    return api.getCostoProduccion(productoId, varianteId)
  }

  async function listCombos(productoId: number) {
    return api.listBomProductos(productoId)
  }

  async function createCombo(productoId: number, payload: api.BomProductoCreate) {
    return api.createBomProducto(productoId, payload)
  }

  async function updateCombo(productoId: number, lineaId: number, payload: Partial<api.BomProductoCreate>) {
    return api.updateBomProducto(productoId, lineaId, payload)
  }

  async function removeCombo(productoId: number, lineaId: number): Promise<void> {
    return api.deleteBomProducto(productoId, lineaId)
  }

  return {
    isMock, mode,
    listInsumos, createInsumo, updateInsumo, removeInsumo, getCosto,
    listCombos, createCombo, updateCombo, removeCombo,
  }
}
