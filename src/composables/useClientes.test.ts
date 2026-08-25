import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAtelierStore } from '@/stores/atelier'

// Mock the api services before importing composable
vi.mock('@/services/api/clientes', () => ({
  listClientes: vi.fn().mockResolvedValue({ items: [{ id: 99, nombre: 'Real Cliente', ciudad: 'Bogotá', created_at: new Date().toISOString() }], total: 1 }),
  getCliente: vi.fn().mockResolvedValue({ id: 99, nombre: 'Real Cliente', created_at: new Date().toISOString() }),
  createCliente: vi.fn().mockResolvedValue({ id: 100, nombre: 'Created Real', created_at: new Date().toISOString() }),
  updateCliente: vi.fn().mockResolvedValue({ id: 99, nombre: 'Updated Real', created_at: new Date().toISOString() }),
  deleteCliente: vi.fn().mockResolvedValue(undefined),
}))

import * as apiClientes from '@/services/api/clientes'
import { useClientes } from './useClientes'

describe('useClientes', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    // re-apply mock implementations after restore
    vi.mocked(apiClientes.listClientes).mockResolvedValue({ items: [{ id: 99, nombre: 'Real Cliente', ciudad: 'Bogotá', created_at: new Date().toISOString() } as apiClientes.ClienteRead], total: 1 })
    vi.mocked(apiClientes.getCliente).mockResolvedValue({ id: 99, nombre: 'Real Cliente', created_at: new Date().toISOString() } as apiClientes.ClienteRead)
    vi.mocked(apiClientes.createCliente).mockResolvedValue({ id: 100, nombre: 'Created Real', created_at: new Date().toISOString() } as apiClientes.ClienteRead)
    vi.mocked(apiClientes.updateCliente).mockResolvedValue({ id: 99, nombre: 'Updated Real', created_at: new Date().toISOString() } as apiClientes.ClienteRead)
    vi.mocked(apiClientes.deleteCliente).mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('VITE_USE_MOCK=true → atelier (mock)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'true')
    })

    it('list filters by tipo/ciudad/q locally (IIFE from spec CRM-2)', async () => {
      const uc = useClientes()
      expect(uc.isMock.value).toBe(true)
      // atelier seed has Gabriela in Pereira, Maira in Manizales
      const all = await uc.list({})
      expect(all.total).toBeGreaterThan(0)

      const pereira = await uc.list({ ciudad: 'Pereira' })
      expect(pereira.items.every((c) => (c as { ciudad: string }).ciudad === 'Pereira')).toBe(true)
      expect(pereira.total).toBeGreaterThan(0)

      const qMaira = await uc.list({ q: 'maira' })
      // Maira (*Comic) should match case-insensitive q
      expect(qMaira.items.length).toBeGreaterThan(0)

      // pagination
      const paged = await uc.list({ limit: 2, offset: 0 })
      expect(paged.items.length).toBeLessThanOrEqual(2)
    })

    it('create pushes to atelier and is retrievable', async () => {
      const uc = useClientes()
      const store = useAtelierStore()
      const before = store.clientes.length
      const created = await uc.create({ nombre: 'Test Cliente Vitest', ciudad: 'Pereira', tipo: 'Clienta Habitual' })
      expect(created).toBeDefined()
      expect(store.clientes.length).toBe(before + 1)
      expect(store.clientes[0].nombre).toBe('Test Cliente Vitest')
    })

    it('update mutates existing cliente', async () => {
      const uc = useClientes()
      const store = useAtelierStore()
      const id = store.clientes[0].id
      const updated = await uc.update(id, { ciudad: 'Bogotá' })
      expect(updated).not.toBeNull()
      expect((updated as { ciudad: string }).ciudad).toBe('Bogotá')
    })

    it('remove deletes from atelier', async () => {
      const uc = useClientes()
      const store = useAtelierStore()
      const id = store.clientes[0].id
      const before = store.clientes.length
      await uc.remove(id)
      expect(store.clientes.length).toBe(before - 1)
      expect(store.clientes.find((c) => c.id === id)).toBeUndefined()
    })

    it('get returns from atelier', async () => {
      const uc = useClientes()
      const store = useAtelierStore()
      const id = store.clientes[0].id
      const found = await uc.get(id)
      expect(found).not.toBeNull()
      expect((found as { id: number }).id).toBe(id)
    })

    it('does NOT call real API when isMock', async () => {
      const uc = useClientes()
      await uc.list({})
      expect(apiClientes.listClientes).not.toHaveBeenCalled()
    })
  })

  describe('VITE_USE_MOCK=false → /api/v1 (real)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'false')
    })

    it('list delegates to api.listClientes with params', async () => {
      const uc = useClientes()
      expect(uc.isMock.value).toBe(false)
      const result = await uc.list({ q: 'maria', tipo: 'mayorista', ciudad: 'Pereira', limit: 10, offset: 0 })
      expect(apiClientes.listClientes).toHaveBeenCalledWith({ q: 'maria', tipo: 'mayorista', ciudad: 'Pereira', limit: 10, offset: 0 })
      expect(result.items[0].nombre).toBe('Real Cliente')
    })

    it('create delegates to api.createCliente', async () => {
      const uc = useClientes()
      const result = await uc.create({ nombre: 'Real New' })
      expect(apiClientes.createCliente).toHaveBeenCalledWith({ nombre: 'Real New' })
      expect(result.nombre).toBe('Created Real')
    })

    it('get/update/remove delegate to api', async () => {
      const uc = useClientes()
      await uc.get(99)
      expect(apiClientes.getCliente).toHaveBeenCalledWith(99)
      await uc.update(99, { ciudad: 'Cali' })
      expect(apiClientes.updateCliente).toHaveBeenCalledWith(99, { ciudad: 'Cali' })
      await uc.remove(99)
      expect(apiClientes.deleteCliente).toHaveBeenCalledWith(99)
    })
  })
})
