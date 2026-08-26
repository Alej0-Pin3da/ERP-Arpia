/**
 * useFinanzas — adapter that selects Pinia mock or real API based on useMode.
 *
 * Covers liquidaciones + anticipos (the finanzas v4 domains).
 * When isMock is true, operations run against src/stores/atelier.ts.
 * Otherwise they delegate to src/services/api/liquidaciones.ts + anticipos.ts.
 * Mirrors useClientes / useVentas; *.vue remain intact.
 */
import { useAtelierStore, type LiquidacionSocias, type AnticipoSocia } from '@/stores/atelier'
import { useMode } from './useMode'
import * as apiLiq from '@/services/api/liquidaciones'
import * as apiAnt from '@/services/api/anticipos'

export interface UseFinanzasReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  // liquidaciones
  listLiquidaciones: (
    params?: apiLiq.ListLiquidacionesParams,
  ) => Promise<apiLiq.Paginated<apiLiq.LiquidacionRead> | apiLiq.Paginated<LiquidacionSocias>>
  getLiquidacion: (id: number) => Promise<apiLiq.LiquidacionRead | LiquidacionSocias | null>
  createLiquidacion: (
    payload: apiLiq.LiquidacionCreatePayload,
  ) => Promise<apiLiq.LiquidacionRead | LiquidacionSocias>
  transitionLiquidacion: (
    id: number,
    payload: { estado: 'BORRADOR' | 'APROBADA' | 'PAGADA' },
  ) => Promise<apiLiq.LiquidacionRead | LiquidacionSocias | null>
  removeLiquidacion: (id: number) => Promise<void>
  // anticipos
  listAnticipos: (
    params?: apiAnt.ListAnticiposParams,
  ) => Promise<apiAnt.Paginated<apiAnt.AnticipoRead> | apiAnt.Paginated<AnticipoSocia>>
  createAnticipo: (payload: apiAnt.AnticipoCreatePayload) => Promise<apiAnt.AnticipoRead | AnticipoSocia>
  descontarAnticipo: (id: number, liquidacion_id: number) => Promise<apiAnt.AnticipoRead | AnticipoSocia | null>
  transitionAnticipo: (
    id: number,
    payload: { estado: 'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO' },
  ) => Promise<apiAnt.AnticipoRead | AnticipoSocia | null>
  removeAnticipo: (id: number) => Promise<void>
}

function toPaginatedLiquidaciones(
  list: LiquidacionSocias[],
  params: apiLiq.ListLiquidacionesParams = {},
): apiLiq.Paginated<LiquidacionSocias> {
  let filtered = [...list]
  if (params.estado) filtered = filtered.filter((l) => l.estado === params.estado)
  if (params.periodo) filtered = filtered.filter((l) => l.periodo === params.periodo)
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

function toPaginatedAnticipos(
  list: AnticipoSocia[],
  params: apiAnt.ListAnticiposParams = {},
): apiAnt.Paginated<AnticipoSocia> {
  let filtered = [...list]
  if (params.socia_id !== undefined) filtered = filtered.filter((a) => a.socia_id === params.socia_id)
  if (params.estado) filtered = filtered.filter((a) => a.estado === params.estado)
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function useFinanzas(): UseFinanzasReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  // ---- liquidaciones ----
  async function listLiquidaciones(params: apiLiq.ListLiquidacionesParams = {}) {
    if (isMock.value) {
      return toPaginatedLiquidaciones(atelier.liquidaciones as unknown as LiquidacionSocias[], params)
    }
    return apiLiq.listLiquidaciones(params)
  }

  async function getLiquidacion(id: number) {
    if (isMock.value) {
      return (atelier.liquidaciones.find((l) => l.id === id) as unknown as LiquidacionSocias) ?? null
    }
    try {
      return await apiLiq.getLiquidacion(id)
    } catch {
      return null
    }
  }

  async function createLiquidacion(payload: apiLiq.LiquidacionCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.liquidaciones.map((l) => l.id)) + 1
      const year = new Date(payload.fecha_cierre).getFullYear()
      const seq = String(atelier.liquidaciones.filter((l) => l.codigo.includes(String(year))).length + 1).padStart(2, '0')
      const codigo = `LIQ-${year}-${seq}`
      const nuevo: LiquidacionSocias = {
        id: nextId,
        codigo,
        periodo: payload.periodo,
        fecha_cierre: payload.fecha_cierre,
        total_ventas_brutas: Number(payload.total_ventas_brutas),
        costo_taller_insumos: Number(payload.costo_taller_insumos),
        gastos_operativos: Number(payload.gastos_operativos),
        utilidad_neta_total: Number(payload.utilidad_neta_total),
        fondo_reinversion_monto: Number(payload.fondo_reinversion_monto),
        utilidad_repartible: Number(payload.utilidad_repartible),
        estado: 'BORRADOR',
        distribucion: [],
        observaciones: payload.observaciones ?? undefined,
        created_at: new Date().toISOString(),
      }
      // naive distribution: split utilidad_repartible equally among active socias
      const activas = atelier.socias.filter((s) => s.activo)
      if (activas.length) {
        const repartible = Number(payload.utilidad_repartible)
        const suma = activas.reduce((a, s) => a + s.porcentaje, 0)
        nuevo.distribucion = activas.map((s) => ({
          socia_id: s.id,
          nombre_socia: s.nombre,
          rol_socia: s.rol,
          porcentaje: s.porcentaje,
          monto_bruto: Math.round((repartible * s.porcentaje) / suma),
          deduccion_anticipos: 0,
          monto_neto_pagar: Math.round((repartible * s.porcentaje) / suma),
          estado_pago: 'PENDIENTE' as const,
        }))
      }
      atelier.liquidaciones.unshift(nuevo as unknown as typeof atelier.liquidaciones[number])
      return nuevo
    }
    return apiLiq.createLiquidacion(payload)
  }

  async function transitionLiquidacion(id: number, payload: { estado: 'BORRADOR' | 'APROBADA' | 'PAGADA' }) {
    if (isMock.value) {
      const liq = atelier.liquidaciones.find((l) => l.id === id) as unknown as LiquidacionSocias | undefined
      if (!liq) return null
      // simple FSM enforce: BORRADOR->APROBADA->PAGADA only
      const valid: Record<string, string> = { BORRADOR: 'APROBADA', APROBADA: 'PAGADA' }
      if (valid[liq.estado] !== payload.estado) {
        throw new Error(`Transición inválida ${liq.estado} -> ${payload.estado}`)
      }
      liq.estado = payload.estado
      return liq
    }
    return apiLiq.transitionLiquidacion(id, payload)
  }

  async function removeLiquidacion(id: number): Promise<void> {
    if (isMock.value) {
      const idx = atelier.liquidaciones.findIndex((l) => l.id === id)
      if (idx !== -1) atelier.liquidaciones.splice(idx, 1)
      return
    }
    return apiLiq.deleteLiquidacion(id)
  }

  // ---- anticipos ----
  async function listAnticipos(params: apiAnt.ListAnticiposParams = {}) {
    if (isMock.value) {
      return toPaginatedAnticipos(atelier.anticipos as unknown as AnticipoSocia[], params)
    }
    return apiAnt.listAnticipos(params)
  }

  async function createAnticipo(payload: apiAnt.AnticipoCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.anticipos.map((a) => a.id)) + 1
      const soc = atelier.socias.find((s) => s.id === payload.socia_id)
      const nuevo: AnticipoSocia = {
        id: nextId,
        socia_id: payload.socia_id,
        nombre_socia: soc?.nombre ?? 'Socia Atelier',
        fecha: (payload.fecha as string) ?? new Date().toISOString().split('T')[0],
        monto: Number(payload.monto),
        concepto: (payload.concepto as string) ?? 'Adelanto a cuenta de utilidades',
        metodo_desembolso: (payload.metodo_desembolso as string) ?? 'Transferencia Bancaria',
        estado: 'PENDIENTE_DESCUENTO',
        liquidacion_id: null,
        comprobante: (payload.comprobante as string) ?? undefined,
        observaciones: payload.observaciones as string | undefined,
      }
      atelier.anticipos.unshift(nuevo as unknown as typeof atelier.anticipos[number])
      return nuevo
    }
    return apiAnt.createAnticipo(payload)
  }

  async function descontarAnticipo(id: number, liquidacion_id: number) {
    if (isMock.value) {
      const ant = atelier.anticipos.find((a) => a.id === id) as unknown as AnticipoSocia | undefined
      if (!ant) return null
      if (ant.estado !== 'PENDIENTE_DESCUENTO') throw new Error('El anticipo ya fue descontado')
      ant.estado = 'DESCONTADO'
      ant.liquidacion_id = liquidacion_id
      return ant
    }
    return apiAnt.descontarAnticipo(id, liquidacion_id)
  }

  async function transitionAnticipo(
    id: number,
    payload: { estado: 'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO' },
  ) {
    if (isMock.value) {
      const ant = atelier.anticipos.find((a) => a.id === id) as unknown as AnticipoSocia | undefined
      if (!ant) return null
      if (ant.estado !== 'PENDIENTE_DESCUENTO') throw new Error('Transición inválida')
      ant.estado = payload.estado
      return ant
    }
    return apiAnt.transitionAnticipo(id, payload)
  }

  async function removeAnticipo(id: number): Promise<void> {
    if (isMock.value) {
      const idx = atelier.anticipos.findIndex((a) => a.id === id)
      if (idx !== -1) atelier.anticipos.splice(idx, 1)
      return
    }
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
