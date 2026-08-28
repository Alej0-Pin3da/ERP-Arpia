import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAtelierStore } from '@/stores/atelier'

vi.mock('@/services/api/insumos', () => ({
  listInsumos: vi.fn().mockResolvedValue({ items: [{ id: 99, nombre: 'Real Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 10, stock_minimo: 2, costo_promedio_actual: 5000 }], total: 1 }),
  getInsumo: vi.fn().mockResolvedValue({ id: 99, nombre: 'Real Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 10, stock_minimo: 2, costo_promedio_actual: 5000 }),
  createInsumo: vi.fn().mockResolvedValue({ id: 100, nombre: 'Created Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 5, stock_minimo: 1, costo_promedio_actual: 3000 }),
  updateInsumo: vi.fn().mockResolvedValue({ id: 99, nombre: 'Updated Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 15, stock_minimo: 2, costo_promedio_actual: 5000 }),
  deleteInsumo: vi.fn().mockResolvedValue(undefined),
}))

import * as apiInsumos from '@/services/api/insumos'
import { useInsumos } from './useInsumos'

describe('useInsumos', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.mocked(apiInsumos.listInsumos).mockResolvedValue({ items: [{ id: 99, nombre: 'Real Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 10, stock_minimo: 2, costo_promedio_actual: 5000 }], total: 1 })
    vi.mocked(apiInsumos.getInsumo).mockResolvedValue({ id: 99, nombre: 'Real Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 10, stock_minimo: 2, costo_promedio_actual: 5000 })
    vi.mocked(apiInsumos.createInsumo).mockResolvedValue({ id: 100, nombre: 'Created Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 5, stock_minimo: 1, costo_promedio_actual: 3000 })
    vi.mocked(apiInsumos.updateInsumo).mockResolvedValue({ id: 99, nombre: 'Updated Insumo', categoria_id: 1, unidad_medida: 'm', stock_actual: 15, stock_minimo: 2, costo_promedio_actual: 5000 })
    vi.mocked(apiInsumos.deleteInsumo).mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('VITE_USE_MOCK=true → atelier (mock)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'true')
    })

    it('list returns items and filters locally', async () => {
      const composable = useInsumos()
      expect(composable.isMock.value).toBe(true)
      const res = await composable.list()
      expect(res.total).toBeGreaterThan(0)
      expect(apiInsumos.listInsumos).not.toHaveBeenCalled()
    })

    it('create, update, delete manipulate local store', async () => {
      const composable = useInsumos()
      const store = useAtelierStore()
      const initialCount = store.insumos.length

      const created = await composable.create({
        categoria_id: 1,
        nombre: 'Nuevo Test Insumo',
        unidad_medida: 'm',
      })
      expect(created.nombre).toBe('Nuevo Test Insumo')
      expect(store.insumos.length).toBe(initialCount + 1)

      const updated = await composable.update(created.id, { nombre: 'Insumo Modificado' })
      expect(updated?.nombre).toBe('Insumo Modificado')

      await composable.remove(created.id)
      expect(store.insumos.length).toBe(initialCount)
    })
  })

  describe('VITE_USE_MOCK=false → API (real)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'false')
    })

    it('delegates list to apiInsumos', async () => {
      const composable = useInsumos()
      expect(composable.isMock.value).toBe(false)
      const res = await composable.list({ q: 'saten' })
      expect(apiInsumos.listInsumos).toHaveBeenCalledWith({ q: 'saten' })
      expect(res.total).toBe(1)
    })

    it('delegates create, update, delete to apiInsumos', async () => {
      const composable = useInsumos()
      await composable.create({
        categoria_id: 1,
        nombre: 'Insumo API',
        unidad_medida: 'unidades',
      })
      expect(apiInsumos.createInsumo).toHaveBeenCalled()

      await composable.update(99, { nombre: 'Insumo Modificado' })
      expect(apiInsumos.updateInsumo).toHaveBeenCalledWith(99, { nombre: 'Insumo Modificado' })

      await composable.remove(99)
      expect(apiInsumos.deleteInsumo).toHaveBeenCalledWith(99)
    })
  })
})
