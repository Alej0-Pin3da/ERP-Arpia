/**
 * InsumosTable component tests (PR9, spec MOD-4).
 *
 * Mounts the REAL InsumosTable with Element Plus: renders the insumo master
 * rows (nombre, server-joined nombre_categoria with '—' fallback, unidad,
 * es-CO stock and cost), highlights rows below their minimum with a severity
 * tag (Crítico/Bajo — reusing the dashboard stockSeverity), hides the
 * Editar/Eliminar actions for non-admin roles (can-edit=false), emits
 * `edit`/`delete` with the row, and shows the empty state.
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import InsumosTable from '@/components/inventario/InsumosTable.vue'
import type { components } from '@/types/api.d'

type InsumoRead = components['schemas']['InsumoRead']

const INSUMOS: InsumoRead[] = [
  {
    id: 1,
    categoria_id: 1,
    nombre: 'Harina de maíz',
    unidad_medida: 'kg',
    stock_actual: '12.00',
    stock_minimo: '5.00',
    costo_promedio_actual: '2500.00',
    nombre_categoria: 'Granos',
  },
  {
    id: 2,
    categoria_id: 2,
    nombre: 'Aceite',
    unidad_medida: 'L',
    stock_actual: '8.00',
    stock_minimo: '3.00',
    costo_promedio_actual: '9800.00',
    nombre_categoria: null, // server join missing -> em dash
  },
  {
    id: 3,
    categoria_id: 1,
    nombre: 'Sal',
    unidad_medida: 'kg',
    stock_actual: '2.00', // below half the minimum -> Crítico
    stock_minimo: '10.00',
    costo_promedio_actual: '800.00',
    nombre_categoria: 'Granos',
  },
]

async function mountTable(rows: InsumoRead[], canEdit = true): Promise<VueWrapper> {
  const wrapper = mount(InsumosTable, {
    props: { rows, canEdit },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  return wrapper
}

const CATEGORIAS = [
  { id: 1, nombre: 'Granos' },
  { id: 2, nombre: 'Abarrotes' },
]

describe('InsumosTable (MOD-4)', () => {
  it('renders the master rows with the server join and es-CO quantities and costs', async () => {
    const wrapper = await mountTable(INSUMOS)

    const text = wrapper.text()
    expect(text).toContain('Harina de maíz')
    expect(text).toContain('Granos') // nombre_categoria rendered as-is
    expect(text).toContain('Aceite')
    expect(text).toContain('L') // unidad_medida
    expect(text).toContain('12') // stock actual es-CO qty
    expect(text).toContain('$2.500,00') // costo_promedio_actual es-CO money
    expect(text).toContain('$9.800,00')
  })

  it('falls back to an em dash when the server join has no category name', async () => {
    const wrapper = await mountTable(INSUMOS)
    expect(wrapper.text()).toContain('—')
  })

  it('highlights rows below the minimum with a severity tag', async () => {
    const wrapper = await mountTable(INSUMOS)

    // id 3: stock 2 < 50% of min 10 -> Crítico; id 1: 12 >= 5 -> no tag.
    expect(wrapper.text()).toContain('Crítico')
  })

  it('renders no severity tag when every row is at or above its minimum', async () => {
    const wrapper = await mountTable([INSUMOS[0], INSUMOS[1]])
    expect(wrapper.text()).not.toContain('Crítico')
    expect(wrapper.text()).not.toContain('Bajo')
  })

  it('emits edit and delete with the row for admins', async () => {
    const wrapper = await mountTable(INSUMOS)

    const editButtons = wrapper.findAll('[data-test="edit-insumo"]')
    const deleteButtons = wrapper.findAll('[data-test="delete-insumo"]')
    expect(editButtons).toHaveLength(3)
    expect(deleteButtons).toHaveLength(3)

    await editButtons[0].trigger('click')
    expect(wrapper.emitted('edit')).toBeDefined()
    expect(wrapper.emitted('edit')![0][0]).toEqual(INSUMOS[0])

    await deleteButtons[1].trigger('click')
    expect(wrapper.emitted('delete')).toBeDefined()
    expect(wrapper.emitted('delete')![0][0]).toEqual(INSUMOS[1])
  })

  it('hides the edit/delete actions for operador and consulta', async () => {
    const wrapper = await mountTable(INSUMOS, false)

    expect(wrapper.findAll('[data-test="edit-insumo"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-insumo"]')).toHaveLength(0)
  })

  it('shows an empty state when there are no insumos', async () => {
    const wrapper = await mountTable([])
    expect(wrapper.text()).toContain('Sin insumos registrados')
  })

  it('builds the categoria header funnel from the categorias prop', async () => {
    const wrapper = mount(InsumosTable, {
      props: { rows: INSUMOS, categorias: CATEGORIAS },
      global: { plugins: [ElementPlus] },
    })
    await nextTick()

    const categoriaColumn = wrapper
      .findAllComponents({ name: 'ElTableColumn' })
      .find((c) => c.props('columnKey') === 'categoria')

    expect(categoriaColumn!.props('filters')).toEqual([
      { text: 'Granos', value: 1 },
      { text: 'Abarrotes', value: 2 },
    ])
  })

  it('renders no funnel when no categorias are passed (empty filters)', async () => {
    const wrapper = await mountTable(INSUMOS)

    const categoriaColumn = wrapper
      .findAllComponents({ name: 'ElTableColumn' })
      .find((c) => c.props('columnKey') === 'categoria')

    expect(categoriaColumn!.props('filters')).toEqual([])
  })

  it('normalizes an el-table filter-change on categoria into a typed emit', async () => {
    const wrapper = await mountTable(INSUMOS)

    wrapper.findComponent({ name: 'ElTable' }).vm.$emit('filter-change', { categoria: [2] })
    await nextTick()

    expect(wrapper.emitted('filter-change')).toBeDefined()
    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ categoria_id: 2 })
  })

  it('emits null when the categoria column filter is cleared', async () => {
    const wrapper = await mountTable(INSUMOS)

    wrapper.findComponent({ name: 'ElTable' }).vm.$emit('filter-change', { categoria: [] })
    await nextTick()

    expect(wrapper.emitted('filter-change')![0][0]).toEqual({ categoria_id: null })
  })

  it('maps an el-table sort-change into a typed {prop, order} emit', async () => {
    const wrapper = await mountTable(INSUMOS)

    wrapper
      .findComponent({ name: 'ElTable' })
      .vm.$emit('sort-change', { column: { key: 'stock_actual' }, order: 'descending' })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'stock_actual', order: 'desc' })
  })
})
