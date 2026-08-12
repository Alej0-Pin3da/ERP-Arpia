/**
 * Ventas register form component tests (task 2.2, spec MOD-1).
 *
 * Mounts the REAL VentasForm with real Element Plus and drives it through
 * real user interaction (el-select dropdowns, el-input-number fields):
 *  - empty detalles blocks submission with a warning and emits nothing
 *  - selecting a product auto-fills precio_unitario from
 *    precio_venta_sugerido and loads its variantes
 *  - a valid form emits the exact VentaCreate POST body
 *  - the client-side total preview mirrors the server total
 *    (subtotal * (1 - descuento/100))
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus, { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import VentasForm from '@/components/ventas/VentasForm.vue'
import type { components } from '@/types/api.d'

type ClienteRead = components['schemas']['ClienteRead']
type ProductoRead = components['schemas']['ProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']

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

const loadVariantes = vi.fn().mockResolvedValue(VARIANTES)

async function mountForm(saving = false): Promise<VueWrapper> {
  const wrapper = mount(VentasForm, {
    props: { productos: PRODUCTOS, clientes: CLIENTES, loadVariantes, saving },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

/** Open an el-select by its data-test and click the option with the label. */
async function pickOption(select: ReturnType<VueWrapper['find']>, label: string): Promise<void> {
  await select.trigger('click')
  await nextTick()
  const item = [...document.querySelectorAll<HTMLElement>('.el-select-dropdown__item')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!item) throw new Error(`dropdown option not found: "${label}"`)
  item.click()
  await flushPromises()
  await nextTick()
}

afterEach(() => {
  ElMessage.closeAll()
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
    await wrapper.find('[data-test="cantidad-input"] input').setValue('2')
    await wrapper.find('[data-test="descuento-input"] input').setValue('5')

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
    await wrapper.find('[data-test="cantidad-input"] input').setValue('2') // subtotal 10000
    await wrapper.find('[data-test="descuento-input"] input').setValue('10') // -10% -> 9000

    expect(wrapper.find('[data-test="total-preview"]').text()).toContain('$9.000,00')
  })

  it('sends es_regalo=true and zeroes the preview when the gift switch is on', async () => {
    const wrapper = await mountForm()

    await pickOption(wrapper.find('[data-test="producto-select"]'), 'Arepa de huevo') // 5000
    await wrapper.find('[data-test="es-regalo-toggle"]').trigger('click')
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
      detalles: [{ producto_id: 1, cantidad: 1, precio_unitario: 5000 }],
    })
  })
})
