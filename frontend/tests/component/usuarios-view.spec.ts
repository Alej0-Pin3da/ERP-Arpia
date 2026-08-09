/**
 * UsuariosView integration tests (PR11, spec MOD-5 usuarios part).
 *
 * Mounts the REAL UsuariosView + UsuariosTable/UsuarioForm against mocked
 * usuariosApi (admin-only module — the route guard already blocks
 * non-admins in guards.spec):
 *  - list renders id/nombre/email + es-CO rol labels (limit 1000)
 *  - create posts the exact UsuarioCreate; a 400 "Email already registered"
 *    is surfaced
 *  - edit changes the rol via the inline form (rol-only PATCH payload)
 *  - self-protection: the self row has NO delete action ("can't delete
 *    self"), and a forced self-demote surfaces the server 400 "Cannot
 *    change your own role away from admin"
 *  - delete other users after a confirm (204)
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus, { ElMessage, ElMessageBox } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'
import UsuariosView from '@/views/UsuariosView.vue'

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))
vi.mock('@/api/endpoints', () => ({
  usuariosApi: {
    list: apiMocks.list,
    create: apiMocks.create,
    update: apiMocks.update,
    delete: apiMocks.delete,
  },
}))

const USUARIOS = [
  { id: 1, nombre: 'Ana Admin', email: 'ana@arpia.com.co', rol: 'admin' },
  { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol: 'operador' },
  { id: 3, nombre: 'Coni Consulta', email: 'coni@arpia.com.co', rol: 'consulta' },
]

async function mountView(): Promise<VueWrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore()
  // The session user IS the admin (id 1) — the self row is id 1.
  auth.$patch({
    accessToken: 'acc-1',
    refreshToken: 'ref-1',
    user: { id: 1, nombre: 'Ana Admin', email: 'ana@arpia.com.co', rol: 'admin' },
  })
  const wrapper = mount(UsuariosView, {
    global: { plugins: [pinia, ElementPlus], stubs: { transition: false } },
  })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

/** Let the el-dialog leave transition finish (Vue's nextFrame is a double rAF). */
async function flushDialogTransition(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

describe('UsuariosView (MOD-5 usuarios + T6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMocks.list.mockResolvedValue({ items: USUARIOS, total: 3 })
    apiMocks.create.mockResolvedValue(USUARIOS[0])
    apiMocks.update.mockResolvedValue({ ...USUARIOS[2], rol: 'consulta' })
    apiMocks.delete.mockResolvedValue(undefined)
  })

  afterEach(() => {
    ElMessage.closeAll()
    vi.restoreAllMocks()
  })

  it('renders the user list with es-CO rol labels and requests the paged list', async () => {
    const wrapper = await mountView()

    const text = wrapper.text()
    expect(text).toContain('Ana Admin')
    expect(text).toContain('pepe@arpia.com.co')
    expect(text).toContain('Administrador')
    expect(text).toContain('Operador')
    expect(text).toContain('Consulta')

    expect(apiMocks.list).toHaveBeenCalledTimes(1)
    expect(apiMocks.list).toHaveBeenCalledWith({ limit: 20, offset: 0 })
  })

  it('renders el-pagination and pages with the new offset', async () => {
    const wrapper = await mountView()
    expect(wrapper.findComponent({ name: 'ElPagination' }).exists()).toBe(true)
    expect(apiMocks.list).toHaveBeenCalledWith({ limit: 20, offset: 0 })

    wrapper.findComponent({ name: 'ElPagination' }).vm.$emit('current-change', 2)
    await flushPromises()
    expect(apiMocks.list).toHaveBeenCalledWith({ limit: 20, offset: 20 })
  })

  it('global q and rol filter reset to page 1 and refetch with the params', async () => {
    const wrapper = await mountView()

    const input = wrapper.find('[data-test="usuario-search"]')
    await input.setValue('ana')
    await input.trigger('keyup.enter')
    await flushPromises()
    expect(apiMocks.list).toHaveBeenCalledWith({ limit: 20, offset: 0, q: 'ana' })

    // Clear the q (clear icon) so the rol filter call is isolated.
    await input.setValue('')
    await input.trigger('keyup.enter')
    await flushPromises()

    const select = wrapper.find('[data-test="usuario-rol-filter"]')
    await select.trigger('click')
    await nextTick()
    const option = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
      (el) => el.textContent?.trim() === 'Operador',
    )
    expect(option).toBeDefined()
    option!.click()
    await flushPromises()
    expect(apiMocks.list).toHaveBeenLastCalledWith({ limit: 20, offset: 0, rol: 'operador' })
  })

  it('hides the delete action on the self row but keeps edit', async () => {
    const wrapper = await mountView()

    // 3 users, self = id 1 -> only 2 delete buttons.
    expect(wrapper.findAll('[data-test="delete-usuario"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="edit-usuario"]')).toHaveLength(3)
  })

  it('opens the create dialog, creates a user with the exact UsuarioCreate payload and refreshes', async () => {
    const wrapper = await mountView()
    expect(apiMocks.list).toHaveBeenCalledTimes(1)

    // The form lives in an el-dialog opened from the toolbar button (FE-DLG-1).
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(false)
    await wrapper.find('[data-test="nuevo-usuario"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'UsuarioForm' }).vm.$emit('submit', {
      nombre: 'María Pérez',
      email: 'maria@arpia.com.co',
      rol: 'operador',
      password: 'clave123',
    })
    await flushPromises()

    expect(apiMocks.create).toHaveBeenCalledTimes(1)
    expect(apiMocks.create).toHaveBeenCalledWith({
      nombre: 'María Pérez',
      email: 'maria@arpia.com.co',
      rol: 'operador',
      password: 'clave123',
    })
    expect(document.body.textContent).toContain('Usuario creado correctamente')
    expect(apiMocks.list).toHaveBeenCalledTimes(2)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(false)
  })

  it('surfaces the 400 when the email is already registered and keeps the dialog open (FE-DLG-2)', async () => {
    apiMocks.create.mockRejectedValueOnce({ response: { data: { detail: 'Email already registered' } } })
    const wrapper = await mountView()

    await wrapper.find('[data-test="nuevo-usuario"]').trigger('click')
    await nextTick()
    wrapper.findComponent({ name: 'UsuarioForm' }).vm.$emit('submit', {
      nombre: 'María Pérez',
      email: 'maria@arpia.com.co',
      rol: 'operador',
      password: 'clave123',
    })
    await flushPromises()

    expect(document.body.textContent).toContain('Email already registered')
    expect(apiMocks.list).toHaveBeenCalledTimes(1) // no refresh after failure
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(true) // stays open
  })

  it('edits another user rol via the edit dialog (rol-only PATCH) and refreshes', async () => {
    const wrapper = await mountView()

    await wrapper.findAll('[data-test="edit-usuario"]')[2].trigger('click') // Coni (id 3)
    await nextTick()
    expect(wrapper.text()).toContain('Editar usuario')
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(true)

    wrapper.findComponent({ name: 'UsuarioForm' }).vm.$emit('submit', { rol: 'operador' })
    await flushPromises()

    expect(apiMocks.update).toHaveBeenCalledTimes(1)
    expect(apiMocks.update).toHaveBeenCalledWith({ usuario_id: 3 }, { rol: 'operador' })
    expect(document.body.textContent).toContain('Usuario actualizado correctamente')
    expect(apiMocks.list).toHaveBeenCalledTimes(2)
    // Success closes the dialog (FE-DLG-2).
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(false)
  })

  it('surfaces the server 400 when the admin tries to demote self and keeps the dialog open', async () => {
    apiMocks.update.mockRejectedValueOnce({
      response: { data: { detail: 'Cannot change your own role away from admin' } },
    })
    const wrapper = await mountView()

    await wrapper.findAll('[data-test="edit-usuario"]')[0].trigger('click') // self (id 1)
    await nextTick()

    wrapper.findComponent({ name: 'UsuarioForm' }).vm.$emit('submit', { rol: 'operador' })
    await flushPromises()

    expect(document.body.textContent).toContain('Cannot change your own role away from admin')
    expect(apiMocks.list).toHaveBeenCalledTimes(1) // account remains admin, no refresh
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(true) // stays open
  })

  it('cancels the create dialog without submitting (FE-DLG-2/3)', async () => {
    const wrapper = await mountView()

    await wrapper.find('[data-test="nuevo-usuario"]').trigger('click')
    await nextTick()
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(true)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushDialogTransition()

    expect(apiMocks.create).not.toHaveBeenCalled()
    expect(wrapper.findComponent({ name: 'UsuarioForm' }).exists()).toBe(false)
  })

  it('deletes another user after the confirm dialog (204) and refreshes', async () => {
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
    const wrapper = await mountView()

    await wrapper.findAll('[data-test="delete-usuario"]')[0].trigger('click') // Pepe (id 2)
    await flushPromises()

    expect(apiMocks.delete).toHaveBeenCalledTimes(1)
    expect(apiMocks.delete).toHaveBeenCalledWith({ usuario_id: 2 })
    expect(document.body.textContent).toContain('Usuario eliminado correctamente')
    expect(apiMocks.list).toHaveBeenCalledTimes(2)
  })
})
