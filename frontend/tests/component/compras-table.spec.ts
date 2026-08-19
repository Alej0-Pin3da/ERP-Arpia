/**
 * ComprasTable component tests (PR9, spec MOD-4).
 *
 * Mounts the REAL ComprasTable with PrimeVue only (slice 1c — the component is
 * fully migrated, no el-* cells left, so ElementPlus is dropped here):
 * renders the joined compra rows (es-CO fecha, insumo name join, cantidad,
 * precio_unitario and the client-computed costo_total) and the empty state.
 * The insumo header funnel is a DataTable filter menu hosting a Select
 * (`filterDisplay="menu"`); it only renders when lookups are passed, and the
 * filter/sort payloads are normalized by the parsePrimeVueFilters/
 * parsePrimeVueSort adapters.
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import ComprasTable from '@/components/inventario/ComprasTable.vue'
import type { CompraRow } from '@/utils/inventario'

const ROWS: CompraRow[] = [
  {
    id: 2,
    fecha: '2026-08-03T10:30:00Z',
    insumo: 'Harina de maíz',
    cantidad: '3.00',
    precio_unitario: '2500.00',
    costo_total: 7500,
  },
  {
    id: 1,
    fecha: '2026-08-01T09:00:00Z',
    insumo: 'Insumo #99',
    cantidad: '2.50',
    precio_unitario: '1200.00',
    costo_total: 3000,
  },
]

async function mountTable(rows: CompraRow[]): Promise<VueWrapper> {
  const wrapper = mount(ComprasTable, {
    props: { rows },
    global: {
      plugins: [[PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }]],
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

const INSUMOS = [
  { id: 1, nombre: 'Harina de maíz' },
  { id: 2, nombre: 'Aceite' },
]

describe('ComprasTable (MOD-4)', () => {
  it('renders the compra rows es-CO with joined insumo names and computed totals', async () => {
    const wrapper = await mountTable(ROWS)

    const text = wrapper.text()
    expect(text).toContain('Harina de maíz')
    expect(text).toContain('Insumo #99') // graceful join fallback
    expect(text).toContain('03/08/2026') // fecha_compra es-CO
    expect(text).toContain('3') // cantidad formatQty
    expect(text).toContain('$2.500,00') // precio_unitario
    expect(text).toContain('$7.500,00') // 3 x 2500 computed client-side
    expect(text).toContain('$1.200,00')
    expect(text).toContain('$3.000,00') // 2.5 x 1200
  })

  it('shows an empty state when there are no compras', async () => {
    const wrapper = await mountTable([])
    expect(wrapper.text()).toContain('Sin compras registradas')
  })

  it('declares the insumo header funnel from the props with labeled options', async () => {
    const wrapper = mount(ComprasTable, {
      props: { rows: ROWS, insumos: INSUMOS },
      global: {
        plugins: [[PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }]],
      },
    })
    await nextTick()

    // Config-level: one 'equals' constraint per column and the funnel renders.
    expect(wrapper.findComponent(DataTable).props('filters')).toEqual({
      insumo: { value: null, matchMode: 'equals' },
    })
    expect(wrapper.findAll('.p-datatable-column-filter-button')).toHaveLength(1)

    // Behavioral: opening the funnel mounts the Select with the insumo options.
    await wrapper.find('.p-datatable-column-filter-button').trigger('click')
    await flushOverlay()

    const insumoSelect = wrapper.findComponent(Select)
    expect(insumoSelect.exists()).toBe(true)
    expect(insumoSelect.props('options')).toEqual([
      { text: 'Harina de maíz', value: 1 },
      { text: 'Aceite', value: 2 },
    ])
  })

  it('renders no funnel when no lookups are passed (empty filters)', async () => {
    const wrapper = await mountTable(ROWS)

    expect(wrapper.findAll('.p-datatable-column-filter-button')).toHaveLength(0)
  })

  it('normalizes a PrimeVue filter payload on insumo into a typed emit', async () => {
    const wrapper = await mountTable(ROWS)

    wrapper.findComponent(DataTable).vm.$emit('filter', {
      filters: { insumo: { value: 1, matchMode: 'equals' } },
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')).toBeDefined()
    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ insumo_id: 1 })
  })

  it('emits null when the insumo column filter is cleared (null constraint)', async () => {
    const wrapper = await mountTable(ROWS)

    wrapper.findComponent(DataTable).vm.$emit('filter', {
      filters: { insumo: { value: null, matchMode: 'equals' } },
    })
    await nextTick()

    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ insumo_id: null })
  })

  it('maps a PrimeVue sort payload into a typed {prop, order} emit', async () => {
    const wrapper = await mountTable(ROWS)

    wrapper
      .findComponent(DataTable)
      .vm.$emit('sort', { sortField: 'precio_unitario_compra', sortOrder: -1 })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'precio_unitario_compra', order: 'desc' })
  })
})
