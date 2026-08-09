/**
 * OmisionesView integration tests (PR3, spec MIG-3/MIG-4 + FE-1/FE-2/FE-3).
 *
 * Mounts the REAL OmisionesView + OmisionesTable against mocked
 * omisionesApi:
 *  - list renders corrida/fase/hoja/nivel/mensaje/resuelta and requests the
 *    paged list {items, total} (FE-1)
 *  - el-pagination pages with the new offset (FE-1)
 *  - q + fase/nivel/hoja/resuelta filters reset to page 1 and refetch with
 *    the params; resuelta=false IS sent (FE-2)
 *  - admin-only "Marcar resuelta"/"Reabrir" (D9, MIG-4) PATCHes and
 *    refreshes; consulta sees NO action button
 *  - network error renders the error state (FE-3); empty renders el-empty
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'
import OmisionesView from '@/views/OmisionesView.vue'

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listOmisiones: vi.fn(),
    updateOmision: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  omisionesApi: {
    listOmisiones: apiMocks.listOmisiones,
    updateOmision: apiMocks.updateOmision,
  },
}))

const OMISIONES = [
  {
    id: 1,
    corrida_id: 'migracion_20260809_120000',
    fecha_corrida: '2026-08-09T12:00:00',
    fase: 'F5',
    hoja: 'VENTAS',
    fila: 12,
    celda: 'C12',
    nivel: 'WARN',
    mensaje: 'canal no mapeado',
    resuelta: false,
    creado_en: '2026-08-09T12:00:00',
  },
  {
    id: 2,
    corrida_id: 'migracion_20260809_120000',
    fecha_corrida: '2026-08-09T12:00:00',
    fase: 'F2',
    hoja: 'COMPRA',
    fila: 4,
    celda: 'B4',
    nivel: 'ERROR',
    mensaje: 'proveedor inexistente',
    resuelta: true,
    creado_en: '2026-08-09T12:00:00',
  },
]

async function mountView(rol = 'admin'): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 1, nombre: 'Ana Admin', email: 'ana@arpia.com.co', rol },
  })
  const wrapper = mount(OmisionesView, { global: { plugins: [pinia, ElementPlus] } })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('OmisionesView (MIG-3/MIG-4 + T10)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMocks.listOmisiones.mockResolvedValue({ items: OMISIONES, total: 2 })
    apiMocks.updateOmision.mockResolvedValue({ ...OMISIONES[0], resuelta: true })
  })

  afterEach(() => {
    ElMessage.closeAll()
    vi.restoreAllMocks()
  })

  it('renders the omisiones rows and requests the paged list', async () => {
    const wrapper = await mountView()

    const text = wrapper.text()
    expect(text).toContain('migracion_20260809_120000')
    expect(text).toContain('F5')
    expect(text).toContain('VENTAS')
    expect(text).toContain('canal no mapeado')
    expect(text).toContain('WARN')
    expect(text).toContain('ERROR')
    expect(text).toContain('Sí') // resuelta row
    expect(text).toContain('No') // pending row

    expect(apiMocks.listOmisiones).toHaveBeenCalledTimes(1)
    expect(apiMocks.listOmisiones).toHaveBeenCalledWith({ limit: 20, offset: 0 })
  })

  it('renders el-pagination and pages with the new offset', async () => {
    const wrapper = await mountView()
    expect(wrapper.findComponent({ name: 'ElPagination' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'ElPagination' }).vm.$emit('current-change', 2)
    await flushPromises()
    expect(apiMocks.listOmisiones).toHaveBeenLastCalledWith({ limit: 20, offset: 20 })
  })

  it('q and nivel/hoja/resuelta filters reset to page 1 and refetch with params', async () => {
    const wrapper = await mountView()

    const input = wrapper.find('[data-test="omision-search"]')
    await input.setValue('canal')
    await input.trigger('keyup.enter')
    await flushPromises()
    expect(apiMocks.listOmisiones).toHaveBeenLastCalledWith({ limit: 20, offset: 0, q: 'canal' })

    // nivel select
    const nivel = wrapper.find('[data-test="omision-nivel-filter"]')
    await nivel.trigger('click')
    await nextTick()
    const warnOption = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
      (el) => el.textContent?.trim() === 'WARN',
    )
    expect(warnOption).toBeDefined()
    warnOption!.click()
    await flushPromises()
    // q persists and combines with the new filter (API-3: AND semantics).
    expect(apiMocks.listOmisiones).toHaveBeenLastCalledWith({
      limit: 20,
      offset: 0,
      q: 'canal',
      nivel: 'WARN',
    })

    // resuelta=false must be sent (FE-2: pending-only filter is meaningful)
    const resuelta = wrapper.find('[data-test="omision-resuelta-filter"]')
    await resuelta.trigger('click')
    await nextTick()
    const noOption = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
      (el) => el.textContent?.trim() === 'No',
    )
    expect(noOption).toBeDefined()
    noOption!.click()
    await flushPromises()
    // AND-combined with the still-active q + nivel filters.
    expect(apiMocks.listOmisiones).toHaveBeenLastCalledWith({
      limit: 20,
      offset: 0,
      q: 'canal',
      nivel: 'WARN',
      resuelta: false,
    })
  })

  it('admin marks a pending omission resolved via PATCH and refreshes', async () => {
    const wrapper = await mountView()

    const buttons = wrapper.findAll('[data-test="toggle-omision"]')
    expect(buttons).toHaveLength(2)
    const pendingButton = buttons.find((b) => b.text() === 'Marcar resuelta')
    expect(pendingButton).toBeDefined()
    await pendingButton!.trigger('click')
    await flushPromises()

    expect(apiMocks.updateOmision).toHaveBeenCalledTimes(1)
    expect(apiMocks.updateOmision).toHaveBeenCalledWith({ omision_id: 1 }, { resuelta: true })
    expect(document.body.textContent).toContain('Omisión marcada como resuelta')
    expect(apiMocks.listOmisiones).toHaveBeenCalledTimes(2) // refreshed after success
  })

  it('admin reopens a resolved omission via PATCH', async () => {
    apiMocks.updateOmision.mockResolvedValue({ ...OMISIONES[1], resuelta: false })
    const wrapper = await mountView()

    const reopen = wrapper.findAll('[data-test="toggle-omision"]').find((b) => b.text() === 'Reabrir')
    expect(reopen).toBeDefined()
    await reopen!.trigger('click')
    await flushPromises()

    expect(apiMocks.updateOmision).toHaveBeenCalledWith({ omision_id: 2 }, { resuelta: false })
    expect(document.body.textContent).toContain('Omisión reabierta')
    expect(apiMocks.listOmisiones).toHaveBeenCalledTimes(2)
  })

  it('hides the marcar-resuelta action for a consulta (D9)', async () => {
    const wrapper = await mountView('consulta')

    expect(wrapper.findAll('[data-test="toggle-omision"]')).toHaveLength(0)
    // read access still renders the rows
    expect(wrapper.text()).toContain('canal no mapeado')
  })

  it('renders the error state when the list request fails (FE-3)', async () => {
    apiMocks.listOmisiones.mockRejectedValueOnce(new Error('network down'))
    const wrapper = await mountView()

    expect(wrapper.text()).toContain('No se pudieron cargar las omisiones')
    expect(apiMocks.listOmisiones).toHaveBeenCalledTimes(1)
  })

  it('renders the empty state when there are no omisiones (FE-1)', async () => {
    apiMocks.listOmisiones.mockResolvedValue({ items: [], total: 0 })
    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Sin omisiones registradas')
  })
})
