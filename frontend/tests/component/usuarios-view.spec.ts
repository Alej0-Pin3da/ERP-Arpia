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
  const wrapper = mount(UsuariosView, { global: { plugins: [pinia, ElementPlus] } })
  await nextTick()
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('UsuariosView (MOD-5 usuarios)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMocks.list.mockResolvedValue(USUARIOS)
    apiMocks.create.mockResolvedValue(USUARIOS[0])
    apiMocks.update.mockResolvedValue({ ...USUARIOS[2], rol: 'consulta' })
    apiMocks.delete.mockResolvedValue(undefined)
  })

  afterEach(() => {
    ElMessage.closeAll()
    vi.restoreAllMocks()
  })

  it('renders the user list with es-CO rol labels and requests limit 1000', async () => {
    const wrapper = await mountView()

    const text = wrapper.text()
    expect(text).toContain('Ana Admin')
    expect(text).toContain('pepe@arpia.com.co')
    expect(text).toContain('Administrador')
    expect(text).toContain('Operador')
    expect(text).toContain('Consulta')

    expect(apiMocks.list).toHaveBeenCalledTimes(1)
    expect(apiMocks.list).toHaveBeenCalledWith({ limit: 1000 })
  })

  it('hides the delete action on the self row but keeps edit', async () => {
    const wrapper = await mountView()

    // 3 users, self = id 1 -> only 2 delete buttons.
    expect(wrapper.findAll('[data-test="delete-usuario"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="edit-usuario"]')).toHaveLength(3)
  })

  it('creates a user with the exact UsuarioCreate payload and refreshes', async () => {
    const wrapper = await mountView()
    expect(apiMocks.list).toHaveBeenCalledTimes(1)

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
  })

  it('surfaces the 400 when the email is already registered', async () => {
    apiMocks.create.mockRejectedValueOnce({ response: { data: { detail: 'Email already registered' } } })
    const wrapper = await mountView()

    wrapper.findComponent({ name: 'UsuarioForm' }).vm.$emit('submit', {
      nombre: 'María Pérez',
      email: 'maria@arpia.com.co',
      rol: 'operador',
      password: 'clave123',
    })
    await flushPromises()

    expect(document.body.textContent).toContain('Email already registered')
    expect(apiMocks.list).toHaveBeenCalledTimes(1) // no refresh after failure
  })

  it('edits another user rol via the inline form (rol-only PATCH) and refreshes', async () => {
    const wrapper = await mountView()

    await wrapper.findAll('[data-test="edit-usuario"]')[2].trigger('click') // Coni (id 3)
    await nextTick()
    expect(wrapper.text()).toContain('Editar usuario')

    wrapper.findComponent({ name: 'UsuarioForm' }).vm.$emit('submit', { rol: 'operador' })
    await flushPromises()

    expect(apiMocks.update).toHaveBeenCalledTimes(1)
    expect(apiMocks.update).toHaveBeenCalledWith({ usuario_id: 3 }, { rol: 'operador' })
    expect(document.body.textContent).toContain('Usuario actualizado correctamente')
    expect(wrapper.text()).toContain('Crear usuario') // back to create form
    expect(apiMocks.list).toHaveBeenCalledTimes(2)
  })

  it('surfaces the server 400 when the admin tries to demote self', async () => {
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
