/**
 * MaestroForm component tests (PR11, spec MOD-5).
 *
 * The generic form renders one input per field config entry:
 *  - required fields block submission with an es-CO warning
 *  - a valid create emits the RAW values (the view builds the typed payload
 *    via the per-entity builders in utils/maestros)
 *  - edit prefills every field from the row and emits the current values
 *  - email fields render a native email input; name-only entities render a
 *    single field
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import MaestroForm from '@/components/maestros/MaestroForm.vue'
import {
  MAESTRO_ENTITIES,
  type MaestroEntityConfig,
  type MaestroRow,
} from '@/utils/maestros'

const CLIENTE_CONFIG = MAESTRO_ENTITIES[0]
const TIPO_CONFIG = MAESTRO_ENTITIES[1]

const CLIENTE_ROW: MaestroRow = {
  id: 1,
  nombre: 'Ana Torres',
  documento_identidad: 'CC 123',
  email: 'ana@arpia.com.co',
  telefono: '3001234567',
}

async function mountForm(
  mode: 'create' | 'edit' = 'create',
  config: MaestroEntityConfig = CLIENTE_CONFIG,
  initial: MaestroRow | null = null,
): Promise<VueWrapper> {
  const wrapper = mount(MaestroForm, {
    props: { mode, fields: config.fields, singular: config.singular, initial },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  await flushPromises()
  return wrapper
}

afterEach(() => {
  ElMessage.closeAll()
})

describe('MaestroForm (MOD-5)', () => {
  it('renders one input per field config entry with the es-CO labels', async () => {
    const wrapper = await mountForm('create')

    const text = wrapper.text()
    expect(text).toContain('Nombre')
    expect(text).toContain('Documento de identidad')
    expect(text).toContain('Email')
    expect(text).toContain('Teléfono')
    expect(wrapper.find('[data-test="maestro-nombre-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="maestro-documento_identidad-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="maestro-email-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="maestro-telefono-input"]').exists()).toBe(true)
  })

  it('renders the email field as a native email input', async () => {
    const wrapper = await mountForm('create')

    expect((wrapper.find('[data-test="maestro-email-input"]').element as HTMLInputElement).type).toBe('email')
  })

  it('renders a single field for a name-only entity', async () => {
    const wrapper = await mountForm('create', TIPO_CONFIG)

    expect(wrapper.find('[data-test="maestro-nombre-input"]').exists()).toBe(true)
    expect(wrapper.findAll('input')).toHaveLength(1)
    expect(wrapper.text()).toContain('Crear Tipo de producto')
  })

  it('blocks create submission when the required nombre is empty', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Nombre es obligatorio.')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the raw values for a valid create (optionals left empty)', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="maestro-nombre-input"]').setValue('Ana Torres')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      nombre: 'Ana Torres',
      documento_identidad: '',
      email: '',
      telefono: '',
    })
  })

  it('emits the raw values with filled optional fields', async () => {
    const wrapper = await mountForm('create')

    await wrapper.find('[data-test="maestro-nombre-input"]').setValue('Ana Torres')
    await wrapper.find('[data-test="maestro-documento_identidad-input"]').setValue('CC 123')
    await wrapper.find('[data-test="maestro-email-input"]').setValue('ana@arpia.com.co')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      nombre: 'Ana Torres',
      documento_identidad: 'CC 123',
      email: 'ana@arpia.com.co',
      telefono: '',
    })
  })

  it('edit mode prefills every field from the row and emits the current values', async () => {
    const wrapper = await mountForm('edit', CLIENTE_CONFIG, CLIENTE_ROW)

    expect((wrapper.find('[data-test="maestro-nombre-input"]').element as HTMLInputElement).value).toBe('Ana Torres')
    expect((wrapper.find('[data-test="maestro-documento_identidad-input"]').element as HTMLInputElement).value).toBe('CC 123')

    await wrapper.find('[data-test="maestro-nombre-input"]').setValue('Ana Torres R.')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('submit')![0][0]).toEqual({
      nombre: 'Ana Torres R.',
      documento_identidad: 'CC 123',
      email: 'ana@arpia.com.co',
      telefono: '3001234567',
    })
  })
})