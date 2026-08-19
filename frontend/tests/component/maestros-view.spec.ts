/**
 * MaestrosView integration tests (PR11, spec MOD-5 maestros part).
 *
 * Mounts the REAL MaestrosView + the generic table/form components against
 * mocked clientesApi/tiposProductoApi/categoriasInsumosApi:
 * the three tabs (Clientes / Tipos de producto / Categorías de
 * insumos), the config-driven lists, role visibility (all master-data writes
 * are require_admin server-side — operador/consulta see read-only lists,
 * admin owns every form/action) and the per-entity CRUD round-trips: create
 * posts the exact schema payload, edit PUTs the update payload via the
 * inline edit form, delete expects 204 and surfaces the tipos-producto 409
 * "in use".
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage, ElMessageBox } from 'element-plus'
import Paginator from 'primevue/paginator'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import { useAuthStore } from '@/stores/auth'
import MaestrosView from '@/views/MaestrosView.vue'

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    listClientes: vi.fn(),
    createCliente: vi.fn(),
    updateCliente: vi.fn(),
    deleteCliente: vi.fn(),
    listTipos: vi.fn(),
    createTipo: vi.fn(),
    updateTipo: vi.fn(),
    deleteTipo: vi.fn(),
    listCategorias: vi.fn(),
    createCategoria: vi.fn(),
    updateCategoria: vi.fn(),
    deleteCategoria: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  clientesApi: {
    list: apiMocks.listClientes,
    create: apiMocks.createCliente,
    update: apiMocks.updateCliente,
    delete: apiMocks.deleteCliente,
  },
  tiposProductoApi: {
    list: apiMocks.listTipos,
    create: apiMocks.createTipo,
    update: apiMocks.updateTipo,
    delete: apiMocks.deleteTipo,
  },
  categoriasInsumosApi: {
    list: apiMocks.listCategorias,
    create: apiMocks.createCategoria,
    update: apiMocks.updateCategoria,
    delete: apiMocks.deleteCategoria,
  },
}))

const CLIENTES = [
  { id: 1, nombre: 'Ana Torres', documento_identidad: 'CC 123', email: 'ana@arpia.com.co', telefono: '3001234567', created_at: '2026-01-01T10:00:00Z' },
  { id: 2, nombre: 'Luis Gómez', documento_identidad: null, email: null, telefono: null, created_at: '2026-01-02T10:00:00Z' },
]
const TIPOS = [{ id: 1, nombre: 'Alimentos' }]
const CATEGORIAS = [{ id: 1, nombre: 'Granos' }]

async function mountView(rol: string): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 2, nombre: 'Pepe', email: 'pepe@arpia.com.co', rol },
  })
  const wrapper = mount(MaestrosView, {
    global: {
      plugins: [
        pinia,
        ElementPlus,
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
      stubs: { transition: false },
    },
  })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

/** Click the PrimeVue Tab with the given label (panels stay mounted). */
async function activateTab(wrapper: VueWrapper, label: string): Promise<void> {
  const item = wrapper.findAll('.p-tab').find((i) => i.text().trim() === label)
  if (!item) throw new Error(`tab not found: "${label}"`)
  await item.trigger('click')
  await nextTick()
  await flushPromises()
}

/** Let the el-dialog leave transition finish (Vue's nextFrame is a double rAF). */
async function flushDialogTransition(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

describe('MaestrosView (MOD-5 + T6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Every list uses the {items,total} contract now.
    apiMocks.listClientes.mockResolvedValue({ items: CLIENTES, total: 2 })
    apiMocks.listTipos.mockResolvedValue({ items: TIPOS, total: 1 })
    apiMocks.listCategorias.mockResolvedValue({ items: CATEGORIAS, total: 1 })
    apiMocks.createCliente.mockResolvedValue(CLIENTES[0])
    apiMocks.updateCliente.mockResolvedValue(CLIENTES[0])
    apiMocks.deleteCliente.mockResolvedValue(undefined)
    apiMocks.createTipo.mockResolvedValue(TIPOS[0])
    apiMocks.updateTipo.mockResolvedValue(TIPOS[0])
    apiMocks.deleteTipo.mockResolvedValue(undefined)
    apiMocks.createCategoria.mockResolvedValue(CATEGORIAS[0])
    apiMocks.updateCategoria.mockResolvedValue(CATEGORIAS[0])
    apiMocks.deleteCategoria.mockResolvedValue(undefined)
  })

  afterEach(() => {
    ElMessage.closeAll()
    vi.restoreAllMocks()
  })

  it('renders the three tabs and loads all three lists (paged) for an operador', async () => {
    const wrapper = await mountView('operador')

    const text = wrapper.text()
    expect(text).toContain('Clientes')
    expect(text).toContain('Tipos de producto')
    expect(text).toContain('Categorías de insumos')

    expect(text).toContain('Ana Torres')
    expect(text).toContain('Luis Gómez')
    expect(text).toContain('Alimentos')
    expect(text).toContain('Granos')

    // Each entity list fetches its page (page 1, pageSize 20).
    const PAGE1 = { limit: 20, offset: 0 }
    expect(apiMocks.listClientes).toHaveBeenCalledTimes(1)
    expect(apiMocks.listClientes).toHaveBeenCalledWith(PAGE1)
    expect(apiMocks.listTipos).toHaveBeenCalledWith(PAGE1)
    expect(apiMocks.listCategorias).toHaveBeenCalledWith(PAGE1)
  })

  it('renders an em dash for empty optional fields', async () => {
    const wrapper = await mountView('operador')

    expect(wrapper.text()).toContain('—')
  })

  it('pages a maestro table and refetches with the new offset', async () => {
    const wrapper = await mountView('operador')
    expect(apiMocks.listClientes).toHaveBeenCalledWith({ limit: 20, offset: 0 })

    wrapper.findComponent(Paginator).vm.$emit('page', { first: 20, rows: 20 })
    await flushPromises()
    expect(apiMocks.listClientes).toHaveBeenCalledWith({ limit: 20, offset: 20 })
  })

  it('global q on a maestro tab resets to page 1 and refetches with q', async () => {
    const wrapper = await mountView('operador')

    const input = wrapper.find('[data-test="maestro-search-clientes"]')
    await input.setValue('ana')
    await input.trigger('keyup.enter')
    await flushPromises()

    expect(apiMocks.listClientes).toHaveBeenCalledWith({ limit: 20, offset: 0, q: 'ana' })
  })

  it('operador and consulta see read-only lists — no forms, no actions', async () => {
    const wrapper = await mountView('operador')

    expect(wrapper.findAllComponents({ name: 'MaestroForm' })).toHaveLength(0)
    expect(wrapper.findAll('[data-test^="nuevo-"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="edit-maestro"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-maestro"]')).toHaveLength(0)

    const consulta = await mountView('consulta')
    expect(consulta.findAllComponents({ name: 'MaestroForm' })).toHaveLength(0)
  })

  it('admin owns one dialog button per entity and the edit/delete actions on every row', async () => {
    const wrapper = await mountView('admin')

    // The forms live in el-dialogs — closed until a button opens them (FE-DLG-1).
    expect(wrapper.findAllComponents({ name: 'MaestroForm' })).toHaveLength(0)
    expect(wrapper.findAll('[data-test^="nuevo-"]')).toHaveLength(3)
    // 2 clientes + 1 tipo + 1 categoria = 4 rows with actions.
    expect(wrapper.findAll('[data-test="edit-maestro"]')).toHaveLength(4)
    expect(wrapper.findAll('[data-test="delete-maestro"]')).toHaveLength(4)
  })

  it('creates a cliente via the dialog with the exact ClienteCreate payload and refreshes', async () => {
    const wrapper = await mountView('admin')
    expect(apiMocks.listClientes).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-test="nuevo-clientes"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'MaestroForm' }).exists()).toBe(true)

    wrapper
      .findAllComponents({ name: 'MaestroForm' })[0]
      .vm.$emit('submit', { nombre: 'Sara López', documento_identidad: 'CC 456', email: '', telefono: '311555' })
    await flushPromises()

    expect(apiMocks.createCliente).toHaveBeenCalledTimes(1)
    expect(apiMocks.createCliente).toHaveBeenCalledWith({
      nombre: 'Sara López',
      documento_identidad: 'CC 456',
      email: null,
      telefono: '311555',
    })
    expect(document.body.textContent).toContain('Se creó Cliente correctamente')
    expect(apiMocks.listClientes).toHaveBeenCalledTimes(2)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'MaestroForm' }).exists()).toBe(false)
  })

  it('cancels a create dialog without submitting (FE-DLG-2/3)', async () => {
    const wrapper = await mountView('admin')

    await wrapper.find('[data-test="nuevo-tipos-producto"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'MaestroForm' }).exists()).toBe(true)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushDialogTransition()

    expect(apiMocks.createTipo).not.toHaveBeenCalled()
    expect(wrapper.findComponent({ name: 'MaestroForm' }).exists()).toBe(false)
  })

  it('deletes a tipo de producto after the confirm dialog (204) and refreshes', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    const wrapper = await mountView('admin')
    await activateTab(wrapper, 'Tipos de producto')
    expect(apiMocks.listTipos).toHaveBeenCalledTimes(1)

    await wrapper.findAll('[data-test="delete-maestro"]')[2].trigger('click') // the only tipo row
    await flushPromises()

    expect(apiMocks.deleteTipo).toHaveBeenCalledTimes(1)
    expect(apiMocks.deleteTipo).toHaveBeenCalledWith({ tipo_producto_id: 1 })
    expect(document.body.textContent).toContain('Se eliminó Tipo de producto correctamente')
    expect(apiMocks.listTipos).toHaveBeenCalledTimes(2)
  })

  it('surfaces the 409 when deleting a tipo that is in use', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    apiMocks.deleteTipo.mockRejectedValueOnce({
      response: { data: { detail: 'TipoProducto is in use and cannot be deleted' } },
    })
    const wrapper = await mountView('admin')
    await activateTab(wrapper, 'Tipos de producto')

    await wrapper.findAll('[data-test="delete-maestro"]')[2].trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('TipoProducto is in use and cannot be deleted')
    expect(apiMocks.listTipos).toHaveBeenCalledTimes(1) // no refresh after failure
  })

  it('creates a categoria de insumos via the dialog with the exact payload', async () => {
    const wrapper = await mountView('admin')
    await activateTab(wrapper, 'Categorías de insumos')

    await wrapper.find('[data-test="nuevo-categorias-insumos"]').trigger('click')
    await nextTick()
    wrapper.findAllComponents({ name: 'MaestroForm' })[0].vm.$emit('submit', { nombre: 'Lácteos' })
    await flushPromises()

    expect(apiMocks.createCategoria).toHaveBeenCalledTimes(1)
    expect(apiMocks.createCategoria).toHaveBeenCalledWith({ nombre: 'Lácteos' })
    expect(document.body.textContent).toContain('Se creó Categoría de insumos correctamente')
    expect(apiMocks.listCategorias).toHaveBeenCalledTimes(2)
  })
})
