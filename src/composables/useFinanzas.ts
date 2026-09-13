/**
 * useFinanzas — REAL-only adapter over liquidaciones + anticipos.
 *
 * Every operation delegates to src/services/api/liquidaciones.ts +
 * anticipos.ts (FastAPI + Postgres). No in-memory mock path remains.
 */
import { useMode } from './useMode'
import * as apiLiq from '@/services/api/liquidaciones'
import * as apiAnt from '@/services/api/anticipos'

export interface UseFinanzasReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  // liquidaciones
  listLiquidaciones: (
    params?: apiLiq.ListLiquidacionesParams,
  ) => Promise<apiLiq.Paginated<apiLiq.LiquidacionRead>>
  getLiquidacion: (id: number) => Promise<apiLiq.LiquidacionRead | null>
  createLiquidacion: (
    payload: apiLiq.LiquidacionCreatePayload,
  ) => Promise<apiLiq.LiquidacionRead>
  transitionLiquidacion: (
    id: number,
    payload: { estado: 'BORRADOR' | 'APROBADA' | 'PAGADA' },
  ) => Promise<apiLiq.LiquidacionRead | null>
  removeLiquidacion: (id: number) => Promise<void>
  // anticipos
  listAnticipos: (
    params?: apiAnt.ListAnticiposParams,
  ) => Promise<apiAnt.Paginated<apiAnt.AnticipoRead>>
  createAnticipo: (payload: apiAnt.AnticipoCreatePayload) => Promise<apiAnt.AnticipoRead>
  descontarAnticipo: (id: number, liquidacion_id: number) => Promise<apiAnt.AnticipoRead | null>
  transitionAnticipo: (
    id: number,
    payload: { estado: 'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO' },
  ) => Promise<apiAnt.AnticipoRead | null>
  removeAnticipo: (id: number) => Promise<void>
}

export function useFinanzas(): UseFinanzasReturn {
  const { isMock, mode } = useMode()

  // ---- liquidaciones ----
  async function listLiquidaciones(params: apiLiq.ListLiquidacionesParams = {}) {
    return apiLiq.listLiquidaciones(params)
  }

  async function getLiquidacion(id: number) {
    try {
      return await apiLiq.getLiquidacion(id)
    } catch {
      return null
    }
  }

  async function createLiquidacion(payload: apiLiq.LiquidacionCreatePayload) {
    return apiLiq.createLiquidacion(payload)
  }

  async function transitionLiquidacion(id: number, payload: { estado: 'BORRADOR' | 'APROBADA' | 'PAGADA' }) {
    return apiLiq.transitionLiquidacion(id, payload)
  }

  async function removeLiquidacion(id: number): Promise<void> {
    return apiLiq.deleteLiquidacion(id)
  }

  // ---- anticipos ----
  async function listAnticipos(params: apiAnt.ListAnticiposParams = {}) {
    return apiAnt.listAnticipos(params)
  }

  async function createAnticipo(payload: apiAnt.AnticipoCreatePayload) {
    return apiAnt.createAnticipo(payload)
  }

  async function descontarAnticipo(id: number, liquidacion_id: number) {
    return apiAnt.descontarAnticipo(id, liquidacion_id)
  }

  async function transitionAnticipo(
    id: number,
    payload: { estado: 'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO' },
  ) {
    return apiAnt.transitionAnticipo(id, payload)
  }

  async function removeAnticipo(id: number): Promise<void> {
    return apiAnt.deleteAnticipo(id)
  }

  return {
    isMock,
    mode,
    listLiquidaciones,
    getLiquidacion,
    createLiquidacion,
    transitionLiquidacion,
    removeLiquidacion,
    listAnticipos,
    createAnticipo,
    descontarAnticipo,
    transitionAnticipo,
    removeAnticipo,
  }
}
