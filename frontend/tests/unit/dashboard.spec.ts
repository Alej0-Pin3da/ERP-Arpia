/**
 * Dashboard analytics mapping tests (task 1.9, spec DASH-1..3).
 *
 * Pure mappers over the analytics endpoints — the backend returns ONLY months
 * with sales (DASH-1: the chart must fill the gaps with zeroes), margen rows
 * carry only IDs (DASH-3: names/variants are joined client-side with graceful
 * fallbacks), and low-stock rows carry Decimal strings (DASH-2: severity is
 * derived from the stock ratio). Tested as pure functions with zero mocks.
 */
import { describe, expect, it } from 'vitest'

import type { components } from '@/types/api.d'
import {
  buildMargenRows,
  fillMissingMonths,
  lastMonthSummary,
  stockSeverity,
} from '@/utils/dashboard'

type VentasMensualesRead = components['schemas']['VentasMensualesRead']
type InsumoBajoStockRead = components['schemas']['InsumoBajoStockRead']
type MargenProductoRead = components['schemas']['MargenProductoRead']
type ProductoRead = components['schemas']['ProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']

const ROW = (mes: string, total: string, cantidad = 1): VentasMensualesRead => ({ mes, total, cantidad })

describe('fillMissingMonths (DASH-1 gap fill)', () => {
  it('fills a gap between the first and last month with zero totals', () => {
    const rows = [ROW('2026-01-01', '1000.00', 3), ROW('2026-03-01', '2500.50', 5)]

    const filled = fillMissingMonths(rows)

    expect(filled).toHaveLength(3)
    expect(filled[0]).toMatchObject({ mes: '2026-01', total: 1000, cantidad: 3 })
    // February has no API row — must be zeroed, not skipped.
    expect(filled[1]).toMatchObject({ mes: '2026-02', total: 0, cantidad: 0 })
    expect(filled[2]).toMatchObject({ mes: '2026-03', total: 2500.5, cantidad: 5 })
  })

  it('sorts unsorted input ascending by month before filling', () => {
    const rows = [ROW('2026-03-01', '3000'), ROW('2026-01-01', '1000')]

    const filled = fillMissingMonths(rows)

    expect(filled.map((r) => r.mes)).toEqual(['2026-01', '2026-02', '2026-03'])
    expect(filled[1].total).toBe(0)
  })

  it('handles a single row (no gap to fill)', () => {
    const filled = fillMissingMonths([ROW('2026-05-01', '999.99', 2)])

    expect(filled).toHaveLength(1)
    expect(filled[0]).toMatchObject({ mes: '2026-05', total: 999.99, cantidad: 2 })
  })

  it('returns an empty list for an empty analytics response', () => {
    expect(fillMissingMonths([])).toEqual([])
  })

  it('produces es-CO short month labels (ene 2026)', () => {
    const filled = fillMissingMonths([ROW('2026-01-01', '1000')])

    expect(filled[0].label).toBe('ene 2026')
  })
})

describe('lastMonthSummary (DASH-1 KPI source)', () => {
  it('returns the most recent month row (raw Decimal strings preserved)', () => {
    const rows = [ROW('2026-01-01', '1000.00', 3), ROW('2026-03-01', '2500.50', 5)]

    expect(lastMonthSummary(rows)).toEqual({ mes: '2026-03', total: '2500.50', cantidad: 5 })
  })

  it('picks the max month even when input is unsorted', () => {
    const rows = [ROW('2026-03-01', '900'), ROW('2026-01-01', '100')]

    expect(lastMonthSummary(rows)?.total).toBe('900')
  })

  it('returns null when there are no rows (KPI shows "$0,00")', () => {
    expect(lastMonthSummary([])).toBeNull()
  })
})

describe('buildMargenRows (DASH-3 client-side join)', () => {
  const productos: ProductoRead[] = [
    {
      id: 1,
      tipo_producto_id: 1,
      nombre: 'Arepa de huevo',
      requiere_fabricacion: true,
      costos_operativos_fijos: '0',
      precio_venta_sugerido: '5000',
    },
    {
      id: 2,
      tipo_producto_id: 1,
      nombre: 'Empanada',
      requiere_fabricacion: true,
      costos_operativos_fijos: '0',
      precio_venta_sugerido: '3000',
    },
  ]
  const variantes: VarianteProductoRead[] = [
    { id: 5, producto_id: 2, nombre_variante: 'De carne', precio_venta: '3500' },
  ]
  const margen = (
    producto_id: number,
    variante_id: number | null,
    margen_total = '1000.00',
    margen_promedio = '500.00',
  ): MargenProductoRead => ({ producto_id, variante_id, margen_total, margen_promedio })

  it('joins product names and renders "(base)" for null variantes', () => {
    const rows = buildMargenRows([margen(1, null)], productos, variantes)

    expect(rows).toHaveLength(1)
    expect(rows[0]).toMatchObject({
      producto_id: 1,
      nombre: 'Arepa de huevo',
      variante: '(base)',
      margen_total: '1000.00',
      margen_promedio: '500.00',
    })
  })

  it('renders the variant label when the margen row references one', () => {
    const rows = buildMargenRows([margen(2, 5)], productos, variantes)

    expect(rows[0].nombre).toBe('Empanada')
    expect(rows[0].variante).toBe('De carne')
  })

  it('falls back to "Producto #{id}" when the product no longer exists', () => {
    const rows = buildMargenRows([margen(99, null)], productos, variantes)

    expect(rows[0].nombre).toBe('Producto #99')
  })

  it('falls back to "Variante #{id}" when the variant is missing', () => {
    const rows = buildMargenRows([margen(1, 77)], productos, variantes)

    expect(rows[0].variante).toBe('Variante #77')
  })

  it('preserves the margen response order', () => {
    const rows = buildMargenRows([margen(2, 5), margen(1, null)], productos, variantes)

    expect(rows.map((r) => r.producto_id)).toEqual([2, 1])
  })
})

describe('stockSeverity (DASH-2 below-minimum highlight)', () => {
  it('flags a stock below half the minimum as danger', () => {
    const row: InsumoBajoStockRead = {
      insumo_id: 1,
      nombre: 'Harina',
      unidad_medida: 'kg',
      stock_actual: '2.0',
      stock_minimo: '10.0',
    }

    expect(stockSeverity(row.stock_actual, row.stock_minimo)).toBe('danger')
  })

  it('flags a stock between half the minimum and the minimum as warning', () => {
    const row: InsumoBajoStockRead = {
      insumo_id: 2,
      nombre: 'Huevo',
      unidad_medida: 'un',
      stock_actual: '6.0',
      stock_minimo: '10.0',
    }

    expect(stockSeverity(row.stock_actual, row.stock_minimo)).toBe('warning')
  })

  it('treats stock at or above the minimum as ok', () => {
    expect(stockSeverity('10', '10')).toBe('ok')
    expect(stockSeverity('12', '10')).toBe('ok')
  })

  it('treats zero stock as danger (worst case)', () => {
    expect(stockSeverity('0', '5')).toBe('danger')
  })

  it('treats unparseable values as ok (no false alarm)', () => {
    expect(stockSeverity('n/a', '5')).toBe('ok')
    expect(stockSeverity(null, '5')).toBe('ok')
  })
})
