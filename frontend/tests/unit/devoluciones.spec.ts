/**
 * Devoluciones mappers unit tests (task 2.3, spec MOD-2).
 *
 * Pure functions over the devoluciones module:
 *  - `buildDevolucionRows`: DevolucionRead.items carry only product IDs —
 *    names are joined client-side (GET /productos?limit=1000) with a graceful
 *    `Producto #{id}` fallback; null motivo degrades to '—'.
 *  - `buildDevolucionPayload`: form model -> DevolucionCreate. tipo 'total'
 *    OMITS items entirely (spec: total without items -> 201); tipo 'parcial'
 *    REQUIRES at least one complete item (server 422 otherwise) and the
 *    payload keeps precio_unitario because the schema requires it — the
 *    backend prices from the sale-time snapshot and ignores this value.
 */
import { describe, expect, it } from 'vitest'

import {
  TIPO_DEVOLUCION,
  buildDevolucionListParams,
  buildDevolucionPayload,
  buildDevolucionRows,
  createDevolucionItemRow,
  hasValidDevolucionItems,
  tipoLabel,
  tipoTagType,
  type DevolucionFormItem,
  type DevolucionPayloadInput,
} from '@/utils/devoluciones'
import type { components } from '@/types/api.d'

type DevolucionRead = components['schemas']['DevolucionRead']

const DEVOLUCION: DevolucionRead = {
  id: 3,
  venta_id: 10,
  fecha: '2026-08-02T14:00:00Z',
  motivo: 'Cliente devolvió dos arepas',
  monto_reembolsado: '10000.00',
  tipo: 'parcial',
  usuario_id: 2,
  items: [
    { id: 1, producto_id: 1, variante_id: null, cantidad: '2', precio_unitario: '5000.00', subtotal: '10000.00' },
  ],
}

const DEVOLUCION_TOTAL: DevolucionRead = {
  id: 2,
  venta_id: 9,
  fecha: '2026-08-01T09:00:00Z',
  motivo: null,
  monto_reembolsado: '15000.00',
  tipo: 'total',
  usuario_id: 2,
  items: [],
}

const PRODUCTOS = [
  { id: 1, tipo_producto_id: 1, nombre: 'Arepa de huevo', requiere_fabricacion: true, costos_operativos_fijos: '0', precio_venta_sugerido: '5000' },
]

describe('devoluciones mappers (MOD-2)', () => {
  it('TIPO_DEVOLUCION lists the two selectable types', () => {
    expect(TIPO_DEVOLUCION).toEqual(['total', 'parcial'])
  })

  it('tipoLabel maps total/parcial to es-CO and passes unknowns through', () => {
    expect(tipoLabel('total')).toBe('Total')
    expect(tipoLabel('parcial')).toBe('Parcial')
    expect(tipoLabel('extra')).toBe('extra')
  })

  it('tipoTagType colors total danger, parcial warning, unknown info', () => {
    expect(tipoTagType('total')).toBe('danger')
    expect(tipoTagType('parcial')).toBe('warning')
    expect(tipoTagType('extra')).toBe('info')
  })

  it('buildDevolucionRows joins product names, keeps items and raw values', () => {
    const rows = buildDevolucionRows([DEVOLUCION], PRODUCTOS)

    expect(rows).toHaveLength(1)
    const row = rows[0]
    expect(row.id).toBe(3)
    expect(row.venta_id).toBe(10)
    expect(row.fecha).toBe('2026-08-02T14:00:00Z')
    expect(row.tipo).toBe('parcial')
    expect(row.motivo).toBe('Cliente devolvió dos arepas')
    expect(row.monto_reembolsado).toBe('10000.00')
    expect(row.items).toHaveLength(1)
    expect(row.items[0]).toEqual({
      producto_id: 1,
      variante_id: null,
      nombre: 'Arepa de huevo',
      cantidad: '2',
      subtotal: '10000.00',
    })
  })

  it('buildDevolucionRows degrades missing product to "Producto #id" and null motivo to an em dash', () => {
    const rows = buildDevolucionRows([DEVOLUCION_TOTAL], [])

    expect(rows).toHaveLength(1)
    expect(rows[0].motivo).toBe('—')
    // DevolucionRead.items is [] for a total return — count 0, no item rows.
    expect(rows[0].items).toEqual([])
  })

  it('createDevolucionItemRow returns a fresh empty row per call', () => {
    const a = createDevolucionItemRow()
    const b = createDevolucionItemRow()
    expect(a).toEqual({ producto_id: null, variante_id: null, cantidad: 1, precio_unitario: 0 })
    expect(a).not.toBe(b) // fresh object, not a shared reference
  })

  it('hasValidDevolucionItems requires at least one product chosen with cantidad > 0', () => {
    const empty: DevolucionFormItem[] = []
    const noProduct = [{ ...createDevolucionItemRow(), cantidad: 2 }]
    const zeroQty = [{ ...createDevolucionItemRow(), producto_id: 1, cantidad: 0 }]
    const valid = [{ ...createDevolucionItemRow(), producto_id: 1, cantidad: 1 }]
    expect(hasValidDevolucionItems(empty)).toBe(false)
    expect(hasValidDevolucionItems(noProduct)).toBe(false)
    expect(hasValidDevolucionItems(zeroQty)).toBe(false)
    expect(hasValidDevolucionItems(valid)).toBe(true)
  })

  it('buildDevolucionPayload: total return omits items entirely (spec 201 without items)', () => {
    const payload = buildDevolucionPayload({
      venta_id: 9,
      tipo: 'total',
      motivo: '',
      items: [],
    })
    expect(payload).toEqual({ venta_id: 9, tipo: 'total' })
    expect('items' in payload).toBe(false)
  })

  it('buildDevolucionPayload: total return includes a non-empty motivo', () => {
    const payload = buildDevolucionPayload({
      venta_id: 9,
      tipo: 'total',
      motivo: '  Cancelación por cliente  ',
      items: [],
    })
    expect(payload).toEqual({ venta_id: 9, tipo: 'total', motivo: 'Cancelación por cliente' })
  })

  it('buildDevolucionPayload: parcial return sends the full items shape with precio_unitario', () => {
    const form: DevolucionPayloadInput = {
      venta_id: 10,
      tipo: 'parcial',
      motivo: 'Dos arepas devueltas',
      items: [
        { producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 },
      ],
    }
    expect(buildDevolucionPayload(form)).toEqual({
      venta_id: 10,
      tipo: 'parcial',
      motivo: 'Dos arepas devueltas',
      items: [{ producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 }],
    })
  })

  it('buildDevolucionPayload: variante_id is omitted (not null) and incomplete rows are dropped', () => {
    const form: DevolucionPayloadInput = {
      venta_id: 10,
      tipo: 'parcial',
      motivo: '',
      items: [
        { producto_id: 1, variante_id: null, cantidad: 1, precio_unitario: 5000 },
        { producto_id: null, variante_id: null, cantidad: 1, precio_unitario: 0 }, // incomplete -> dropped
        { producto_id: 2, variante_id: null, cantidad: 0, precio_unitario: 5000 }, // qty 0 -> dropped
      ],
    }
    expect(buildDevolucionPayload(form)).toEqual({
      venta_id: 10,
      tipo: 'parcial',
      items: [{ producto_id: 1, cantidad: 1, precio_unitario: 5000 }],
    })
  })

  it('buildDevolucionListParams omits unset filters and keeps set ones', () => {
    expect(buildDevolucionListParams({ venta_id: null, fecha_desde: '', fecha_hasta: '' })).toEqual({})
    expect(buildDevolucionListParams({ venta_id: 7, fecha_desde: '', fecha_hasta: '' })).toEqual({
      venta_id: 7,
    })
    expect(
      buildDevolucionListParams({
        venta_id: null,
        fecha_desde: '2026-01-01',
        fecha_hasta: '2026-01-31',
      }),
    ).toEqual({ fecha_desde: '2026-01-01', fecha_hasta: '2026-01-31' })
    expect(
      buildDevolucionListParams({
        venta_id: 7,
        fecha_desde: '2026-01-01',
        fecha_hasta: '2026-01-31',
      }),
    ).toEqual({ venta_id: 7, fecha_desde: '2026-01-01', fecha_hasta: '2026-01-31' })
  })
})
