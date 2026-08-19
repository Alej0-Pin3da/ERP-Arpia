/**
 * Devoluciones list table component tests (task 2.3, spec MOD-2).
 *
 * Mounts the REAL DevolucionesTable with pre-joined rows (buildDevolucionRows
 * output): es-CO formatted fecha/monto, tipo labels + tags, motivo fallback
 * '—', items count, and expandable detail lines with joined product names.
 *
 * Migrated to PrimeVue DataTable (slice 1b): rows are `tbody tr` (DataTable
 * paints `p-row-even`/`p-row-odd` body rows), expansion uses the expander
 * column's `.p-datatable-row-toggle-button` opening the `#expansion` nested
 * DataTable (BEH-6). Element Plus was fully dropped in slice 5 (MIG-2).
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import DevolucionesTable from '@/components/devoluciones/DevolucionesTable.vue'
import type { DevolucionRow } from '@/utils/devoluciones'

const ROW: DevolucionRow = {
  id: 3,
  venta_id: 10,
  fecha: '2026-08-02T14:00:00Z',
  tipo: 'parcial',
  motivo: 'Cliente devolvió dos arepas',
  monto_reembolsado: '10000.00',
  items: [
    { producto_id: 1, variante_id: null, nombre: 'Arepa de huevo', cantidad: '2', subtotal: '10000.00' },
  ],
}

const ROW_TOTAL: DevolucionRow = {
  id: 2,
  venta_id: 9,
  fecha: '2026-08-01T09:00:00Z',
  tipo: 'total',
  motivo: '—',
  monto_reembolsado: '15000.00',
  items: [
    { producto_id: 99, variante_id: null, nombre: 'Producto #99', cantidad: '1', subtotal: '8000.00' },
  ],
}

async function mountTable(rows: DevolucionRow[], loading = false): Promise<VueWrapper> {
  const wrapper = mount(DevolucionesTable, {
    props: { rows, loading },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  // DataTable paints its body one tick after mount.
  await nextTick()
  return wrapper
}

describe('DevolucionesTable (MOD-2 list)', () => {
  it('renders rows with es-CO formatting, tipo tag and motivo', async () => {
    const wrapper = await mountTable([ROW])

    const rowText = wrapper.findAll('tbody tr')[0].text()
    expect(rowText).toContain('3') // id cell
    expect(rowText).toContain('02/08/2026')
    expect(rowText).toContain('10') // venta_id cell
    expect(rowText).toContain('Parcial')
    expect(rowText).toContain('Cliente devolvió dos arepas')
    expect(rowText).toContain('$10.000,00') // monto reembolsado
    expect(rowText).toContain('1') // items count
  })

  it('shows a total tipo with its label and degrades missing joins', async () => {
    const wrapper = await mountTable([ROW_TOTAL])

    const text = wrapper.text()
    expect(text).toContain('Total')
    expect(text).toContain('—') // null motivo fallback

    // The joined product label (fallback for a missing product) renders in
    // the expandable item area.
    await wrapper.find('.p-datatable-row-toggle-button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Producto #99')
  })

  it('expands a row into item lines with product name, qty and subtotal', async () => {
    const wrapper = await mountTable([ROW])
    await wrapper.find('.p-datatable-row-toggle-button').trigger('click')
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Arepa de huevo')
    expect(text).toContain('2') // cantidad formatQty
    expect(text).toContain('$10.000,00') // item subtotal
  })

  it('renders an empty state when there are no devoluciones', async () => {
    const wrapper = await mountTable([])

    expect(wrapper.text()).toContain('Sin devoluciones registradas')
  })
})
