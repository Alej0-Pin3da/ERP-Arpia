import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api/maestros', () => ({
  listProveedores: vi.fn().mockResolvedValue({ items: [{ id: 99, nombre: 'Real Prov', categoria: 'Telas', activo: true }], total: 1 }),
  createProveedor: vi.fn().mockResolvedValue({ id: 100, nombre: 'Created Prov', categoria: 'Telas' }),
  updateProveedor: vi.fn().mockResolvedValue({ id: 99, nombre: 'Updated Prov' }),
  deleteProveedor: vi.fn().mockResolvedValue(undefined),
  listCategorias: vi.fn().mockResolvedValue({ items: [{ id: 1, nombre: 'Cat', tipo_talla: 'TALLA_UNICA' }], total: 1 }),
  createCategoria: vi.fn().mockResolvedValue({ id: 10, nombre: 'Created Cat' }),
  updateCategoria: vi.fn().mockResolvedValue({ id: 1, nombre: 'Updated Cat' }),
  deleteCategoria: vi.fn().mockResolvedValue(undefined),
  listUbicaciones: vi.fn().mockResolvedValue({ items: [{ id: 1, codigo: 'UB-A1', nombre: 'Estante', tipo: 'ROLLOS_TELAS' }], total: 1 }),
  createUbicacion: vi.fn().mockResolvedValue({ id: 10, codigo: 'UB-X1', nombre: 'New' }),
  updateUbicacion: vi.fn().mockResolvedValue({ id: 1, codigo: 'UB-A1', nombre: 'Updated' }),
  deleteUbicacion: vi.fn().mockResolvedValue(undefined),
  listCanales: vi.fn().mockResolvedValue({ items: [{ id: 1, codigo: 'web', nombre: 'Web' }], total: 1 }),
  createCanal: vi.fn().mockResolvedValue({ id: 10, codigo: 'new', nombre: 'New Canal' }),
  updateCanal: vi.fn().mockResolvedValue({ id: 1, nombre: 'Updated Canal' }),
  deleteCanal: vi.fn().mockResolvedValue(undefined),
  listMetodosPago: vi.fn().mockResolvedValue({ items: [{ id: 1, codigo: 'nequi', nombre: 'Nequi' }], total: 1 }),
  createMetodo: vi.fn().mockResolvedValue({ id: 10, codigo: 'newpay', nombre: 'New Pay' }),
  updateMetodo: vi.fn().mockResolvedValue({ id: 1, nombre: 'Updated Pay' }),
  deleteMetodo: vi.fn().mockResolvedValue(undefined),
  listTallas: vi.fn().mockResolvedValue({ items: [{ id: 1, talla: 'M', orden: 4 }], total: 1 }),
  createTalla: vi.fn().mockResolvedValue({ id: 10, talla: 'XXL', orden: 7 }),
  updateTalla: vi.fn().mockResolvedValue({ id: 1, talla: 'M', orden: 4 }),
  deleteTalla: vi.fn().mockResolvedValue(undefined),
  listProductosSinTalla: vi.fn().mockResolvedValue({ items: [{ id: 1, nombre: 'Tote', categoria: 'Merch' }], total: 1 }),
  createProductoSinTalla: vi.fn().mockResolvedValue({ id: 10, nombre: 'New Tote' }),
  updateProductoSinTalla: vi.fn().mockResolvedValue({ id: 1, nombre: 'Updated Tote' }),
  deleteProductoSinTalla: vi.fn().mockResolvedValue(undefined),
  getParametros: vi.fn().mockResolvedValue({ id: 1, costo_minuto_costura: 80, distribucion_reinversion_pct: 40, reparto_margara_pct: 30, reparto_valqui_pct: 30 }),
  updateParametros: vi.fn().mockResolvedValue({ id: 1, costo_minuto_costura: 120, distribucion_reinversion_pct: 40, reparto_margara_pct: 30, reparto_valqui_pct: 30 }),
}))

import * as apiMaestros from '@/services/api/maestros'
import { useMaestros } from './useMaestros'

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  // Re-apply after restore
  vi.mocked(apiMaestros.listProveedores).mockResolvedValue({ items: [{ id: 99, nombre: 'Real Prov', categoria: 'Telas', activo: true } as never], total: 1 })
  vi.mocked(apiMaestros.getParametros).mockResolvedValue({ id: 1, costo_minuto_costura: 80, costo_hora_patronaje: 15000, margen_meta_global_pct: 35, desperdicio_textil_default_pct: 8, iva_regimen_pct: 19, distribucion_reinversion_pct: 40, reparto_margara_pct: 30, reparto_valqui_pct: 30, created_at: '', updated_at: '' } as never)
  vi.mocked(apiMaestros.listCanales).mockResolvedValue({ items: [{ id: 1, codigo: 'web', nombre: 'Web' } as never], total: 1 })
  vi.mocked(apiMaestros.listMetodosPago).mockResolvedValue({ items: [{ id: 1, codigo: 'nequi', nombre: 'Nequi' } as never], total: 1 })
  vi.mocked(apiMaestros.listTallas).mockResolvedValue({ items: [{ id: 1, talla: 'M', orden: 4 } as never], total: 1 })
  vi.mocked(apiMaestros.listProductosSinTalla).mockResolvedValue({ items: [{ id: 1, nombre: 'Tote', categoria: 'Merch' } as never], total: 1 })
  vi.mocked(apiMaestros.listCategorias).mockResolvedValue({ items: [{ id: 1, nombre: 'Cat', tipo_talla: 'TALLA_UNICA' } as never], total: 1 })
  vi.mocked(apiMaestros.listUbicaciones).mockResolvedValue({ items: [{ id: 1, codigo: 'UB-A1', nombre: 'Estante', tipo: 'ROLLOS_TELAS' } as never], total: 1 })
})

afterEach(() => vi.unstubAllEnvs())

describe('useMaestros', () => {
  it('isMock true routes to atelier', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const m = useMaestros()
    expect(m.isMock.value).toBe(true)
    const res = await m.listProveedores({ q: 'atenea' })
    expect(res.total).toBeGreaterThanOrEqual(0)
    expect(apiMaestros.listProveedores).not.toHaveBeenCalled()
  })

  it('isMock false calls api', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const m = useMaestros()
    const res = await m.listProveedores({ q: 'atenea' })
    expect(apiMaestros.listProveedores).toHaveBeenCalledWith({ q: 'atenea' })
    expect(res.total).toBe(1)
  })

  it('listCategorias mock filter', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const m = useMaestros()
    await m.createCategoria({ nombre: 'Cat Mock', tipo_talla: 'TALLA_UNICA' })
    const res = await m.listCategorias({ tipo_talla: 'TALLA_UNICA' })
    expect(res.items.some((c) => c.nombre === 'Cat Mock')).toBe(true)
  })

  it('listUbicaciones api', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const m = useMaestros()
    await m.listUbicaciones({ tipo: 'ROLLOS_TELAS' })
    expect(apiMaestros.listUbicaciones).toHaveBeenCalled()
  })

  it('listCanales api fallback path', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const m = useMaestros()
    const res = await m.listCanales()
    expect(apiMaestros.listCanales).toHaveBeenCalled()
    expect(res.items.length).toBeGreaterThan(0)
  })

  it('listMetodosPago api', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const m = useMaestros()
    const res = await m.listMetodosPago({ tipo: 'BILLETERA_DIGITAL' })
    expect(res.total).toBe(1)
  })

  it('listTallas api sorts', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const m = useMaestros()
    const res = await m.listTallas({ sort_by: 'orden' })
    expect(apiMaestros.listTallas).toHaveBeenCalledWith({ sort_by: 'orden' })
    expect(res.items[0].talla).toBe('M')
  })

  it('listProductosSinTalla api', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const m = useMaestros()
    await m.listProductosSinTalla({ categoria: 'Merch' })
    expect(apiMaestros.listProductosSinTalla).toHaveBeenCalled()
  })

  it('getParametros mock vs api', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const m1 = useMaestros()
    const p1 = await m1.getParametros()
    expect(p1).toBeDefined()
    vi.stubEnv('VITE_USE_MOCK', 'false')
    const m2 = useMaestros()
    const p2 = await m2.getParametros()
    expect(apiMaestros.getParametros).toHaveBeenCalled()
    expect(p2.id).toBe(1)
  })

  it('createProveedor mock adds', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const m = useMaestros()
    const before = (await m.listProveedores()).total
    await m.createProveedor({ nombre: 'Prov Test', categoria: 'Test', ciudad: 'Pereira' })
    const after = (await m.listProveedores()).total
    expect(after).toBe(before + 1)
  })

  it('updateParametros mock persists', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const m = useMaestros()
    await m.updateParametros({ costo_minuto_costura: 999 })
    const p = await m.getParametros()
    expect(Number((p as unknown as Record<string, unknown>).costo_minuto_costura)).toBe(999)
  })

  it('removeProveedor mock deletes', async () => {
    vi.stubEnv('VITE_USE_MOCK', 'true')
    const m = useMaestros()
    const created = (await m.createProveedor({ nombre: 'ToDelete', categoria: 'Test' })) as unknown as { id: number }
    const before = (await m.listProveedores()).total
    await m.removeProveedor(created.id)
    const after = (await m.listProveedores()).total
    expect(after).toBe(before - 1)
  })
})
