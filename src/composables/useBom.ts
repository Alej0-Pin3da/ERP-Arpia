/**
 * useBom — adapter that selects Pinia mock or real API based on useMode.
 *
 * BOM lines are nested under a producto, so every operation takes
 * `productoId` explicitly. When isMock is true, lines are read from
 * `atelier.recetas[].items` (in-memory); otherwise they delegate to
 * src/services/api/bom.ts (FastAPI + Postgres).
 */
import { useAtelierStore, type BomItem, type RecetaBOM } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/bom'

export interface UseBomReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  listInsumos: (productoId: number) => Promise<api.BomInsumoRead[] | BomItem[]>
  createInsumo: (productoId: number, payload: api.BomInsumoCreate) => Promise<api.BomInsumoRead | BomItem>
  updateInsumo: (productoId: number, lineaId: number, payload: Partial<api.BomInsumoCreate>) => Promise<api.BomInsumoRead | BomItem | null>
  removeInsumo: (productoId: number, lineaId: number) => Promise<void>
  getCosto: (productoId: number, varianteId?: number | null) => Promise<api.CostoProduccionRead | { total: number; lineas: BomItem[] }>
  listCombos: (productoId: number) => Promise<api.BomProductoRead[]>
  createCombo: (productoId: number, payload: api.BomProductoCreate) => Promise<api.BomProductoRead>
  updateCombo: (productoId: number, lineaId: number, payload: Partial<api.BomProductoCreate>) => Promise<api.BomProductoRead>
  removeCombo: (productoId: number, lineaId: number) => Promise<void>
}

function findReceta(atelier: ReturnType<typeof useAtelierStore>, productoId: number): RecetaBOM | undefined {
  return (atelier.recetas as unknown as RecetaBOM[]).find((r) => r.id === productoId)
}

export function useBom(): UseBomReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function listInsumos(productoId: number) {
    if (isMock.value) {
      return [...(findReceta(atelier, productoId)?.items ?? [])]
    }
    return api.listBomInsumos(productoId)
  }

  async function createInsumo(productoId: number, payload: api.BomInsumoCreate) {
    if (isMock.value) {
      const receta = findReceta(atelier, productoId)
      const items = receta?.items ?? []
      const nextId = Math.max(0, ...items.map((i) => i.insumo_id)) + 1
      const cantidad = Number(payload.cantidad_requerida ?? 0)
      const nuevo: BomItem = {
        id: nextId,
        insumo_id: nextId,
        nombre: `Insumo ${payload.insumo_id}`,
        tipo: 'Directo',
        consumo_unitario: cantidad,
        unidad: 'ud',
        merma_pct: Number(payload.porcentaje_desperdicio ?? 0),
        costo_unitario: 0,
        subtotal: 0,
      }
      items.push(nuevo)
      return nuevo
    }
    return api.createBomInsumo(productoId, payload)
  }

  async function updateInsumo(productoId: number, lineaId: number, payload: Partial<api.BomInsumoCreate>) {
    if (isMock.value) {
      const items = findReceta(atelier, productoId)?.items ?? []
      const row = items.find((i) => i.insumo_id === lineaId)
      if (!row) return null
      if (payload.cantidad_requerida !== undefined) row.consumo_unitario = Number(payload.cantidad_requerida)
      if (payload.porcentaje_desperdicio !== undefined) row.merma_pct = Number(payload.porcentaje_desperdicio)
      row.subtotal = row.consumo_unitario * row.costo_unitario * (1 + row.merma_pct / 100)
      return row
    }
    return api.updateBomInsumo(productoId, lineaId, payload)
  }

  async function removeInsumo(productoId: number, lineaId: number): Promise<void> {
    if (isMock.value) {
      const items = findReceta(atelier, productoId)?.items
      if (items) {
        const idx = items.findIndex((i) => i.insumo_id === lineaId)
        if (idx !== -1) items.splice(idx, 1)
      }
      return
    }
    return api.deleteBomInsumo(productoId, lineaId)
  }

  async function getCosto(productoId: number, varianteId?: number | null) {
    if (isMock.value) {
      const items = findReceta(atelier, productoId)?.items ?? []
      return { total: items.reduce((acc, i) => acc + Number(i.subtotal ?? 0), 0), lineas: items }
    }
    return api.getCostoProduccion(productoId, varianteId)
  }

  // Combos have no mock collection — the views guard `isMock` and never call
  // these in mock mode, so mock returns empty/echo without persisting.
  async function listCombos(productoId: number) {
    if (isMock.value) return []
    return api.listBomProductos(productoId)
  }

  async function createCombo(productoId: number, payload: api.BomProductoCreate) {
    if (isMock.value) {
      return { id: 0, combo_id: productoId, ...payload } as api.BomProductoRead
    }
    return api.createBomProducto(productoId, payload)
  }

  async function updateCombo(productoId: number, lineaId: number, payload: Partial<api.BomProductoCreate>) {
    if (isMock.value) {
      return { id: lineaId, combo_id: productoId, ...payload } as api.BomProductoRead
    }
    return api.updateBomProducto(productoId, lineaId, payload)
  }

  async function removeCombo(productoId: number, lineaId: number): Promise<void> {
    if (isMock.value) return
    return api.deleteBomProducto(productoId, lineaId)
  }

  return {
    isMock, mode,
    listInsumos, createInsumo, updateInsumo, removeInsumo, getCosto,
    listCombos, createCombo, updateCombo, removeCombo,
  }
}
