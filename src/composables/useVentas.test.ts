import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

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
