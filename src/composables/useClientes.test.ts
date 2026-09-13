import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

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
