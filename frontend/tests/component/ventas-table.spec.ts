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

async function mountTable(rows: VentaRow[], loading = false): Promise<VueWrapper> {
  const wrapper = mount(VentasTable, {
    props: { rows, loading },
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
})
