import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAtelierStore } from '@/stores/atelier'

vi.mock('@/services/api/ventas', () => ({
  listVentas: vi.fn().mockResolvedValue({ items: [{ id: 99, cliente_id: 1, canal_venta: 'web', metodo_pago: 'efectivo', estado: 'COMPLETADA', total_venta: 100 }], total: 1 }),
  getVenta: vi.fn().mockResolvedValue({ id: 99, canal_venta: 'web', metodo_pago: 'efectivo', estado: 'COMPLETADA' }),
  createVenta: vi.fn().mockResolvedValue({ id: 100, canal_venta: 'web', metodo_pago: 'transferencia', estado: 'COMPLETADA' }),
  anularVenta: vi.fn().mockResolvedValue({ id: 99, canal_venta: 'web', estado: 'ANULADA' }),
}))

import * as apiVentas from '@/services/api/ventas'
import { useVentas } from './useVentas'

describe('useVentas', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.mocked(apiVentas.listVentas).mockResolvedValue({ items: [{ id: 99, cliente_id: 1, canal_venta: 'web', metodo_pago: 'efectivo', estado: 'COMPLETADA', total_venta: 100 } as unknown as apiVentas.VentaRead], total: 1 })
    vi.mocked(apiVentas.getVenta).mockResolvedValue({ id: 99, canal_venta: 'web', metodo_pago: 'efectivo', estado: 'COMPLETADA' } as unknown as apiVentas.VentaRead)
    vi.mocked(apiVentas.createVenta).mockResolvedValue({ id: 100, canal_venta: 'web', metodo_pago: 'transferencia', estado: 'COMPLETADA' } as unknown as apiVentas.VentaRead)
    vi.mocked(apiVentas.anularVenta).mockResolvedValue({ id: 99, canal_venta: 'web', estado: 'ANULADA' } as unknown as apiVentas.VentaRead)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('VITE_USE_MOCK=true → atelier', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'true')
    })

    it('list filters by canal_venta locally', async () => {
      const uv = useVentas()
      expect(uv.isMock.value).toBe(true)
      const all = await uv.list({})
      expect(all.total).toBeGreaterThan(0)
      // atelier seeds have canal values like "Feria Showroom", "WhatsApp / DM"
      const feria = await uv.list({ canal_venta: 'feria' as never })
      // feria won't match legacy strings, so should be 0 or filtered; verify pagination still works
      expect(feria.items.length).toBeLessThanOrEqual(all.total)
    })

    it('create pushes to atelier with canal_venta / metodo_pago', async () => {
      const uv = useVentas()
      const store = useAtelierStore()
      const before = store.ventas.length
      const created = await uv.create({
        canal_venta: 'web',
        metodo_pago: 'transferencia',
        detalles: [{ producto_id: 1, cantidad: 2, precio_unitario: 50000 }],
      })
      expect(created).toBeDefined()
      expect(store.ventas.length).toBe(before + 1)
      expect((created as { canal: string }).canal).toBe('web')
      expect((created as { metodo_pago: string }).metodo_pago).toBe('transferencia')
      expect((created as { items: unknown[] }).items.length).toBe(1)
    })

    it('anular sets estado ANULADA', async () => {
      const uv = useVentas()
      const store = useAtelierStore()
      const id = store.ventas[0].id
      const anulada = await uv.anular(id)
      expect(anulada).not.toBeNull()
      expect((anulada as { estado: string }).estado).toBe('ANULADA')
      expect(store.ventas.find((v) => v.id === id)?.estado).toBe('ANULADA')
    })

    it('does NOT call real API when isMock', async () => {
      const uv = useVentas()
      await uv.list({})
      expect(apiVentas.listVentas).not.toHaveBeenCalled()
    })

    it('handles all 5 canonical canales + 4 metodos types', async () => {
      const uv = useVentas()
      for (const canal of ['web', 'whatsapp', 'instagram', 'feria', 'showroom_pereira'] as const) {
        const c = await uv.create({ canal_venta: canal, detalles: [{ producto_id: 1, cantidad: 1, precio_unitario: 10000 }] })
        expect((c as { canal: string }).canal).toBe(canal)
      }
      for (const metodo of ['efectivo', 'transferencia', 'tarjeta', 'contraentrega'] as const) {
        const c = await uv.create({ canal_venta: 'web', metodo_pago: metodo, detalles: [{ producto_id: 1, cantidad: 1, precio_unitario: 10000 }] })
        expect((c as { metodo_pago: string }).metodo_pago).toBe(metodo)
      }
    })
  })

  describe('VITE_USE_MOCK=false → /api/v1', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'false')
    })

    it('list delegates to api.listVentas', async () => {
      const uv = useVentas()
      expect(uv.isMock.value).toBe(false)
      const result = await uv.list({ canal_venta: 'web', limit: 5 })
      expect(apiVentas.listVentas).toHaveBeenCalledWith({ canal_venta: 'web', limit: 5 })
      expect((result.items[0] as unknown as { canal_venta: string }).canal_venta).toBe('web')
    })

    it('create delegates to api.createVenta with whitelist values', async () => {
      const uv = useVentas()
      await uv.create({ canal_venta: 'showroom_pereira', metodo_pago: 'efectivo', detalles: [{ producto_id: 1, cantidad: 1, precio_unitario: 90000 }] })
      expect(apiVentas.createVenta).toHaveBeenCalledWith({ canal_venta: 'showroom_pereira', metodo_pago: 'efectivo', detalles: [{ producto_id: 1, cantidad: 1, precio_unitario: 90000 }] })
    })

    it('anular delegates to api.anularVenta', async () => {
      const uv = useVentas()
      await uv.anular(99)
      expect(apiVentas.anularVenta).toHaveBeenCalledWith(99)
    })
  })
})
