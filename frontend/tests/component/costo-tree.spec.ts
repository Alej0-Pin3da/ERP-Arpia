/**
 * CostoTree component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL CostoTree with Element Plus — the cost breakdown tree from
 * GET /productos/{id}/costo, pre-grouped by buildCostoTree:
 *  - renders each group section label (Insumos / Productos / Costos
 *    operativos fijos), its lines (nombre, cantidad es-CO, costo_unitario
 *    es-CO, costo_total es-CO), the group subtotal and the grand total
 *  - renders only the grupos present in the tree
 *  - renders the empty state when the tree has no groups
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { afterEach, describe, expect, it } from 'vitest'

import CostoTree from '@/components/productos/CostoTree.vue'
import type { CostoTree as CostoTreeType } from '@/utils/productos'

const TREE: CostoTreeType = {
  total: '15200.00',
  groups: [
    {
      tipo: 'insumo',
      label: 'Insumos',
      subtotal: 5250,
      lineas: [
        { tipo: 'insumo', id: 1, nombre: 'Harina de maíz', cantidad: '2.10', costo_unitario: '2500.00', costo_total: '5250.00' },
      ],
    },
    {
      tipo: 'producto',
      label: 'Productos',
      subtotal: 4950,
      lineas: [
        { tipo: 'producto', id: 2, nombre: 'Queso campesino', cantidad: '1.00', costo_unitario: '4950.00', costo_total: '4950.00' },
      ],
    },
    {
      tipo: 'operativos_fijos',
      label: 'Costos operativos fijos',
      subtotal: 5000,
      lineas: [
        { tipo: 'operativos_fijos', id: 1, nombre: 'Arepa de choclo', cantidad: '1.00', costo_unitario: '5000.00', costo_total: '5000.00' },
      ],
    },
  ],
}

async function mountTree(tree: CostoTreeType | null = TREE, loading = false): Promise<VueWrapper> {
  const wrapper = mount(CostoTree, {
    props: { tree, loading },
    global: { plugins: [ElementPlus] },
  })
  await flushPromises()
  return wrapper
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('CostoTree (MOD-5)', () => {
  it('renders every group section with its lines, subtotal and the grand total', async () => {
    const wrapper = await mountTree()

    const text = wrapper.text()
    // Group labels
    expect(text).toContain('Insumos')
    expect(text).toContain('Productos')
    expect(text).toContain('Costos operativos fijos')
    // Lines: nombre + cantidad + unit + total
    expect(text).toContain('Harina de maíz')
    expect(text).toContain('$2.500,00') // costo_unitario
    expect(text).toContain('$5.250,00') // costo_total insumo
    expect(text).toContain('Queso campesino')
    expect(text).toContain('$4.950,00') // costo_total producto
    // Group subtotals
    expect(text).toContain('$5.250,00')
    expect(text).toContain('$5.000,00') // subtotal operativos fijos
    // Grand total
    expect(text).toContain('Costo total de producción')
    expect(text).toContain('$15.200,00')
  })

  it('renders only the groups present in the tree', async () => {
    const wrapper = await mountTree({ total: '5000.00', groups: TREE.groups.slice(2) })

    const text = wrapper.text()
    expect(text).toContain('Costos operativos fijos')
    expect(text).not.toContain('Insumos')
    expect(text).not.toContain('Productos')
    expect(text).toContain('$5.000,00')
  })

  it('renders the empty state when the tree has no groups', async () => {
    const wrapper = await mountTree({ total: '0.00', groups: [] })
    expect(wrapper.text()).toContain('El producto no tiene costos desglosables')
  })

  it('shows skeleton placeholders while loading instead of the tree', async () => {
    const wrapper = await mountTree(TREE, true)

    expect(wrapper.find('.p-skeleton').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Costo total de producción')
  })
})
