/**
 * ComprasTable component tests (PR9, spec MOD-4).
 *
 * Mounts the REAL ComprasTable with Element Plus: renders the joined compra
 * rows (es-CO fecha, insumo name join, cantidad, precio_unitario and the
 * client-computed costo_total) and the empty state.
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

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
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

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
})
