/**
 * VariantesTable component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL VariantesTable with Element Plus + PrimeVue (slice 1c) —
 * the nested variantes list for ONE selected product:
 *  - renders nombre_variante and precio_venta es-CO, with '—' for a null
 *    precio (the backend VarianteProductoRead has NO costo_adicional — only
 *    nombre_variante + precio_venta)
 *  - Editar / Eliminar emit `edit` / `delete` with the row; hidden when
 *    canEdit=false
 *  - the empty state renders
 * el-button cells migrated to PrimeVue in slice 2b.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import DataTable from 'primevue/datatable'
import PrimeVue from 'primevue/config'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import VariantesTable from '@/components/productos/VariantesTable.vue'
import type { components } from '@/types/api.d'

type VarianteProductoRead = components['schemas']['VarianteProductoRead']

const VARIANTES: VarianteProductoRead[] = [
  { id: 1, producto_id: 1, nombre_variante: 'Individual', precio_venta: '13000.00' },
  { id: 2, producto_id: 1, nombre_variante: 'Docena', precio_venta: null },
]

async function mountTable(canEdit = true, variantes = VARIANTES): Promise<VueWrapper> {
  const wrapper = mount(VariantesTable, {
    props: { variantes, loading: false, canEdit },
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

describe('VariantesTable (MOD-5)', () => {
  it('renders the variante name and precio_venta es-CO with a dash for null', async () => {
    const wrapper = await mountTable()

    const text = wrapper.text()
    expect(text).toContain('Individual')
    expect(text).toContain('$13.000,00')
    expect(text).toContain('Docena')
    expect(text).toContain('—') // null precio_venta
  })

  it('renders one DataTable row per variante', async () => {
    const wrapper = await mountTable()

    expect(wrapper.findComponent(DataTable).exists()).toBe(true)
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(2)
  })

  it('emits edit and delete with the row when the actions are visible', async () => {
    const wrapper = await mountTable()

    await wrapper.findAll('[data-test="edit-variante"]')[0].trigger('click')
    expect(wrapper.emitted('edit')![0][0]).toMatchObject({ id: 1, nombre_variante: 'Individual' })

    await wrapper.findAll('[data-test="delete-variante"]')[1].trigger('click')
    expect(wrapper.emitted('delete')![0][0]).toMatchObject({ id: 2, nombre_variante: 'Docena' })
  })

  it('hides the edit/delete actions when canEdit is false', async () => {
    const wrapper = await mountTable(false)

    expect(wrapper.findAll('[data-test="edit-variante"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-variante"]')).toHaveLength(0)
  })

  it('renders the empty state when the product has no variantes', async () => {
    const wrapper = await mountTable(true, [])
    expect(wrapper.text()).toContain('Sin variantes registradas')
  })
})
