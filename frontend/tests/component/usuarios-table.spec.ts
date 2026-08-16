/**
 * UsuariosTable component tests (PR11, spec MOD-5 usuarios).
 *
 * Admin-only module table (route meta.roles ['admin']): id/nombre/email plus
 * the rol shown with its es-CO label (Administrador/Operador/Consulta) and a
 * rol-colored tag. Editar emits the row; Eliminar is HIDDEN for the current
 * user's own row ("can't delete self" — the backend also rejects it with
 * 400 "Cannot delete your own user").
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. el-tag/el-button cells
 * still need the ElementPlus plugin until slice 2b.
 */
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import DataTable from 'primevue/datatable'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import UsuariosTable from '@/components/usuarios/UsuariosTable.vue'
import type { components } from '@/types/api.d'

type UsuarioRead = components['schemas']['UsuarioRead']

const USUARIOS: UsuarioRead[] = [
  { id: 1, nombre: 'Ana Admin', email: 'ana@arpia.com.co', rol: 'admin' },
  { id: 2, nombre: 'Pepe Operador', email: 'pepe@arpia.com.co', rol: 'operador' },
  { id: 3, nombre: 'Coni Consulta', email: 'coni@arpia.com.co', rol: 'consulta' },
]

async function mountTable(
  rows: UsuarioRead[] = USUARIOS,
  currentUserId: number | null = 1,
): Promise<VueWrapper> {
  const wrapper = mount(UsuariosTable, {
    props: { rows, currentUserId },
    global: {
      plugins: [
        ElementPlus,
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  await flushPromises()
  return wrapper
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('UsuariosTable (MOD-5 usuarios)', () => {
  it('renders id, nombre, email and the es-CO rol labels', async () => {
    const wrapper = await mountTable()

    const text = wrapper.text()
    expect(text).toContain('#')
    expect(text).toContain('Nombre')
    expect(text).toContain('Email')
    expect(text).toContain('Rol')
    expect(text).toContain('Ana Admin')
    expect(text).toContain('ana@arpia.com.co')
    expect(text).toContain('Administrador')
    expect(text).toContain('Operador')
    expect(text).toContain('Consulta')
  })

  it('renders one DataTable row per user', async () => {
    const wrapper = await mountTable()

    expect(wrapper.findComponent(DataTable).exists()).toBe(true)
    expect(wrapper.findAll('tbody tr')).toHaveLength(3)
  })

  it('emits edit and delete with the row for other users', async () => {
    const wrapper = await mountTable(USUARIOS, 1)

    await wrapper.findAll('[data-test="edit-usuario"]')[1].trigger('click')
    expect(wrapper.emitted('edit')![0][0]).toMatchObject({ id: 2, nombre: 'Pepe Operador' })

    await wrapper.findAll('[data-test="delete-usuario"]')[1].trigger('click')
    expect(wrapper.emitted('delete')![0][0]).toMatchObject({ id: 3, nombre: 'Coni Consulta' })
  })

  it("hides the delete action for the current user row (can't delete self)", async () => {
    const wrapper = await mountTable(USUARIOS, 1)

    const deletes = wrapper.findAll('[data-test="delete-usuario"]')
    expect(deletes).toHaveLength(2) // rows 2 and 3 only
    // The self row still offers edit (a self-demote is rejected by the server).
    expect(wrapper.findAll('[data-test="edit-usuario"]')).toHaveLength(3)
  })

  it('shows the empty state', async () => {
    const wrapper = await mountTable([])

    expect(wrapper.text()).toContain('Sin usuarios registrados')
  })
})
