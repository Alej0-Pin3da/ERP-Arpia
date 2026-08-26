import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAtelierStore } from '@/stores/atelier'

vi.mock('@/services/api/liquidaciones', () => ({
  listLiquidaciones: vi.fn().mockResolvedValue({ items: [{ id: 99, codigo: 'LIQ-2026-01', periodo: '2026-07', estado: 'BORRADOR', distribucion: [], warnings: [] }], total: 1 }),
  getLiquidacion: vi.fn().mockResolvedValue({ id: 99, codigo: 'LIQ-2026-01', estado: 'BORRADOR', distribucion: [], warnings: [] }),
  createLiquidacion: vi.fn().mockResolvedValue({ id: 100, codigo: 'LIQ-2026-02', periodo: '2026-08', estado: 'BORRADOR', distribucion: [], warnings: [] }),
  transitionLiquidacion: vi.fn().mockResolvedValue({ id: 99, codigo: 'LIQ-2026-01', estado: 'APROBADA', distribucion: [], warnings: [] }),
  deleteLiquidacion: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('@/services/api/anticipos', () => ({
  listAnticipos: vi.fn().mockResolvedValue({ items: [{ id: 99, socia_id: 2, monto: 50000, fecha: '2026-07-10', estado: 'PENDIENTE_DESCUENTO' }], total: 1 }),
  createAnticipo: vi.fn().mockResolvedValue({ id: 100, socia_id: 2, monto: 50000, fecha: '2026-07-11', estado: 'PENDIENTE_DESCUENTO' }),
  descontarAnticipo: vi.fn().mockResolvedValue({ id: 99, socia_id: 2, monto: 50000, estado: 'DESCONTADO', liquidacion_id: 99 }),
  transitionAnticipo: vi.fn().mockResolvedValue({ id: 99, socia_id: 2, estado: 'ANULADO' }),
  deleteAnticipo: vi.fn().mockResolvedValue(undefined),
}))

import * as apiLiq from '@/services/api/liquidaciones'
import * as apiAnt from '@/services/api/anticipos'
import { useFinanzas } from './useFinanzas'

describe('useFinanzas', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.mocked(apiLiq.listLiquidaciones).mockResolvedValue({ items: [{ id: 99, codigo: 'LIQ-2026-01', periodo: '2026-07', estado: 'BORRADOR', distribucion: [], warnings: [] } as unknown as apiLiq.LiquidacionRead], total: 1 })
    vi.mocked(apiLiq.getLiquidacion).mockResolvedValue({ id: 99, codigo: 'LIQ-2026-01', estado: 'BORRADOR', distribucion: [], warnings: [] } as unknown as apiLiq.LiquidacionRead)
    vi.mocked(apiLiq.createLiquidacion).mockResolvedValue({ id: 100, codigo: 'LIQ-2026-02', periodo: '2026-08', estado: 'BORRADOR', distribucion: [], warnings: [] } as unknown as apiLiq.LiquidacionRead)
    vi.mocked(apiLiq.transitionLiquidacion).mockResolvedValue({ id: 99, codigo: 'LIQ-2026-01', estado: 'APROBADA', distribucion: [], warnings: [] } as unknown as apiLiq.LiquidacionRead)
    vi.mocked(apiLiq.deleteLiquidacion).mockResolvedValue(undefined)
    vi.mocked(apiAnt.listAnticipos).mockResolvedValue({ items: [{ id: 99, socia_id: 2, monto: 50000, fecha: '2026-07-10', estado: 'PENDIENTE_DESCUENTO' } as apiAnt.AnticipoRead], total: 1 })
    vi.mocked(apiAnt.createAnticipo).mockResolvedValue({ id: 100, socia_id: 2, monto: 50000, fecha: '2026-07-11', estado: 'PENDIENTE_DESCUENTO' } as apiAnt.AnticipoRead)
    vi.mocked(apiAnt.descontarAnticipo).mockResolvedValue({ id: 99, socia_id: 2, monto: 50000, estado: 'DESCONTADO', liquidacion_id: 99 } as apiAnt.AnticipoRead)
    vi.mocked(apiAnt.transitionAnticipo).mockResolvedValue({ id: 99, socia_id: 2, estado: 'ANULADO' } as apiAnt.AnticipoRead)
    vi.mocked(apiAnt.deleteAnticipo).mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('VITE_USE_MOCK=true → atelier (mock)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'true')
    })

    it('listLiquidaciones filters by estado locally (LIQ-2)', async () => {
      const uf = useFinanzas()
      expect(uf.isMock.value).toBe(true)
      const all = await uf.listLiquidaciones({})
      expect(all.total).toBeGreaterThanOrEqual(0)
      const borrador = await uf.listLiquidaciones({ estado: 'BORRADOR' })
      expect(borrador.items.every((l) => (l as { estado: string }).estado === 'BORRADOR')).toBe(true)
    })

    it('createLiquidacion pushes LIQ-YYYY-NN with distribucion (LIQ-1)', async () => {
      const uf = useFinanzas()
      const store = useAtelierStore()
      const before = store.liquidaciones.length
      const created = await uf.createLiquidacion({
        periodo: '2026-09',
        fecha_cierre: '2026-09-30',
        total_ventas_brutas: 150000,
        costo_taller_insumos: 30000,
        gastos_operativos: 20000,
        utilidad_neta_total: 100000,
        fondo_reinversion_monto: 40000,
        utilidad_repartible: 60000,
      })
      expect(created).toBeDefined()
      expect(store.liquidaciones.length).toBe(before + 1)
      expect((created as { codigo: string }).codigo).toMatch(/^LIQ-2026-\d{2}$/)
      expect((created as { estado: string }).estado).toBe('BORRADOR')
    })

    it('transitionLiquidacion BORRADOR→APROBADA mock FSM (LIQ-2)', async () => {
      const uf = useFinanzas()
      const created = await uf.createLiquidacion({
        periodo: '2026-10',
        fecha_cierre: '2026-10-31',
        total_ventas_brutas: 150000,
        costo_taller_insumos: 30000,
        gastos_operativos: 20000,
        utilidad_neta_total: 100000,
        fondo_reinversion_monto: 40000,
        utilidad_repartible: 60000,
      })
      const id = (created as { id: number }).id
      const aprob = await uf.transitionLiquidacion(id, { estado: 'APROBADA' })
      expect((aprob as { estado: string }).estado).toBe('APROBADA')
      const pagada = await uf.transitionLiquidacion(id, { estado: 'PAGADA' })
      expect((pagada as { estado: string }).estado).toBe('PAGADA')
    })

    it('removeLiquidacion deletes from atelier (LIQ-1)', async () => {
      const uf = useFinanzas()
      const created = await uf.createLiquidacion({
        periodo: '2026-11',
        fecha_cierre: '2026-11-30',
        total_ventas_brutas: 150000,
        costo_taller_insumos: 30000,
        gastos_operativos: 20000,
        utilidad_neta_total: 100000,
        fondo_reinversion_monto: 40000,
        utilidad_repartible: 60000,
      })
      const id = (created as { id: number }).id
      const before = useAtelierStore().liquidaciones.length
      await uf.removeLiquidacion(id)
      expect(useAtelierStore().liquidaciones.length).toBe(before - 1)
    })

    it('listAnticipos filters by socia_id/estado locally (ANT-3)', async () => {
      const uf = useFinanzas()
      const all = await uf.listAnticipos({})
      expect(all.total).toBeGreaterThanOrEqual(0)
      // create two anticipos for same socia then filter
      const sId = useAtelierStore().socias[0].id
      await uf.createAnticipo({ socia_id: sId, monto: 1000 })
      await uf.createAnticipo({ socia_id: sId, monto: 2000 })
      const bySocia = await uf.listAnticipos({ socia_id: sId })
      expect(bySocia.items.every((a) => (a as { socia_id: number }).socia_id === sId)).toBe(true)
      const pendiente = await uf.listAnticipos({ estado: 'PENDIENTE_DESCUENTO' })
      expect(pendiente.items.every((a) => (a as { estado: string }).estado === 'PENDIENTE_DESCUENTO')).toBe(true)
    })

    it('createAnticipo + descontarAnticipo mock flow (ANT-1/2)', async () => {
      const uf = useFinanzas()
      const sId = useAtelierStore().socias[0].id
      const ant = await uf.createAnticipo({ socia_id: sId, monto: 5000 })
      expect((ant as { estado: string }).estado).toBe('PENDIENTE_DESCUENTO')
      const liq = await uf.createLiquidacion({
        periodo: '2026-12',
        fecha_cierre: '2026-12-31',
        total_ventas_brutas: 150000,
        costo_taller_insumos: 30000,
        gastos_operativos: 20000,
        utilidad_neta_total: 100000,
        fondo_reinversion_monto: 40000,
        utilidad_repartible: 60000,
      })
      const descontado = await uf.descontarAnticipo((ant as { id: number }).id, (liq as { id: number }).id)
      expect((descontado as { estado: string }).estado).toBe('DESCONTADO')
      expect((descontado as { liquidacion_id: number }).liquidacion_id).toBe((liq as { id: number }).id)
    })

    it('does NOT call real API when isMock', async () => {
      const uf = useFinanzas()
      await uf.listLiquidaciones({})
      await uf.listAnticipos({})
      expect(apiLiq.listLiquidaciones).not.toHaveBeenCalled()
      expect(apiAnt.listAnticipos).not.toHaveBeenCalled()
    })
  })

  describe('VITE_USE_MOCK=false → /api/v1 (real)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'false')
    })

    it('listLiquidaciones delegates to api.listLiquidaciones', async () => {
      const uf = useFinanzas()
      expect(uf.isMock.value).toBe(false)
      const res = await uf.listLiquidaciones({ estado: 'BORRADOR', limit: 5 })
      expect(apiLiq.listLiquidaciones).toHaveBeenCalledWith({ estado: 'BORRADOR', limit: 5 })
      expect(res.items[0].codigo).toBe('LIQ-2026-01')
    })

    it('createLiquidacion delegates to api.createLiquidacion', async () => {
      const uf = useFinanzas()
      const payload = {
        periodo: '2026-07',
        fecha_cierre: '2026-07-31',
        total_ventas_brutas: 150000,
        costo_taller_insumos: 30000,
        gastos_operativos: 20000,
        utilidad_neta_total: 100000,
        fondo_reinversion_monto: 40000,
        utilidad_repartible: 60000,
      }
      const res = await uf.createLiquidacion(payload)
      expect(apiLiq.createLiquidacion).toHaveBeenCalledWith(payload)
      expect(res.codigo).toBe('LIQ-2026-02')
    })

    it('transition/remove liquidacion delegate to api', async () => {
      const uf = useFinanzas()
      await uf.transitionLiquidacion(99, { estado: 'APROBADA' })
      expect(apiLiq.transitionLiquidacion).toHaveBeenCalledWith(99, { estado: 'APROBADA' })
      await uf.removeLiquidacion(99)
      expect(apiLiq.deleteLiquidacion).toHaveBeenCalledWith(99)
    })

    it('listAnticipos delegates to api.listAnticipos', async () => {
      const uf = useFinanzas()
      const res = await uf.listAnticipos({ socia_id: 2, estado: 'PENDIENTE_DESCUENTO' })
      expect(apiAnt.listAnticipos).toHaveBeenCalledWith({ socia_id: 2, estado: 'PENDIENTE_DESCUENTO' })
      expect(res.items[0].estado).toBe('PENDIENTE_DESCUENTO')
    })

    it('create/descontar/transition anticipos delegate to api', async () => {
      const uf = useFinanzas()
      await uf.createAnticipo({ socia_id: 2, monto: 5000 })
      expect(apiAnt.createAnticipo).toHaveBeenCalledWith({ socia_id: 2, monto: 5000 })
      await uf.descontarAnticipo(99, 99)
      expect(apiAnt.descontarAnticipo).toHaveBeenCalledWith(99, 99)
      await uf.transitionAnticipo(99, { estado: 'ANULADO' })
      expect(apiAnt.transitionAnticipo).toHaveBeenCalledWith(99, { estado: 'ANULADO' })
      await uf.removeAnticipo(99)
      expect(apiAnt.deleteAnticipo).toHaveBeenCalledWith(99)
    })
  })
})
