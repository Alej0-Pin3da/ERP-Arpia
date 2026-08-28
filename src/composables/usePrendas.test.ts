import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAtelierStore } from '@/stores/atelier'

vi.mock('@/services/api/prendas', () => ({
  listPrendas: vi.fn().mockResolvedValue({ items: [{ id: 99, variante_id: 1, talla: 'M', estado: 'disponible', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }], total: 1 }),
  getPrenda: vi.fn().mockResolvedValue({ id: 99, variante_id: 1, talla: 'M', estado: 'disponible', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }),
  createPrenda: vi.fn().mockResolvedValue({ id: 100, variante_id: 1, talla: 'S', estado: 'disponible', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }),
  updatePrenda: vi.fn().mockResolvedValue({ id: 99, variante_id: 1, talla: 'M', estado: 'vendida', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }),
  deletePrenda: vi.fn().mockResolvedValue(undefined),
}))

import * as apiPrendas from '@/services/api/prendas'
import { usePrendas } from './usePrendas'

describe('usePrendas', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.mocked(apiPrendas.listPrendas).mockResolvedValue({ items: [{ id: 99, variante_id: 1, talla: 'M', estado: 'disponible', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }], total: 1 })
    vi.mocked(apiPrendas.getPrenda).mockResolvedValue({ id: 99, variante_id: 1, talla: 'M', estado: 'disponible', created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    vi.mocked(apiPrendas.createPrenda).mockResolvedValue({ id: 100, variante_id: 1, talla: 'S', estado: 'disponible', created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    vi.mocked(apiPrendas.updatePrenda).mockResolvedValue({ id: 99, variante_id: 1, talla: 'M', estado: 'vendida', created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    vi.mocked(apiPrendas.deletePrenda).mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('VITE_USE_MOCK=true → atelier (mock)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'true')
    })

    it('list returns items and filters locally', async () => {
      const composable = usePrendas()
      expect(composable.isMock.value).toBe(true)
      const res = await composable.list()
      expect(res.total).toBeGreaterThan(0)
      expect(apiPrendas.listPrendas).not.toHaveBeenCalled()
    })

    it('create, update, delete manipulate local store', async () => {
      const composable = usePrendas()
      const store = useAtelierStore()
      const initialCount = store.prendasListas.length

      const created = await composable.create({
        variante_id: 1,
        talla: 'L',
        precio_venta: 120000,
      })
      expect(created.id).toBeDefined()
      expect(store.prendasListas.length).toBe(initialCount + 1)

      const updated = await composable.update(created.id, { precio_venta: 150000 })
      expect(updated?.precio_venta).toBe(150000)

      await composable.remove(created.id)
      expect(store.prendasListas.length).toBe(initialCount)
    })
  })

  describe('VITE_USE_MOCK=false → API (real)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'false')
    })

    it('delegates list to apiPrendas', async () => {
      const composable = usePrendas()
      expect(composable.isMock.value).toBe(false)
      const res = await composable.list({ estado: 'disponible' })
      expect(apiPrendas.listPrendas).toHaveBeenCalledWith({ estado: 'disponible' })
      expect(res.total).toBe(1)
    })

    it('delegates create, update, delete to apiPrendas', async () => {
      const composable = usePrendas()
      await composable.create({
        variante_id: 1,
        talla: 'M',
      })
      expect(apiPrendas.createPrenda).toHaveBeenCalled()

      await composable.update(99, { estado: 'vendida' })
      expect(apiPrendas.updatePrenda).toHaveBeenCalledWith(99, { estado: 'vendida' })

      await composable.remove(99)
      expect(apiPrendas.deletePrenda).toHaveBeenCalledWith(99)
    })
  })
})
