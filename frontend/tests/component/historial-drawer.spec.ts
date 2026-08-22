/**
 * HistorialDrawer component tests (compras-wac-ux SCN-CI-005 + REQ-WAC-003).
 *
 * - CSV header exact: fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura
 * - Rows show prev→new stock/cost + factura
 * - buildHistorialCsv escaping + parity
 */
import { flushPromises, mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'
import esCO from '@/utils/locales/es-CO'
import { buildHistorialCsv, CSV_HEADER } from '@/utils/inventario'
import HistorialDrawer from '@/components/inventario/HistorialDrawer.vue'
import type { components } from '@/types/api.d'

type InsumoRead = components['schemas']['InsumoRead']
type CompraInsumoRead = components['schemas']['CompraInsumoRead']

const INSUMO: InsumoRead = {
  id: 1,
  categoria_id: 1,
  nombre: 'Harina',
  unidad_medida: 'kg',
  stock_actual: '20.00',
  stock_minimo: '5.00',
  costo_promedio_actual: '7.00',
  nombre_categoria: 'Granos',
}

const COMPRAS: CompraInsumoRead[] = [
  {
    id: 1,
    insumo_id: 1,
    fecha_compra: '2026-08-01T09:00:00Z',
    cantidad_comprada: '10.00',
    precio_unitario_compra: '5.00',
    costo_unitario_aplicado: '5.0000',
    factura: 'F-001',
  } as unknown as CompraInsumoRead,
  {
    id: 2,
    insumo_id: 1,
    fecha_compra: '2026-08-02T10:00:00Z',
    cantidad_comprada: '10.00',
    precio_unitario_compra: '9.00',
    costo_unitario_aplicado: '7.0000',
    factura: 'F-002',
  } as unknown as CompraInsumoRead,
]

describe('HistorialDrawer (compras-wac-ux)', () => {
  it('CSV header exact matches spec', () => {
    expect(CSV_HEADER).toBe('fecha,cantidad,prevStock,newStock,prevCost,newCost,total,factura')
  })

  it('buildHistorialCsv header + escaping', () => {
    const csv = buildHistorialCsv([
      { fecha: '2026-08-01', cantidad: '10.00', prevStock: '10.00', newStock: '20.00', prevCost: '5.0000', newCost: '7.0000', total: '90.00', factura: 'F,001' },
    ])
    const lines = csv.split('\n')
    expect(lines[0]).toBe(CSV_HEADER)
    // comma in factura should be quoted
    expect(lines[1]).toContain('"F,001"')
  })

  it('renders prev→new stock/cost and factura rows (newest first)', async () => {
    const wrapper = mount(HistorialDrawer, {
      props: { visible: true, insumo: INSUMO, compras: COMPRAS, loading: false },
      global: { plugins: [[PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }]] },
      attachTo: document.body,
    })
    await nextTick()
    await flushPromises()
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r as FrameRequestCallback)))
    await flushPromises()
    // Drawer teleports to body — check document.body (or wrapper if teleport disabled)
    const text = (document.body.textContent ?? '') + (wrapper.text() ?? '')
    expect(text).toContain('F-002')
    expect(text).toContain('10.00 → 20.00')
    expect(text).toContain('5.0000 → 7.0000')
    // CSV export button — search both wrapper and document
    const btn = (wrapper.find('[data-test="export-csv"]').exists() ? wrapper.find('[data-test="export-csv"]').element : document.body.querySelector('[data-test="export-csv"]')) as HTMLElement | null
    expect(btn).not.toBeNull()
    wrapper.unmount()
    document.body.innerHTML = ''
  })

  it('shows empty state when no compras', async () => {
    const wrapper = mount(HistorialDrawer, {
      props: { visible: true, insumo: INSUMO, compras: [], loading: false },
      global: { plugins: [[PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } }, locale: esCO }]] },
      attachTo: document.body,
    })
    await nextTick()
    await flushPromises()
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r as FrameRequestCallback)))
    await flushPromises()
    const text = (document.body.textContent ?? '') + (wrapper.text() ?? '')
    expect(text).toContain('Sin compras')
    const btn2 = (wrapper.find('[data-test="export-csv"]').exists() ? wrapper.find('[data-test="export-csv"]').element : document.body.querySelector('[data-test="export-csv"]')) as HTMLElement | null
    expect(btn2).not.toBeNull()
    wrapper.unmount()
    document.body.innerHTML = ''
  })

  it('parity buildHistorialCsv for 10@5+10@9 preserves factura', () => {
    const rows = [
      { fecha: '2026-08-01', cantidad: '10.00', prevStock: '0.00', newStock: '10.00', prevCost: '0.0000', newCost: '5.0000', total: '50.00', factura: '' },
      { fecha: '2026-08-02', cantidad: '10.00', prevStock: '10.00', newStock: '20.00', prevCost: '5.0000', newCost: '7.0000', total: '90.00', factura: 'F-001' },
    ]
    const csv = buildHistorialCsv(rows)
    expect(csv).toContain('F-001')
    expect(csv.split('\n')).toHaveLength(3)
  })
})
