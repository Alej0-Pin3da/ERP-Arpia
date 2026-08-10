/**
 * ProductosTable component tests (PR10, spec MOD-5).
 *
 * Mounts the REAL ProductosTable with Element Plus:
 *  - the list renders the client-joined tipo label, nombre,
 *    requiere_fabricacion as a Sí/No tag, and the two money fields es-CO
 *    ($12.345,67 format)
 *  - Editar / Eliminar actions emit `edit` / `delete` with the row; they are
 *    hidden when canEdit=false (operador/consulta)
 *  - a "Variantes" action emits `select-variantes` with the row (the view
 *    then lazy-fetches GET /productos/{id}/variantes)
 *  - the empty state renders
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import ProductosTable from '@/components/productos/ProductosTable.vue'

type ProductoRow = {
  id: number
  tipo: string
  nombre: string
  requiere_fabricacion: boolean
  costos_operativos_fijos: string
  precio_venta_sugerido: string
}

const ROWS: ProductoRow[] = [
  {
    id: 1,
    tipo: 'Alimentos',
    nombre: 'Arepa de choclo',
    requiere_fabricacion: true,
    costos_operativos_fijos: '5000.00',
    precio_venta_sugerido: '12000.00',
  },
  {
    id: 2,
    tipo: 'Tipo #99', // tipo gone -> fallback label already joined by the mapper
    nombre: 'Detergente',
    requiere_fabricacion: false,
    costos_operativos_fijos: '0.00',
    precio_venta_sugerido: '8000.00',
  },
]

async function mountTable(canEdit = true, rows: ProductoRow[] = ROWS): Promise<VueWrapper> {
  const wrapper = mount(ProductosTable, {
    props: { rows, loading: false, canEdit },
    global: { plugins: [ElementPlus] },
  })
  await flushPromises()
  return wrapper
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('ProductosTable (MOD-5)', () => {
  it('renders the joined tipo label, name, fabrication tag and es-CO money', async () => {
    const wrapper = await mountTable()

    const text = wrapper.text()
    expect(text).toContain('Alimentos') // client-joined tipo label
    expect(text).toContain('Arepa de choclo')
    expect(text).toContain('$12.000,00') // precio_venta_sugerido es-CO
    expect(text).toContain('$5.000,00') // costos_operativos_fijos es-CO
    expect(text).toContain('Sí') // requiere_fabricacion tag
    expect(text).toContain('No')
  })

  it('renders the fallback tipo label when the join failed', async () => {
    const wrapper = await mountTable()
    expect(wrapper.text()).toContain('Tipo #99')
  })

  it('emits edit and delete with the row when the actions are visible', async () => {
    const wrapper = await mountTable()

    await wrapper.findAll('[data-test="edit-producto"]')[0].trigger('click')
    expect(wrapper.emitted('edit')![0][0]).toMatchObject({ id: 1, nombre: 'Arepa de choclo' })

    await wrapper.findAll('[data-test="delete-producto"]')[1].trigger('click')
    expect(wrapper.emitted('delete')![0][0]).toMatchObject({ id: 2, nombre: 'Detergente' })
  })

  it('emits select-variantes with the row', async () => {
    const wrapper = await mountTable()

    await wrapper.findAll('[data-test="producto-variantes"]')[0].trigger('click')
    expect(wrapper.emitted('select-variantes')![0][0]).toMatchObject({ id: 1 })
  })

  it('hides the edit/delete/variantes actions when canEdit is false', async () => {
    const wrapper = await mountTable(false)

    expect(wrapper.findAll('[data-test="edit-producto"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-producto"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="producto-variantes"]')).toHaveLength(0)
  })

  it('renders the empty state when there are no products', async () => {
    const wrapper = await mountTable(true, [])
    expect(wrapper.text()).toContain('Sin productos registrados')
  })

  it('maps an el-table sort-change into a typed {prop, order} emit', async () => {
    const wrapper = await mountTable()

    wrapper
      .findComponent({ name: 'ElTable' })
      .vm.$emit('sort-change', { column: { key: 'precio_venta_sugerido' }, order: 'descending' })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'precio_venta_sugerido', order: 'desc' })
  })

  it('maps a cleared sort (null order) for the nombre column', async () => {
    const wrapper = await mountTable()

    wrapper.findComponent({ name: 'ElTable' }).vm.$emit('sort-change', { column: { key: 'nombre' }, order: null })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'nombre', order: null })
  })
})
