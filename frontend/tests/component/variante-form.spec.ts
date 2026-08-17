/**
 * VarianteForm component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL VarianteForm with PrimeVue in both modes — the nested
 * variante create/edit form for ONE product:
 *  - create: nombre_variante + optional precio_venta; empty nombre blocks
 *    submission with a warning
 *  - a valid create emits VarianteProductoCreate, omitting precio_venta when
 *    null (the backend schema default) and keeping it when set
 *  - edit mode prefills from the row and emits the update payload
 * The view owns the POST/PUT, the admin-only gate and the refresh.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import VarianteForm from '@/components/productos/VarianteForm.vue'
import type { components } from '@/types/api.d'

type VarianteProductoRead = components['schemas']['VarianteProductoRead']

const VARIANTE: VarianteProductoRead = {
  id: 1,
  producto_id: 1,
  nombre_variante: 'Individual',
  precio_venta: '13000.00',
}

async function mountForm(
  mode: 'create' | 'edit' = 'create',
  initial: VarianteProductoRead | null = null,
): Promise<VueWrapper> {
  const wrapper = mount(VarianteForm, {
    props: { mode, initial },
    global: {
      plugins: [
        ElementPlus,
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  return wrapper
}

/** PrimeVue InputNumber commits the model on blur — type then blur like a user. */
async function setNumber(wrapper: VueWrapper, testId: string, value: string): Promise<void> {
  const input = wrapper.find(`[data-test="${testId}"] input`)
  await input.setValue(value)
  await input.trigger('blur')
  await nextTick()
}

afterEach(() => {
  ElMessage.closeAll()
})

describe('VarianteForm (MOD-5)', () => {
  it('renders the two fields in create mode', async () => {
    const wrapper = await mountForm('create')
    expect(wrapper.text()).toContain('Nombre de la variante')
    expect(wrapper.text()).toContain('Precio de venta')
  })

  it('blocks create submission with an empty nombre_variante', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Escribe el nombre de la variante')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact create payload, omitting precio_venta when null', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-variante-input"]').setValue('Docena')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({ nombre_variante: 'Docena' })
  })

  it('includes precio_venta when set', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="nombre-variante-input"]').setValue('Individual')
    await setNumber(wrapper, 'precio-variante-input', '13000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      nombre_variante: 'Individual',
      precio_venta: 13000,
    })
  })

  it('edit mode prefills the name and price and emits the update payload', async () => {
    const wrapper = await mountForm('edit', VARIANTE)

    expect((wrapper.find('[data-test="nombre-variante-input"]').element as HTMLInputElement).value).toBe(
      'Individual',
    )

    await wrapper.find('[data-test="nombre-variante-input"]').setValue('Individual premium')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      nombre_variante: 'Individual premium',
      precio_venta: 13000,
    })
  })
})