import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api/socios', () => ({
  listSocios: vi.fn().mockResolvedValue({ items: [{ id: 99, nombre: 'Real Socia', porcentaje_participacion: 30, activo: true, es_fondo_taller: false }], total: 1 }),
  getSocia: vi.fn().mockResolvedValue({ id: 99, nombre: 'Real Socia', porcentaje_participacion: 30 }),
  createSocia: vi.fn().mockResolvedValue({ id: 100, nombre: 'Created Real', porcentaje_participacion: 30 }),
  updateSocia: vi.fn().mockResolvedValue({ id: 99, nombre: 'Updated Real', porcentaje_participacion: 35 }),
  deleteSocia: vi.fn().mockResolvedValue(undefined),
}))

import * as apiSocios from '@/services/api/socios'
import { useSocios } from './useSocios'

describe('useSocios', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.mocked(apiSocios.listSocios).mockResolvedValue({ items: [{ id: 99, nombre: 'Real Socia', porcentaje_participacion: 30, activo: true, es_fondo_taller: false } as apiSocios.SociaRead], total: 1 })
    vi.mocked(apiSocios.getSocia).mockResolvedValue({ id: 99, nombre: 'Real Socia', porcentaje_participacion: 30 } as apiSocios.SociaRead)
    vi.mocked(apiSocios.createSocia).mockResolvedValue({ id: 100, nombre: 'Created Real', porcentaje_participacion: 30 } as apiSocios.SociaRead)
    vi.mocked(apiSocios.updateSocia).mockResolvedValue({ id: 99, nombre: 'Updated Real', porcentaje_participacion: 35 } as apiSocios.SociaRead)
    vi.mocked(apiSocios.deleteSocia).mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('VITE_USE_MOCK=false → /api/v1 (real)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'false')
    })

    it('list delegates to api.listSocios with params (SOC-3)', async () => {
      const us = useSocios()
      expect(us.isMock.value).toBe(false)
      const result = await us.list({ activo: true, es_fondo_taller: false, q: 'marg', limit: 10, offset: 0 })
      expect(apiSocios.listSocios).toHaveBeenCalledWith({ activo: true, es_fondo_taller: false, q: 'marg', limit: 10, offset: 0 })
      expect(result.items[0].nombre).toBe('Real Socia')
    })

    it('create delegates to api.createSocia', async () => {
      const us = useSocios()
      const result = await us.create({ nombre: 'Real New', porcentaje_participacion: 30 })
      expect(apiSocios.createSocia).toHaveBeenCalledWith({ nombre: 'Real New', porcentaje_participacion: 30 })
      expect(result.nombre).toBe('Created Real')
    })

    it('get/update/remove delegate to api', async () => {
      const us = useSocios()
      await us.get(99)
      expect(apiSocios.getSocia).toHaveBeenCalledWith(99)
      await us.update(99, { rol: 'Modista' })
      expect(apiSocios.updateSocia).toHaveBeenCalledWith(99, { rol: 'Modista' })
      await us.remove(99)
      expect(apiSocios.deleteSocia).toHaveBeenCalledWith(99)
    })
  })
})
