/**
 * Ventas list table component tests (task 2.1, spec MOD-1).
 *
 * Mounts the REAL VentasTable with pre-joined rows (buildVentaRows output):
 * es-CO formatted money/date, canal/estado labels, joined product names in
 * the summary column, and expandable detail lines with product/variant names.
 *
 * Migrated to PrimeVue DataTable (slice 1a): rows are `tbody tr` (DataTable
 * paints `p-row-even`/`p-row-odd` body rows — there is no `.p-datatable-row`
 * class), expansion uses `.p-datatable-row-toggle-button`, and the header
 * funnels are DataTable filter menus (`filterDisplay="menu"`) hosting a
 * Select per column. Element Plus was fully dropped in slice 5 (MIG-2); the
 * v-tooltip gift action needs the PrimeVue Tooltip directive.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import PrimeVue from 'primevue/config'
import Tooltip from 'primevue/tooltip'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import VentasTable from '@/components/ventas/VentasTable.vue'
import type { VentaRow } from '@/utils/ventas'

const ROW: VentaRow = {
  id: 10,
  fecha: '2026-08-01T10:30:00Z',
  canal_venta: 'whatsapp',
  estado: 'completada',
  es_regalo: false,
  total_venta: '15000.00',
  cliente: 'Juan Pérez',
  detalle_count: 2,
  detalles: [
    {
      producto_id: 1,
      variante_id: 5,
      nombre: 'Arepa de huevo',
      variante: 'Grande',
      cantidad: '2',
      precio_unitario_aplicado: '5000.00',
    },
    {
      producto_id: 2,
      variante_id: null,
      nombre: 'Jugo de naranja',
      variante: '(base)',
      cantidad: '1',
      precio_unitario_aplicado: '5000.00',
    },
  ],
}

const ROW_ANULADA: VentaRow = {
  ...ROW,
  id: 9,
  estado: 'anulada',
  cliente: '—',
  detalle_count: 1,
  detalles: [
    {
      producto_id: 99,
      variante_id: 77,
      nombre: 'Producto #99',
      variante: 'Variante #77',
      cantidad: '1',
      precio_unitario_aplicado: '8000.00',
    },
  ],
}

const ROW_REGALO: VentaRow = {
  ...ROW,
  id: 8,
  estado: 'completada',
  es_regalo: true,
  total_venta: '10000.00', // historical reference price (never reported)
  cliente: '—',
  detalle_count: 1,
  detalles: [
    {
      producto_id: 1,
      variante_id: null,
      nombre: 'Arepa de huevo',
      variante: '(base)',
      cantidad: '1',
      precio_unitario_aplicado: '10000.00',
    },
  ],
}

async function mountTable(rows: VentaRow[], loading = false, canMarkRegalo = false): Promise<VueWrapper> {
  const wrapper = mount(VentasTable, {
    props: { rows, loading, canMarkRegalo },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
      directives: { tooltip: Tooltip },
    },
  })
  // DataTable paints its body one tick after mount.
  await nextTick()
  return wrapper
}

/** Let the funnel overlay open (Teleport + transition) before interacting. */
async function flushOverlay(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await flushPromises()
}

describe('VentasTable (MOD-1 list)', () => {
  it('renders joined rows with es-CO formatting and labels', async () => {
    const wrapper = await mountTable([ROW])

    const text = wrapper.text()
    expect(wrapper.findAll('tbody tr')[0].text()).toContain('10') // id cell
    expect(text).toContain('01/08/2026')
    expect(text).toContain('WhatsApp')
    expect(text).toContain('Completada')
    expect(text).toContain('$15.000,00')
    expect(text).toContain('Juan Pérez')
    expect(text).toContain('Arepa de huevo ×2')
    expect(text).toContain('Jugo de naranja ×1')
  })

  it('shows an anulada estado with its label and degrades missing joins', async () => {
    const wrapper = await mountTable([ROW_ANULADA])

    const text = wrapper.text()
    expect(text).toContain('Anulada')
    expect(text).toContain('Producto #99 ×1')
    expect(text).toContain('—') // cliente fallback
  })

  it('expands a row into detail lines with product/variant names and money', async () => {
    const wrapper = await mountTable([ROW])
    // Expand the first row: DataTable's expander toggler opens the detail row.
    await wrapper.find('.p-datatable-row-toggle-button').trigger('click')
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Arepa de huevo')
    expect(text).toContain('Grande')
    expect(text).toContain('Jugo de naranja')
    expect(text).toContain('(base)')
    expect(text).toContain('$5.000,00') // precio unitario aplicado
  })

  it('renders an empty state when there are no ventas', async () => {
    const wrapper = await mountTable([])

    expect(wrapper.text()).toContain('Sin ventas registradas')
  })

  it('declares header funnel filters on the canal/estado columns with labeled options', async () => {
    const wrapper = await mountTable([ROW])

    // Config-level: the lazy filter state declares one constraint per column
    // and funnels render for canal/estado (equals) + fecha (between, DatePicker rango) + nombre/cliente/total_venta (contains) (filterDisplay="menu").
    expect(wrapper.findComponent(DataTable).props('filters')).toEqual({
      canal_venta: { value: null, matchMode: 'equals' },
      estado: { value: null, matchMode: 'equals' },
      fecha: { value: null, matchMode: 'between' },
      nombre: { value: null, matchMode: 'contains' },
      cliente: { value: null, matchMode: 'contains' },
      total_venta: { value: null, matchMode: 'contains' },
    })
    // fecha filter is now a DatePicker rango (array or null), not InputText
    const fechaFilter = wrapper.findComponent(DataTable).props('filters').fecha
    expect(fechaFilter.value === null || Array.isArray(fechaFilter.value)).toBe(true)
    expect(wrapper.findAll('.p-datatable-column-filter-button')).toHaveLength(6)

    // Behavioral: opening the canal funnel mounts the Select with labeled options.
    // Fecha is the first filterable column (InputText), canal is second.
    await wrapper.findAll('.p-datatable-column-filter-button')[1].trigger('click')
    await flushOverlay()

    const canalSelect = wrapper.findComponent(Select)
    expect(canalSelect.exists()).toBe(true)
    expect(canalSelect.props('options')).toEqual([
      { text: 'Web', value: 'web' },
      { text: 'WhatsApp', value: 'whatsapp' },
      { text: 'Instagram', value: 'instagram' },
      { text: 'Feria', value: 'feria' },
    ])
  })

  it('normalizes a PrimeVue filter payload into a typed single-value emit', async () => {
    const wrapper = await mountTable([ROW])

    wrapper.findComponent(DataTable).vm.$emit('filter', {
      filters: {
        canal_venta: { value: 'feria', matchMode: 'equals' },
        estado: { value: 'anulada', matchMode: 'equals' },
      },
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')).toBeDefined()
    expect(wrapper.emitted('filter-change')![0][0]).toEqual({
      canal_venta: 'feria',
      estado: 'anulada',
      cliente: null,
      producto: null,
      fecha_desde: null,
      fecha_hasta: null,
      total_venta: null,
    })
  })

  it('emits nulls when a column filter is cleared (null constraint)', async () => {
    const wrapper = await mountTable([ROW])

    wrapper.findComponent(DataTable).vm.$emit('filter', {
      filters: {
        canal_venta: { value: null, matchMode: 'equals' },
        estado: { value: null, matchMode: 'equals' },
      },
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')![0][0]).toEqual({
      canal_venta: null,
      estado: null,
      cliente: null,
      producto: null,
      fecha_desde: null,
      fecha_hasta: null,
      total_venta: null,
    })
  })

  it('emits fecha_desde/hasta as ISO dates when the fecha range is set', async () => {
    const wrapper = await mountTable([ROW])

    const d1 = new Date('2026-08-01T00:00:00.000Z')
    const d2 = new Date('2026-08-10T00:00:00.000Z')
    wrapper.findComponent(DataTable).vm.$emit('filter', {
      filters: {
        fecha: { value: [d1, d2], matchMode: 'between' },
      },
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')![0][0]).toEqual({
      canal_venta: null,
      estado: null,
      cliente: null,
      producto: null,
      fecha_desde: '2026-08-01',
      fecha_hasta: '2026-08-10',
      total_venta: null,
    })
  })

  it('maps a PrimeVue sort payload into a typed {prop, order} emit', async () => {
    const wrapper = await mountTable([ROW])

    wrapper.findComponent(DataTable).vm.$emit('sort', { sortField: 'total_venta', sortOrder: 1 })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'total_venta', order: 'asc' })
  })

  it('maps a cleared sort (order 0) for the same column', async () => {
    const wrapper = await mountTable([ROW])

    wrapper.findComponent(DataTable).vm.$emit('sort', { sortField: 'cliente', sortOrder: 0 })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'cliente', order: null })
  })

  it('renders a gift row with a Regalo tag and a $0 total (es_regalo)', async () => {
    const wrapper = await mountTable([ROW_REGALO])

    const text = wrapper.text()
    expect(wrapper.find('[data-test="tag-regalo"]').exists()).toBe(true)
    expect(text).toContain('Regalo')
    expect(text).toContain('$0,00') // gift total is always $0 in the list
    expect(text).not.toContain('$10.000,00') // reference price never shown as total
  })

  it('hides the marcar-regalo action for gift rows and hides it without canMarkRegalo', async () => {
    // No prop -> no actions column at all.
    const wrapperNoProp = await mountTable([ROW])
    expect(wrapperNoProp.find('[data-test="marcar-regalo"]').exists()).toBe(false)

    // canMarkRegalo -> button only for non-gift rows.
    const wrapper = await mountTable([ROW, ROW_REGALO], false, true)
    const buttons = wrapper.findAll('[data-test="marcar-regalo"]')
    expect(buttons).toHaveLength(1) // ROW has it, ROW_REGALO does not
  })

  it('emits marcar-regalo with the venta id when the action is clicked', async () => {
    const wrapper = await mountTable([ROW], false, true)

    await wrapper.find('[data-test="marcar-regalo"]').trigger('click')
    await nextTick()

    expect(wrapper.emitted('marcar-regalo')).toBeDefined()
    expect(wrapper.emitted('marcar-regalo')![0][0]).toBe(10)
  })

  it('shows Editar for every non-anulada row and Anular only for normal rows', async () => {
    // ROW (normal) -> Editar + Anular; ROW_REGALO -> Editar (regalos are
    // editable) but NO Anular; ROW_ANULADA -> neither.
    const wrapper = await mountTable([ROW, ROW_REGALO, ROW_ANULADA], false, true)

    const editButtons = wrapper.findAll('[data-test="editar-venta"]')
    const anularButtons = wrapper.findAll('[data-test="anular-venta"]')
    expect(editButtons).toHaveLength(2)
    expect(anularButtons).toHaveLength(1)
  })

  it('hides the whole actions column without canMarkRegalo', async () => {
    const wrapper = await mountTable([ROW])

    expect(wrapper.find('[data-test="editar-venta"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="anular-venta"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="marcar-regalo"]').exists()).toBe(false)
  })

  it('emits editar with the row and anular with the venta id', async () => {
    const wrapper = await mountTable([ROW], false, true)

    await wrapper.find('[data-test="editar-venta"]').trigger('click')
    await nextTick()
    expect(wrapper.emitted('editar')).toBeDefined()
    expect(wrapper.emitted('editar')![0][0]).toEqual(ROW)

    await wrapper.find('[data-test="anular-venta"]').trigger('click')
    await nextTick()
    expect(wrapper.emitted('anular')).toBeDefined()
    expect(wrapper.emitted('anular')![0][0]).toBe(10)
  })
})