/**
 * SociosForm component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL SociosForm with Element Plus in both modes:
 *  - create: nombre + porcentaje fields; empty nombre and empty porcentaje
 *    each block submission with a warning
 *  - edit: percentage only (the backend SocioConfiguracionUpdate schema has
 *    NO nombre — the partner name is not updatable)
 *  - a valid create emits the exact SocioConfiguracionCreate body; a valid
 *    edit emits the exact SocioConfiguracionUpdate body
 * The view owns the POST/PATCH, the 422 sum-to-100 surfacing and the refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import SociosForm from '@/components/finanzas/SociosForm.vue'
import type { components } from '@/types/api.d'

type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']

const SOCIO: SocioConfiguracionRead = { id: 1, nombre: 'Ana María', porcentaje_participacion: '60.00' }

async function mountForm(mode: 'create' | 'edit' = 'create', initial: SocioConfiguracionRead | null = null): Promise<VueWrapper> {
  const wrapper = mount(SociosForm, {
    props: { mode, initial },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

afterEach(() => {
  ElMessage.closeAll()
})

describe('SociosForm (MOD-3)', () => {
  it('renders nombre + porcentaje in create mode', async () => {
    const wrapper = await mountForm('create')

    const text = wrapper.text()
    expect(text).toContain('Nombre del socio')
    expect(text).toContain('Porcentaje de participación')
  })

  it('blocks create submission with an empty nombre', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="porcentaje-socio-input"] input').setValue('25')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe el nombre del socio')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('blocks create submission with an empty porcentaje', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-socio-input"]').setValue('Luis Vega')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('El porcentaje debe ser mayor a cero')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact create payload', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-socio-input"]').setValue('Luis Vega')
    await wrapper.find('[data-test="porcentaje-socio-input"] input').setValue('25')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ nombre: 'Luis Vega', porcentaje_participacion: 25 })
  })

  it('edit mode shows the name read-only and edits the percentage only', async () => {
    const wrapper = await mountForm('edit', SOCIO)

    const text = wrapper.text()
    expect(text).toContain('Ana María')
    expect(wrapper.find('[data-test="nombre-socio-input"]').exists()).toBe(false)

    await wrapper.find('[data-test="porcentaje-socio-input"] input').setValue('20')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ porcentaje_participacion: 20 })
  })

  it('blocks edit submission when the percentage is cleared', async () => {
    const wrapper = await mountForm('edit', SOCIO)

    // Edit mode prefills the share from the row — the gate fires only after
    // the user clears the field (el-input-number empties to null).
    const input = wrapper.find('[data-test="porcentaje-socio-input"] input')
    await input.setValue('')
    await input.trigger('change')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('El porcentaje debe ser mayor a cero')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })
})
