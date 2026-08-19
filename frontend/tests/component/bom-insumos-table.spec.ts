/**
 * BomInsumosTable component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL BomInsumosTable with Element Plus + PrimeVue (slice 1c) —
 * the BOM insumo lines for the selected product:
 *  - renders the joined insumo name, unidad_medida, cantidad_requerida es-CO
 *    and porcentaje_desperdicio as a % (5% / 0%)
 *  - Editar / Eliminar emit `edit` / `delete` with the row; hidden when
 *    canEdit=false (operador/consulta)
 *  - the empty state renders
 * el-button cells still need the ElementPlus plugin until slice 2b.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import DataTable from 'primevue/datatable'
import PrimeVue from 'primevue/config'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import BomInsumosTable from '@/components/productos/BomInsumosTable.vue'
import type { BomInsumoRow } from '@/utils/productos'

const ROWS: BomInsumoRow[] = [
  {
    id: 1,
    insumo: 'Harina de maíz',
    unidad_medida: 'kg',
    cantidad_requerida: '2.00',
    porcentaje_desperdicio: '5.00',
  },
  {
    id: 2,
    insumo: 'Insumo #99', // insumo gone -> mapper fallback
    unidad_medida: '—',
    cantidad_requerida: '1.50',
    porcentaje_desperdicio: '0.00',
  },
]

async function mountTable(canEdit = true, rows: BomInsumoRow[] = ROWS): Promise<VueWrapper> {
  const wrapper = mount(BomInsumosTable, {
    props: { rows, loading: false, canEdit },
    global: {
      plugins: [
        ElementPlus,
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

describe('BomInsumosTable (MOD-5)', () => {
  it('renders the joined insumo name, unidad, cantidad es-CO and desperdicio %', async () => {
    const wrapper = await mountTable()

    const text = wrapper.text()
    expect(text).toContain('Harina de maíz')
    expect(text).toContain('kg')
    expect(text).toContain('2') // cantidad_requerida
    expect(text).toContain('5 %') // porcentaje_desperdicio
    expect(text).toContain('Insumo #99') // fallback label
  })

  it('renders one DataTable row per BOM line', async () => {
    const wrapper = await mountTable()

    expect(wrapper.findComponent(DataTable).exists()).toBe(true)
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(2)
  })

  it('emits edit and delete with the row when the actions are visible', async () => {
    const wrapper = await mountTable()

    await wrapper.findAll('[data-test="edit-bom-insumo"]')[0].trigger('click')
    expect(wrapper.emitted('edit')![0][0]).toMatchObject({ id: 1, insumo: 'Harina de maíz' })

    await wrapper.findAll('[data-test="delete-bom-insumo"]')[1].trigger('click')
    expect(wrapper.emitted('delete')![0][0]).toMatchObject({ id: 2 })
  })

  it('hides the edit/delete actions when canEdit is false', async () => {
    const wrapper = await mountTable(false)

    expect(wrapper.findAll('[data-test="edit-bom-insumo"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-bom-insumo"]')).toHaveLength(0)
  })

  it('renders the empty state when there are no BOM insumo lines', async () => {
    const wrapper = await mountTable(true, [])
    expect(wrapper.text()).toContain('Sin insumos en la receta')
  })
})
