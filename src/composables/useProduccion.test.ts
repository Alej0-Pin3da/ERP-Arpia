import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAtelierStore } from '@/stores/atelier'

vi.mock('@/services/api/pedidos-produccion', () => ({
  listPedidosProduccion: vi.fn().mockResolvedValue({ items: [{ id: 99, producto_id: 1, cantidad: 5, cantidad_producida: 0, estado: 'pendiente', prioridad: 'normal', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }], total: 1 }),
  getPedidoProduccion: vi.fn().mockResolvedValue({ id: 99, producto_id: 1, cantidad: 5, cantidad_producida: 0, estado: 'pendiente', prioridad: 'normal', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }),
  createPedidoProduccion: vi.fn().mockResolvedValue({ id: 100, producto_id: 1, cantidad: 10, cantidad_producida: 0, estado: 'pendiente', prioridad: 'alta', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }),
  updatePedidoProduccion: vi.fn().mockResolvedValue({ id: 99, producto_id: 1, cantidad: 5, cantidad_producida: 2, estado: 'en_produccion', prioridad: 'normal', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }),
  deletePedidoProduccion: vi.fn().mockResolvedValue(undefined),
}))

import * as apiPedidos from '@/services/api/pedidos-produccion'
import { useProduccion } from './useProduccion'

describe('useProduccion', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.mocked(apiPedidos.listPedidosProduccion).mockResolvedValue({ items: [{ id: 99, producto_id: 1, cantidad: 5, cantidad_producida: 0, estado: 'pendiente', prioridad: 'normal', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }], total: 1 })
    vi.mocked(apiPedidos.getPedidoProduccion).mockResolvedValue({ id: 99, producto_id: 1, cantidad: 5, cantidad_producida: 0, estado: 'pendiente', prioridad: 'normal', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    vi.mocked(apiPedidos.createPedidoProduccion).mockResolvedValue({ id: 100, producto_id: 1, cantidad: 10, cantidad_producida: 0, estado: 'pendiente', prioridad: 'alta', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    vi.mocked(apiPedidos.updatePedidoProduccion).mockResolvedValue({ id: 99, producto_id: 1, cantidad: 5, cantidad_producida: 2, estado: 'en_produccion', prioridad: 'normal', fecha_pedido: '2026-08-27', created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    vi.mocked(apiPedidos.deletePedidoProduccion).mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('VITE_USE_MOCK=true → atelier (mock)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'true')
    })

    it('list returns items and filters locally', async () => {
      const composable = useProduccion()
      expect(composable.isMock.value).toBe(true)
      const res = await composable.list()
      expect(res.total).toBeGreaterThan(0)
      expect(apiPedidos.listPedidosProduccion).not.toHaveBeenCalled()
    })

    it('create, update, delete manipulate local store', async () => {
      const composable = useProduccion()
      const store = useAtelierStore()
      const initialCount = store.pedidos.length

      const created = await composable.create({
        producto_id: 1,
        cantidad: 3,
        observaciones: 'Test pedido',
      })
      expect(created.id).toBeDefined()
      expect(store.pedidos.length).toBe(initialCount + 1)

      const updated = await composable.update(created.id, { observaciones: 'Observación actualizada' })
      expect(updated?.observaciones).toBe('Observación actualizada')

      await composable.remove(created.id)
      expect(store.pedidos.length).toBe(initialCount)
    })
  })

  describe('VITE_USE_MOCK=false → API (real)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'false')
    })

    it('delegates list to apiPedidos', async () => {
      const composable = useProduccion()
      expect(composable.isMock.value).toBe(false)
      const res = await composable.list({ estado: 'pendiente' })
      expect(apiPedidos.listPedidosProduccion).toHaveBeenCalledWith({ estado: 'pendiente' })
      expect(res.total).toBe(1)
    })

    it('delegates create, update, delete to apiPedidos', async () => {
      const composable = useProduccion()
      await composable.create({
        producto_id: 1,
        cantidad: 10,
      })
      expect(apiPedidos.createPedidoProduccion).toHaveBeenCalled()

      await composable.update(99, { estado: 'en_produccion' })
      expect(apiPedidos.updatePedidoProduccion).toHaveBeenCalledWith(99, { estado: 'en_produccion' })

      await composable.remove(99)
      expect(apiPedidos.deletePedidoProduccion).toHaveBeenCalledWith(99)
    })
  })
})
