/**
 * SociosTable component tests (PR8, spec MOD-3).
 *
 * Mounts the REAL SociosTable with PrimeVue (slice 1b+):
 * renders partner rows with es-CO percentages, shows the sum-to-100 progress
 * (current sum vs 100, with a green ProgressBar at exactly 100), hides
 * edit/delete actions for read-only roles (can-edit=false), emits
 * `edit`/`delete` with the row, and shows the empty state. Column sort is a
 * DataTable lazy `@sort` normalized by parsePrimeVueSort. The tree is fully
 * PrimeVue since slice 3a (ProgressBar replaced the last el-progress, so the
 * ElementPlus plugin was dropped).
 */
import { mount, type VueWrapper } from '@vue/test-utils'
import DataTable from 'primevue/datatable'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import SociosTable from '@/components/finanzas/SociosTable.vue'
import type { components } from '@/types/api.d'

type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']

const SOCIOS: SocioConfiguracionRead[] = [
  { id: 1, nombre: 'Ana María', porcentaje_participacion: '60.00' },
  { id: 2, nombre: 'Carlos Ruiz', porcentaje_participacion: '40.00' },
]

const PARTIAL: SocioConfiguracionRead[] = [
  { id: 1, nombre: 'Ana María', porcentaje_participacion: '60.00' },
  { id: 2, nombre: 'Carlos Ruiz', porcentaje_participacion: '30.00' },
]

async function mountTable(rows: SocioConfiguracionRead[], canEdit = true): Promise<VueWrapper> {
  const wrapper = mount(SociosTable, {
    props: { rows, canEdit },
    global: {
      plugins: [
        [PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }],
      ],
    },
  })
  await nextTick()
  return wrapper
}

describe('SociosTable (MOD-3)', () => {
  it('renders partner rows with es-CO percentages and a complete progress at 100', async () => {
    const wrapper = await mountTable(SOCIOS)

    const text = wrapper.text()
    expect(text).toContain('Ana María')
    expect(text).toContain('Carlos Ruiz')
    expect(text).toContain('60')
    expect(text).toContain('40')

    // Sum-to-100 progress: 100% shown and marked complete.
    expect(text).toContain('100%')
    expect(wrapper.find('[data-test="socios-progress"]').exists()).toBe(true)
    // Migrated to PrimeVue ProgressBar (slice 3a): bar present with the value.
    expect(wrapper.find('.p-progressbar').exists()).toBe(true)
    expect(wrapper.find('[role="progressbar"]').attributes('aria-valuenow')).toBe('100')
  })

  it('shows a warning-style progress when the sum is below 100', async () => {
    const wrapper = await mountTable(PARTIAL)

    expect(wrapper.text()).toContain('90%')
    expect(wrapper.text()).toContain('100%') // target rendered too
    expect(wrapper.find('.p-progressbar').exists()).toBe(true)
    expect(wrapper.find('[role="progressbar"]').attributes('aria-valuenow')).toBe('90')
  })

  it('hides the progress section when there are no socios', async () => {
    const wrapper = await mountTable([])

    expect(wrapper.find('[data-test="socios-progress"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Sin socios configurados')
  })

  it('emits `edit` and `delete` with the row when the actions are clicked', async () => {
    const wrapper = await mountTable(SOCIOS)

    await wrapper.findAll('[data-test="edit-socio"]')[0].trigger('click')
    await wrapper.findAll('[data-test="delete-socio"]')[1].trigger('click')

    expect(wrapper.emitted('edit')![0][0]).toEqual(SOCIOS[0])
    expect(wrapper.emitted('delete')![0][0]).toEqual(SOCIOS[1])
  })

  it('hides the edit/delete actions for read-only roles', async () => {
    const wrapper = await mountTable(SOCIOS, false)

    expect(wrapper.findAll('[data-test="edit-socio"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="delete-socio"]')).toHaveLength(0)
  })

  it('maps a PrimeVue sort payload into a typed {prop, order} emit', async () => {
    const wrapper = await mountTable(SOCIOS)

    wrapper
      .findComponent(DataTable)
      .vm.$emit('sort', { sortField: 'porcentaje_participacion', sortOrder: 1 })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({
      prop: 'porcentaje_participacion',
      order: 'asc',
    })
  })

  it('maps a cleared sort (order 0) for the nombre column', async () => {
    const wrapper = await mountTable(SOCIOS)

    wrapper.findComponent(DataTable).vm.$emit('sort', { sortField: 'nombre', sortOrder: 0 })
    await nextTick()

    expect(wrapper.emitted('sort-change')![0][0]).toEqual({ prop: 'nombre', order: null })
  })
})
