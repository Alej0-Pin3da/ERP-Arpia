/**
 * MaestrosTable component tests (PR11, spec MOD-5).
 *
 * The generic el-table is driven by the per-entity column config:
 *  - renders each configured column with the row value; empty/null optionals
 *    render an em dash ('—')
 *  - canEdit=false hides the Editar/Eliminar actions (operador/consulta are
 *    read-only — writes are admin-only server-side)
 *  - Editar/Eliminar emit the row to the parent (view owns the API calls)
 *  - the entity's emptyText renders in the empty state
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { afterEach, describe, expect, it } from 'vitest'

import MaestrosTable from '@/components/maestros/MaestrosTable.vue'
import { MAESTRO_ENTITIES, type MaestroColumn, type MaestroRow } from '@/utils/maestros'

const CLIENTE_COLUMNS = MAESTRO_ENTITIES[0].columns

const CLIENTES: MaestroRow[] = [
  { id: 1, nombre: 'Ana Torres', documento_identidad: 'CC 123', email: 'ana@arpia.com.co', telefono: '3001234567' },
  { id: 2, nombre: 'Luis Gómez', documento_identidad: null, email: null, telefono: '' },
]

async function mountTable(
  rows: MaestroRow[],
  columns: MaestroColumn[] = CLIENTE_COLUMNS,
  canEdit = true,
): Promise<VueWrapper> {
  const wrapper = mount(MaestrosTable, {
    props: { rows, columns, emptyText: 'Sin clientes registrados', canEdit },
    global: { plugins: [ElementPlus] },
  })
  await nextTick()
  await flushPromises()
  return wrapper
}

import { nextTick } from 'vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('MaestrosTable (MOD-5)', () => {
  it('renders every configured column with the row values', async () => {
    const wrapper = await mountTable(CLIENTES)

    const text = wrapper.text()
    expect(text).toContain('Nombre')
    expect(text).toContain('Documento')
    expect(text).toContain('Email')
    expect(text).toContain('Teléfono')
    expect(text).toContain('Ana Torres')
    expect(text).toContain('CC 123')
    expect(text).toContain('ana@arpia.com.co')
  })

  it('renders an em dash for empty optional values', async () => {
    const wrapper = await mountTable(CLIENTES)

    const text = wrapper.text()
    expect(text).toContain('Luis Gómez')
    expect(text).toContain('—')
    // Exactly two rows: the dash fills the 3 empty cells of row 2.
    expect(text.split('—')).toHaveLength(4)
  })

  it('renders a single-column table for a name-only entity config', async () => {
    const wrapper = await mountTable([{ id: 1, nombre: 'Alimentos' }], MAESTRO_ENTITIES[1].columns)

    expect(wrapper.text()).toContain('Nombre')
    expect(wrapper.text()).toContain('Alimentos')
  })

  it('shows the entity emptyText when there are no rows', async () => {
    const wrapper = await mountTable([])

    expect(wrapper.text()).toContain('Sin clientes registrados')
  })

  it('emits edit and delete with the row', async () => {
    const wrapper = await mountTable(CLIENTES)

    await wrapper.findAll('[data-test="edit-maestro"]')[0].trigger('click')
    expect(wrapper.emitted('edit')![0][0]).toMatchObject({ id: 1, nombre: 'Ana Torres' })

    await wrapper.findAll('[data-test="delete-maestro"]')[1].trigger('click')
    expect(wrapper.emitted('delete')![0][0]).toMatchObject({ id: 2, nombre: 'Luis Gómez' })
  })

  it('hides the actions for canEdit=false (read-only roles)', async () => {
    const wrapper = await mountTable(CLIENTES, CLIENTE_COLUMNS, false)

    expect(wrapper.findAll('[data-test="edit-maestro"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-maestro"]')).toHaveLength(0)
    expect(wrapper.text()).toContain('Ana Torres') // list still renders
  })
})
