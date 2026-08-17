/**
 * MovimientosTable component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL MovimientosTable with Element Plus + PrimeVue (slice 1b):
 * renders the joined rows es-CO (fecha, tipo tag, descripcion, socio name/'—',
 * monto, settlement id), hides the delete action for read-only roles
 * (can-delete=false), emits `delete` with the row, and shows the empty state.
 * The tipo header funnel is a DataTable filter menu hosting a Select
 * (`filterDisplay="menu"`), and the filter/sort payloads are normalized by
 * the parsePrimeVueFilters/parsePrimeVueSort adapters. el-tag/el-button cells
 * el-button cells migrated to PrimeVue in slice 2b.
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import MovimientosTable from '@/components/finanzas/MovimientosTable.vue'
import type { MovimientoRow } from '@/utils/finanzas'

const ROWS: MovimientoRow[] = [
  {
    id: 3,
    fecha: '2026-08-03T15:00:00Z',
    tipo: 'Retiro',
    descripcion: 'Liquidación abc',
    socio: 'Ana María',
    monto: '30000.00',
    liquidacion_id: 'abc00',
  },
  {
    id: 2,
    fecha: '2026-08-02T12:00:00Z',
    tipo: 'Inversion',
    descripcion: 'Horno nuevo',
    socio: '—',
    monto: '1000000.00',
    liquidacion_id: null,
  },
  {
    id: 1,
    fecha: '2026-08-01T10:00:00Z',
    tipo: 'Gasto',
    descripcion: 'Compra de arepas',
    socio: '—',
    monto: '50000.00',
    liquidacion_id: null,
  },
]

async function mountTable(rows: MovimientoRow[], canDelete = true, canEdit = false): Promise<VueWrapper> {
  const wrapper = mount(MovimientosTable, {
    props: { rows, canDelete, canEdit },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  return wrapper
}

/** Let the funnel overlay open (Teleport + transition) before interacting. */
async function flushOverlay(): Promise<void> {
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  await nextTick()
}

describe('MovimientosTable (MOD-3)', () => {
  it('renders the joined rows es-CO with tipo tags and socio fallbacks', async () => {
    const wrapper = await mountTable(ROWS)

    const text = wrapper.text()
    expect(text).toContain('Retiro')
    expect(text).toContain('Inversión')
    expect(text).toContain('Gasto')
    expect(text).toContain('Liquidación abc')
    expect(text).toContain('Horno nuevo')
    expect(text).toContain('Compra de arepas')
    expect(text).toContain('Ana María')
    expect(text).toContain('$30.000,00')
    expect(text).toContain('$1.000.000,00')
    expect(text).toContain('$50.000,00')

    // The settlement key surfaces for liquidacion-born rows.
    expect(text).toContain('abc00')
  })

  it('emits `delete` with the row when the delete action is clicked', async () => {
    const wrapper = await mountTable(ROWS)

    const buttons = wrapper.findAll('[data-test="delete-movimiento"]')
    expect(buttons).toHaveLength(3)
    await buttons[0].trigger('click')

    expect(wrapper.emitted('delete')).toBeDefined()
    expect(wrapper.emitted('delete')![0][0]).toEqual(ROWS[0])
  })

  it('emits `edit` with the row when the edit action is clicked (T9)', async () => {
    const wrapper = await mountTable(ROWS, true, true)

    const buttons = wrapper.findAll('[data-test="edit-movimiento"]')
    expect(buttons).toHaveLength(3)
    await buttons[0].trigger('click')

    expect(wrapper.emitted('edit')).toBeDefined()
    expect(wrapper.emitted('edit')![0][0]).toEqual(ROWS[0])
  })

  it('hides the edit action when can-edit is false (read-only roles)', async () => {
    const wrapper = await mountTable(ROWS, true, false)

    expect(wrapper.findAll('[data-test="edit-movimiento"]')).toHaveLength(0)
  })

  it('hides the delete action for read-only roles', async () => {
    const wrapper = await mountTable(ROWS, false)

    expect(wrapper.findAll('[data-test="delete-movimiento"]')).toHaveLength(0)
  })

  it('shows an empty state when there are no movimientos', async () => {
    const wrapper = await mountTable([])

    expect(wrapper.text()).toContain('Sin movimientos registrados')
  })

  it('declares the tipo header funnel with labeled options', async () => {
    const wrapper = await mountTable(ROWS)

    // Config-level: one 'equals' constraint per column and the funnel renders.
    expect(wrapper.findComponent(DataTable).props('filters')).toEqual({
      tipo: { value: null, matchMode: 'equals' },
    })
    expect(wrapper.findAll('.p-datatable-column-filter-button')).toHaveLength(1)

    // Behavioral: opening the funnel mounts the Select with the tipo options.
    await wrapper.find('.p-datatable-column-filter-button').trigger('click')
    await flushOverlay()

    const tipoSelect = wrapper.findComponent(Select)
    expect(tipoSelect.exists()).toBe(true)
    expect(tipoSelect.props('options')).toEqual([
      { text: 'Gasto', value: 'Gasto' },
      { text: 'Inversión', value: 'Inversion' },
      { text: 'Retiro', value: 'Retiro' },
    ])
  })

  it('normalizes a PrimeVue filter payload on tipo into a typed emit', async () => {
    const wrapper = await mountTable(ROWS)

    wrapper.findComponent(DataTable).vm.$emit('filter', {
      filters: { tipo: { value: 'Gasto', matchMode: 'equals' } },
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')).toBeDefined()
    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ tipo: 'Gasto' })
  })

  it('emits null when the tipo column filter is cleared (null constraint)', async () => {
    const wrapper = await mountTable(ROWS)

    wrapper.findComponent(DataTable).vm.$emit('filter', {
      filters: { tipo: { value: null, matchMode: 'equals' } },
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ tipo: null })
  })

  it('maps a PrimeVue sort payload into a typed {prop, order} emit', async () => {
    const wrapper = await mountTable(ROWS)

    wrapper.findComponent(DataTable).vm.$emit('sort', { sortField: 'monto', sortOrder: -1 })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'monto', order: 'desc' })
  })

  it('maps a cleared sort (order 0) for a prop column', async () => {
    const wrapper = await mountTable(ROWS)

    wrapper.findComponent(DataTable).vm.$emit('sort', { sortField: 'socio', sortOrder: 0 })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'socio', order: null })
  })
})
