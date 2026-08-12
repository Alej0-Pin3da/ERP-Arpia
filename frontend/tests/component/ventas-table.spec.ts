/**
 * Ventas list table component tests (task 2.1, spec MOD-1).
 *
 * Mounts the REAL VentasTable with pre-joined rows (buildVentaRows output):
 * es-CO formatted money/date, canal/estado labels, joined product names in
 * the summary column, and expandable detail lines with product/variant names.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

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
    global: { plugins: [ElementPlus] },
  })
  // el-table paints its body one tick after mount (ResizeObserver layout).
  await nextTick()
  return wrapper
}

describe('VentasTable (MOD-1 list)', () => {
  it('renders joined rows with es-CO formatting and labels', async () => {
    const wrapper = await mountTable([ROW])

    const text = wrapper.text()
    expect(wrapper.findAll('.el-table__row')[0].text()).toContain('10') // id cell
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
    // Expand the first row: el-table's expand icon toggles the detail area.
    const expandIcon = wrapper.find('.el-table__expand-icon')
    await expandIcon.trigger('click')
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

    const canalColumn = wrapper
      .findAllComponents({ name: 'ElTableColumn' })
      .find((c) => c.props('columnKey') === 'canal_venta')
    const estadoColumn = wrapper
      .findAllComponents({ name: 'ElTableColumn' })
      .find((c) => c.props('columnKey') === 'estado')

    expect(canalColumn!.props('filters')).toEqual([
      { text: 'Web', value: 'web' },
      { text: 'WhatsApp', value: 'whatsapp' },
      { text: 'Instagram', value: 'instagram' },
      { text: 'Feria', value: 'feria' },
    ])
    expect(estadoColumn!.props('filters')).toEqual([
      { text: 'Completada', value: 'completada' },
      { text: 'Anulada', value: 'anulada' },
    ])
  })

  it('normalizes an el-table filter-change into a typed single-value emit', async () => {
    const wrapper = await mountTable([ROW])

    wrapper.findComponent({ name: 'ElTable' }).vm.$emit('filter-change', {
      canal_venta: ['feria'],
      estado: ['anulada'],
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')).toBeDefined()
    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ canal_venta: 'feria', estado: 'anulada' })
  })

  it('emits nulls when a column filter is cleared (empty selection)', async () => {
    const wrapper = await mountTable([ROW])

    wrapper.findComponent({ name: 'ElTable' }).vm.$emit('filter-change', {
      canal_venta: [],
      estado: [],
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ canal_venta: null, estado: null })
  })

  it('maps an el-table sort-change into a typed {prop, order} emit', async () => {
    const wrapper = await mountTable([ROW])

    wrapper
      .findComponent({ name: 'ElTable' })
      .vm.$emit('sort-change', { column: { key: 'total_venta' }, order: 'ascending' })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'total_venta', order: 'asc' })
  })

  it('maps a cleared sort (null order) for the same column', async () => {
    const wrapper = await mountTable([ROW])

    wrapper
      .findComponent({ name: 'ElTable' })
      .vm.$emit('sort-change', { column: { key: 'cliente' }, order: null })
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
})
