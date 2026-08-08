/**
 * UsuarioForm component tests (PR11, spec MOD-5 usuarios).
 *
 * Admin-only user form, dual mode:
 *  - create: nombre, email, rol select (admin/operador/consulta) and
 *    password; empty nombre/email/rol/password each block submission, and a
 *    password under 6 chars is rejected (backend schema min_length=6)
 *  - edit: ROL-ONLY select prefilled from the row; submits the rol-only
 *    UsuarioUpdate (a self-demote attempt is rejected server-side with 400)
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import UsuarioForm from '@/components/usuarios/UsuarioForm.vue'
import type { components } from '@/types/api.d'

type UsuarioRead = components['schemas']['UsuarioRead']

const USUARIO: UsuarioRead = {
  id: 1,
  nombre: 'Ana Admin',
  email: 'ana@arpia.com.co',
  rol: 'admin',
}

async function mountForm(
  mode: 'create' | 'edit' = 'create',
  initial: UsuarioRead | null = null,
): Promise<VueWrapper> {
  const wrapper = mount(UsuarioForm, {
    props: { mode, initial },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  await flushPromises()
  return wrapper
}

async function pickRol(wrapper: VueWrapper, label: string): Promise<void> {
  const select = wrapper.find('[data-test="usuario-rol-select"]')
  await select.trigger('click')
  await nextTick()
  const item = [...document.querySelectorAll<HTMLElement>('.usuario-rol-popper .el-select-dropdown__item')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`rol option not found: "${label}"`)
  item.click()
  await nextTick()
  await flushPromises()
}

afterEach(() => {
  ElMessage.closeAll()
  document.body.innerHTML = ''
})

describe('UsuarioForm (MOD-5 usuarios)', () => {
  it('renders the four create fields and the three rol options', async () => {
    const wrapper = await mountForm('create')

    const text = wrapper.text()
    expect(text).toContain('Nombre')
    expect(text).toContain('Email')
    expect(text).toContain('Rol')
    expect(text).toContain('Contraseña')
    expect(wrapper.find('[data-test="usuario-nombre-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="usuario-email-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="usuario-password-input"]').exists()).toBe(true)

    await wrapper.find('[data-test="usuario-rol-select"]').trigger('click')
    await nextTick()
    const options = [...document.querySelectorAll<HTMLElement>('.usuario-rol-popper .el-select-dropdown__item')]
    expect(options.map((o) => o.textContent?.trim())).toEqual(['Administrador', 'Operador', 'Consulta'])
  })

  it('blocks create with an empty nombre', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="usuario-email-input"]').setValue('ana@arpia.com.co')
    await pickRol(wrapper, 'Operador')
    await wrapper.find('[data-test="usuario-password-input"]').setValue('clave123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe el nombre del usuario.')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create with an empty email', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="usuario-nombre-input"]').setValue('Ana')
    await pickRol(wrapper, 'Operador')
    await wrapper.find('[data-test="usuario-password-input"]').setValue('clave123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe el correo del usuario.')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create without a rol', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="usuario-nombre-input"]').setValue('Ana')
    await wrapper.find('[data-test="usuario-email-input"]').setValue('ana@arpia.com.co')
    await wrapper.find('[data-test="usuario-password-input"]').setValue('clave123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Selecciona el rol.')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create with an empty password', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="usuario-nombre-input"]').setValue('Ana')
    await wrapper.find('[data-test="usuario-email-input"]').setValue('ana@arpia.com.co')
    await pickRol(wrapper, 'Operador')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe la contraseña.')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks a password shorter than 6 characters (schema min_length=6)', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="usuario-nombre-input"]').setValue('Ana')
    await wrapper.find('[data-test="usuario-email-input"]').setValue('ana@arpia.com.co')
    await pickRol(wrapper, 'Operador')
    await wrapper.find('[data-test="usuario-password-input"]').setValue('abc12')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('La contraseña debe tener al menos 6 caracteres.')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact UsuarioCreate payload', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="usuario-nombre-input"]').setValue('  María Pérez ')
    await wrapper.find('[data-test="usuario-email-input"]').setValue('maria@arpia.com.co')
    await pickRol(wrapper, 'Operador')
    await wrapper.find('[data-test="usuario-password-input"]').setValue('clave123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      nombre: 'María Pérez',
      email: 'maria@arpia.com.co',
      rol: 'operador',
      password: 'clave123',
    })
  })

  it('edit mode renders ONLY the rol select prefilled and emits the rol-only update', async () => {
    const wrapper = await mountForm('edit', USUARIO)

    expect(wrapper.find('[data-test="usuario-nombre-input"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="usuario-password-input"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Administrador') // prefilled rol label

    await pickRol(wrapper, 'Consulta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ rol: 'consulta' })
  })
})
