/**
 * Ventas register form component tests (task 2.2, spec MOD-1).
 *
 * Mounts the REAL VentasForm with PrimeVue and drives it through real user
 * interaction (Select dropdowns, InputNumber fields):
 *  - empty detalles blocks submission with a warning and emits nothing
 *  - selecting a product auto-fills precio_unitario from
 *    precio_venta_sugerido and loads its variantes
 *  - a valid form emits the exact VentaCreate POST body
 *  - the client-side total preview mirrors the server total
 *    (subtotal * (1 - descuento/100))
 *
 * Migrated to PrimeVue (slice 2a): dropdown options are `.p-select-option`
 * (teleported to body), input-number commits on blur, ToggleSwitch toggles
 * through its inner checkbox. el-button migrated to PrimeVue in slice 2b.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import { clearToastHost, mountToastHost } from '../helpers/toast-host'
import esCO from '@/utils/locales/es-CO'
import VentasForm from '@/components/ventas/VentasForm.vue'
import type { VentaCreate } from '@/utils/ventas'
import type { components } from '@/types/api.d'

type ClienteRead = components['schemas']['ClienteRead']
type ProductoRead = components['schemas']['ProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']
type VentaRead = components['schemas']['VentaRead']

const PRODUCTOS: ProductoRead[] = [
  {
    id: 1,
    tipo_producto_id: 1,
    nombre: 'Arepa de huevo',
    requiere_fabricacion: true,
    costos_operativos_fijos: '0',
    precio_venta_sugerido: '5000',
  },
  {
    id: 2,
    tipo_producto_id: 1,
    nombre: 'Jugo de naranja',
    requiere_fabricacion: false,
    costos_operativos_fijos: '0',
    precio_venta_sugerido: '8000',
  },
  {
    id: 3,
    tipo_producto_id: 1,
    nombre: 'Caja Saca Las Garras',
    requiere_fabricacion: true,
    costos_operativos_fijos: '0',
    precio_venta_sugerido: '12000',
  },
]

const CLIENTES: ClienteRead[] = [
  {
    id: 7,
    nombre: 'Juan Pérez',
    documento_identidad: null,
    email: null,
    telefono: null,
    created_at: '2026-01-01T00:00:00Z',
  },
]

const VARIANTES: VarianteProductoRead[] = [
  { id: 5, producto_id: 1, nombre_variante: 'Grande', precio_venta: '6000' },
]

/** Fixture variant loader: product 1 is sized (has variants); 2 and 3 load none. */
const loadVariantes = vi.fn().mockImplementation(
  (productoId: number): Promise<VarianteProductoRead[]> =>
    Promise.resolve(productoId === 1 ? VARIANTES : []),
)

/** A completed venta used as the `initial` prefill for edit mode. */
const VENTA_EDIT: VentaRead = {
  id: 10,
  fecha: '2026-08-01T10:30:00Z',
  cliente_id: 7,
  canal_venta: 'whatsapp',
  descuento_porcentaje: '5',
  estado: 'completada',
  es_regalo: false,
  total_venta: '9500.00',
  detalles: [
    {
      id: 1,
      producto_id: 1,
      variante_id: 5,
      cantidad: '2',
      precio_unitario_aplicado: '5000.00',
      costo_unitario_aplicado: '2000.00',
    },
  ],
}

/** VV-1 edit prefill: a sized product line whose stored variant is NULL. */
const VENTA_EDIT_SIN_VARIANTE: VentaRead = {
  id: 11,
  fecha: '2026-08-02T10:30:00Z',
  cliente_id: null,
  canal_venta: 'web',
  descuento_porcentaje: '0',
  estado: 'completada',
  es_regalo: false,
  total_venta: '10000.00',
  detalles: [
    {
      id: 2,
      producto_id: 1,
      variante_id: null,
      cantidad: '2',
      precio_unitario_aplicado: '5000.00',
      costo_unitario_aplicado: '2000.00',
    },
  ],
}

async function mountForm(saving = false): Promise<VueWrapper> {
  const wrapper = mount(VentasForm, {
    props: { productos: PRODUCTOS, clientes: CLIENTES, loadVariantes, saving },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  return wrapper
}

async function mountEditForm(initial: VentaRead = VENTA_EDIT): Promise<VueWrapper> {
  const wrapper = mount(VentasForm, {
    props: {
      productos: PRODUCTOS,
      clientes: CLIENTES,
      loadVariantes,
      mode: 'edit',
      initial,
      saving: false,
    },
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

/** Let a PrimeVue Select overlay open (Teleport + transition) before interacting. */
async function flushOverlay(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

/** Open a Select by its data-test and click the option with the label. */
async function pickOption(select: ReturnType<VueWrapper['find']>, label: string): Promise<void> {
  await select.trigger('click')
  await flushOverlay()
  const item = [...document.querySelectorAll<HTMLElement>('.p-select-option')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`dropdown option not found: "${label}"`)
  item.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
  await flushOverlay()
  await nextTick()
}

/** PrimeVue InputNumber commits the model on blur — type then blur like a user. */
async function setNumber(wrapper: VueWrapper, testId: string, value: string): Promise<void> {
  const input = wrapper.find(`[data-test="${testId}"] input`)
  await input.setValue(value)
  await input.trigger('blur')
  await nextTick()
}

mountToastHost()

afterEach(() => {
  clearToastHost()
})

describe('VentasForm (MOD-1 register)', () => {
  it('renders cliente/canal/descuento fields, one default detail row and a zero preview', async () => {
    const wrapper = await mountForm()

    const text = wrapper.text()
    expect(text).toContain('Cliente')
    expect(text).toContain('Canal de venta')
    expect(text).toContain('Descuento')
    expect(wrapper.findAll('[data-test="detalle-row"]')).toHaveLength(1)
    expect(text).toContain('Total')
    expect(text).toContain('$0,00')

    // Canal dropdown lists the four channels.
    await pickOption(wrapper.find('[data-test="canal-select"]'), 'WhatsApp')
    expect(wrapper.find('[data-test="canal-select"]').text()).toContain('WhatsApp')
  })

  it('selecting a product defaults precio_unitario from precio_venta_sugerido and loads variantes', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo')

    const precioInput = wrapper.find('[data-test="precio-input"] input')
    expect((precioInput.element as HTMLInputElement).value).toBe('5000')
    expect(loadVariantes).toHaveBeenCalledWith(1)

    // The variante dropdown now offers the loaded variant.
    await pickOption(wrapper.find('[data-test="variante-select"]'), 'Grande')
    expect(wrapper.find('[data-test="variante-select"]').text()).toContain('Grande')
  })

  it('adds and removes dynamic detail rows', async () => {
    const wrapper = await mountForm()

    await wrapper.find('[data-test="add-detalle"]').trigger('click')
    await nextTick()
    expect(wrapper.findAll('[data-test="detalle-row"]')).toHaveLength(2)

    await wrapper.findAll('[data-test="remove-detalle"]')[0].trigger('click')
    await nextTick()
    expect(wrapper.findAll('[data-test="detalle-row"]')).toHaveLength(1)
  })

  it('blocks submission when there is no complete detail and emits nothing', async () => {
    const wrapper = await mountForm()

    // Remove the only (empty) row -> no valid detalles at all.
    await wrapper.findAll('[data-test="remove-detalle"]')[0].trigger('click')
    await nextTick()
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('Agrega al menos un detalle')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits the exact VentaCreate payload for a fully filled form', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="cliente-select"]'), 'Juan Pérez')
    await pickOption(wrapper.find('[data-test="canal-select"]'), 'WhatsApp')
    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo')
    await pickOption(wrapper.find('[data-test="variante-select"]'), 'Grande')
    await setNumber(wrapper, 'cantidad-input', '2')
    await setNumber(wrapper, 'descuento-input', '5')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0]).toEqual({
      cliente_id: 7,
      canal_venta: 'whatsapp',
      descuento_porcentaje: 5,
      es_regalo: false,
      detalles: [{ producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 }],
    })
  })

  it('updates the total preview with cantidad x precio minus the percentage discount', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo') // 5000
    await setNumber(wrapper, 'cantidad-input', '2') // subtotal 10000
    await setNumber(wrapper, 'descuento-input', '10') // -10% -> 9000

    expect(wrapper.find('[data-test="total-preview"]').text()).toContain('$9.000,00')
  })

  it('sends es_regalo=true and zeroes the preview when the gift switch is on', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo') // 5000
    await pickOption(wrapper.find('[data-test="variante-select"]'), 'Grande') // VV-1: sized product
    await wrapper.find('[data-test="es-regalo-toggle"] input').trigger('change')
    await nextTick()

    expect(wrapper.find('[data-test="total-preview"]').text()).toContain('$0,00') // gift -> $0

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0]).toEqual({
      canal_venta: 'web',
      descuento_porcentaje: 0,
      es_regalo: true,
      detalles: [{ producto_id: 1, variante_id: 5, cantidad: 1, precio_unitario: 5000 }],
    })
  })

  it('prefills every editable field from `initial` in edit mode', async () => {
    const wrapper = await mountEditForm()

    expect(wrapper.find('[data-test="cliente-select"]').text()).toContain('Juan Pérez')
    expect(wrapper.find('[data-test="canal-select"]').text()).toContain('WhatsApp')
    expect((wrapper.find('[data-test="descuento-input"] input').element as HTMLInputElement).value).toBe('5')
    expect((wrapper.find('[data-test="cantidad-input"] input').element as HTMLInputElement).value).toBe('2')
    expect((wrapper.find('[data-test="precio-input"] input').element as HTMLInputElement).value).toBe('5000')
    // The prefilled variant renders its label once variantes are loaded.
    expect(wrapper.find('[data-test="variante-select"]').text()).toContain('Grande')
    expect(loadVariantes).toHaveBeenCalledWith(1)
    expect(wrapper.find('[data-test="submit-venta"]').text()).toContain('Guardar cambios')
  })

  it('emits the same VentaCreate payload when submitting in edit mode', async () => {
    const wrapper = await mountEditForm()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0]).toEqual({
      cliente_id: 7,
      canal_venta: 'whatsapp',
      descuento_porcentaje: 5,
      es_regalo: false,
      detalles: [{ producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 }],
    })
  })

  it('prefills es_regalo=true and zeroes the preview in edit mode', async () => {
    const wrapper = await mountEditForm({ ...VENTA_EDIT, es_regalo: true, total_venta: '0.00' })

    expect(wrapper.find('[data-test="es-regalo-toggle"]').classes()).toContain('p-toggleswitch-checked')
    expect(wrapper.find('[data-test="total-preview"]').text()).toContain('$0,00')

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    const emitted = wrapper.emitted('submit')
    expect(emitted![0][0]).toEqual({
      cliente_id: 7,
      canal_venta: 'whatsapp',
      descuento_porcentaje: 5,
      es_regalo: true,
      detalles: [{ producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 }],
    })
  })

  it('VV-1: blocks a sized product without a variant and emits nothing', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(document.body.textContent).toContain('requieren seleccionar una variante')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('VV-1: emits with variante_id once a variant is chosen for the sized product', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo')
    await pickOption(wrapper.find('[data-test="variante-select"]'), 'Grande')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted<VentaCreate[]>('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0].detalles[0]).toMatchObject({
      producto_id: 1,
      variante_id: 5,
      cantidad: 1,
      precio_unitario: 5000,
    })
  })

  it('VV-2: a variant-less product submits without a variante', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Jugo de naranja')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted<VentaCreate[]>('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0].detalles[0]).toEqual({ producto_id: 2, cantidad: 1, precio_unitario: 8000 })
    expect(emitted![0][0].detalles[0]).not.toHaveProperty('variante_id')
  })

  it('VV-2: the variant select is disabled on an empty line', async () => {
    const wrapper = await mountForm()

    expect(wrapper.find('[data-test="variante-select"]').classes()).toContain('p-disabled')
  })

  it('VV-4: the select stays disabled when the loaded variant list is empty', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Jugo de naranja')
    expect(loadVariantes).toHaveBeenCalledWith(2)
    expect(wrapper.find('[data-test="variante-select"]').classes()).toContain('p-disabled')
  })

  it('VV-4: a sized product enables the select once its variants load', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo')
    expect(loadVariantes).toHaveBeenCalledWith(1)
    expect(wrapper.find('[data-test="variante-select"]').classes()).not.toContain('p-disabled')
  })

  it('VV-3: a combo sale submits one detail without a variante', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Caja Saca Las Garras')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const emitted = wrapper.emitted<VentaCreate[]>('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0].detalles).toHaveLength(1)
    expect(emitted![0][0].detalles[0]).toEqual({ producto_id: 3, cantidad: 1, precio_unitario: 12000 })
    expect(emitted![0][0].detalles[0]).not.toHaveProperty('variante_id')
  })

  it('VV-1: edit prefill with a sized product and null variant is blocked until a variant is chosen', async () => {
    const wrapper = await mountEditForm(VENTA_EDIT_SIN_VARIANTE)

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(document.body.textContent).toContain('requieren seleccionar una variante')
    expect(wrapper.emitted('submit')).toBeUndefined()

    await pickOption(wrapper.find('[data-test="variante-select"]'), 'Grande')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    const emitted = wrapper.emitted<VentaCreate[]>('submit')
    expect(emitted).toBeDefined()
    expect(emitted![0][0].detalles[0]).toMatchObject({ producto_id: 1, variante_id: 5 })
  })
})
