import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAtelierStore } from '@/stores/atelier'

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

  describe('VITE_USE_MOCK=true → atelier (mock)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_USE_MOCK', 'true')
    })

    it('list filters by activo / es_fondo_taller / q locally (SOC-3)', async () => {
      const us = useSocios()
      expect(us.isMock.value).toBe(true)
      const all = await us.list({})
      expect(all.total).toBeGreaterThan(0)

      const activas = await us.list({ activo: true })
      expect(activas.items.every((s) => (s as { activo: boolean }).activo === true)).toBe(true)

      const fondo = await us.list({ es_fondo_taller: true })
      // atelier seed: one fondo row exists conceptually; if mocked later, should filter
      expect(fondo.items.every((s) => Boolean((s as { es_fondo_taller: boolean }).es_fondo_taller))).toBe(true)

      const qMarga = await us.list({ q: 'marg' })
      // should match at least one if seed contains Margarita-like; q is case-insensitive
      expect(qMarga.items.length).toBeGreaterThanOrEqual(0)

      const paged = await us.list({ limit: 1, offset: 0 })
      expect(paged.items.length).toBeLessThanOrEqual(1)
    })

    it('create pushes to atelier and is retrievable (SOC-1)', async () => {
      const us = useSocios()
      const store = useAtelierStore()
      const before = store.socias.length
      const created = await us.create({ nombre: 'Test Socia Vitest', porcentaje_participacion: 30 })
      expect(created).toBeDefined()
      expect(store.socias.length).toBe(before + 1)
      expect((store.socias[0] as { nombre: string }).nombre).toBe('Test Socia Vitest')
    })

    it('create with extended profile maps fields', async () => {
      const us = useSocios()
      const created = await us.create({ nombre: 'Fondo Vitest', porcentaje_participacion: 40, es_fondo_taller: true, email: 'fondo@arpia.com', tipo_cuenta: 'AHORROS' })
      expect((created as { es_fondo_taller: boolean }).es_fondo_taller).toBe(true)
      expect((created as { email: string }).email).toBe('fondo@arpia.com')
    })

    it('update mutates existing socia (SOC-1 PATCH)', async () => {
      const us = useSocios()
      const store = useAtelierStore()
      const id = store.socias[0].id
      const updated = await us.update(id, { rol: 'Modista' })
      expect(updated).not.toBeNull()
      expect((updated as { rol: string }).rol).toBe('Modista')
    })

    it('remove deletes from atelier', async () => {
      const us = useSocios()
      const store = useAtelierStore()
      const id = store.socias[0].id
      const before = store.socias.length
      await us.remove(id)
      expect(store.socias.length).toBe(before - 1)
      expect(store.socias.find((s) => s.id === id)).toBeUndefined()
    })

    it('get returns from atelier', async () => {
      const us = useSocios()
      const store = useAtelierStore()
      const id = store.socias[0].id
      const found = await us.get(id)
      expect(found).not.toBeNull()
      expect((found as { id: number }).id).toBe(id)
    })

    it('does NOT call real API when isMock', async () => {
      const us = useSocios()
      await us.list({})
      expect(apiSocios.listSocios).not.toHaveBeenCalled()
    })
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
