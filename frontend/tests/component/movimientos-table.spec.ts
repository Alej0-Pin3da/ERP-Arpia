/**
 * MovimientosTable component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL MovimientosTable with Element Plus: renders the joined
 * rows es-CO (fecha, tipo tag, descripcion, socio name/'—', monto, settlement
 * id), hides the delete action for read-only roles (can-delete=false), emits
 * `delete` with the row, and shows the empty state.
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

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

async function mountTable(rows: MovimientoRow[], canDelete = true): Promise<VueWrapper> {
  const wrapper = mount(MovimientosTable, {
    props: { rows, canDelete },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
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

  it('hides the delete action for read-only roles', async () => {
    const wrapper = await mountTable(ROWS, false)

    expect(wrapper.findAll('[data-test="delete-movimiento"]')).toHaveLength(0)
  })

  it('shows an empty state when there are no movimientos', async () => {
    const wrapper = await mountTable([])

    expect(wrapper.text()).toContain('Sin movimientos registrados')
  })
})
