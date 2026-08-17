/**
 * BomProductosTable component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL BomProductosTable with Element Plus + PrimeVue (slice 1c) —
 * the combo contents (BomProducto lines) for the selected product:
 *  - renders the joined included product name and cantidad es-CO
 *  - Editar / Eliminar emit `edit` / `delete` with the row; hidden when
 *    canEdit=false
 *  - the empty state renders
 * NOTE: the backend BomProducto schema has NO desperdicio field — only
 * producto_incluido_id + cantidad (verified backend schemas/bom.py).
 * el-button cells migrated to PrimeVue in slice 2b.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import DataTable from 'primevue/datatable'
import PrimeVue from 'primevue/config'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import BomProductosTable from '@/components/productos/BomProductosTable.vue'
import type { BomProductoRow } from '@/utils/productos'

const ROWS: BomProductoRow[] = [
  { id: 1, producto: 'Queso campesino', cantidad: '2.00' },
  { id: 2, producto: 'Producto #88', cantidad: '3.00' }, // producto gone
]

async function mountTable(canEdit = true, rows: BomProductoRow[] = ROWS): Promise<VueWrapper> {
  const wrapper = mount(BomProductosTable, {
    props: { rows, loading: false, canEdit },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await flushPromises()
  return wrapper
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('BomProductosTable (MOD-5)', () => {
  it('renders the joined product name and cantidad es-CO', async () => {
    const wrapper = await mountTable()

    const text = wrapper.text()
    expect(text).toContain('Queso campesino')
    expect(text).toContain('2') // cantidad
    expect(text).toContain('Producto #88') // fallback label
  })

  it('renders one DataTable row per combo line', async () => {
    const wrapper = await mountTable()

    expect(wrapper.findComponent(DataTable).exists()).toBe(true)
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(2)
  })

  it('emits edit and delete with the row when the actions are visible', async () => {
    const wrapper = await mountTable()

    await wrapper.findAll('[data-test="edit-bom-producto"]')[0].trigger('click')
    expect(wrapper.emitted('edit')![0][0]).toMatchObject({ id: 1, producto: 'Queso campesino' })

    await wrapper.findAll('[data-test="delete-bom-producto"]')[1].trigger('click')
    expect(wrapper.emitted('delete')![0][0]).toMatchObject({ id: 2 })
  })

  it('hides the edit/delete actions when canEdit is false', async () => {
    const wrapper = await mountTable(false)

    expect(wrapper.findAll('[data-test="edit-bom-producto"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-bom-producto"]')).toHaveLength(0)
  })

  it('renders the empty state when the combo has no contents', async () => {
    const wrapper = await mountTable(true, [])
    expect(wrapper.text()).toContain('Sin productos en el combo')
  })
})
