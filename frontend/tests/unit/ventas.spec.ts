/**
 * Ventas module mapping tests (tasks 2.1+2.2, spec MOD-1).
 *
 * Pure mappers over the ventas module:
 *  - the list is UNBOUNDED server-side (GET /ventas has no pagination params),
 *    so the client slices it to the most recent N (MOD-1 "pagination deferred");
 *  - VentaRead.detalles carry only IDs — product/variant names are joined
 *    client-side with graceful fallbacks (buildMargenRows pattern);
 *  - the register form model maps to the VentaCreate POST body, mirroring the
 *    server total: subtotal * (1 - descuento/100) (backend services/inventory).
 * Tested as pure functions with zero mocks.
 */
import { describe, expect, it } from 'vitest'

import type { components } from '@/types/api.d'
import {
  buildVentaPayload,
  buildVentaRows,
  canalLabel,
  computeTotalPreview,
  createDetalleRow,
  estadoLabel,
  hasValidDetalles,
  sliceVentas,
  ventaSubtotal,
  type VentasFormDetalle,
} from '@/utils/ventas'

type VentaRead = components['schemas']['VentaRead']
type DetalleVentaRead = components['schemas']['DetalleVentaRead']
type ProductoRead = components['schemas']['ProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']
type ClienteRead = components['schemas']['ClienteRead']

const producto = (id: number, nombre: string): ProductoRead => ({
  id,
  tipo_producto_id: 1,
  nombre,
  requiere_fabricacion: true,
  costos_operativos_fijos: '0',
  precio_venta_sugerido: '5000',
})

const variante = (id: number, producto_id: number, nombre_variante: string): VarianteProductoRead => ({
  id,
  producto_id,
  nombre_variante,
  precio_venta: null,
})

const cliente = (id: number, nombre: string): ClienteRead => ({
  id,
  nombre,
  documento_identidad: null,
  email: null,
  telefono: null,
  created_at: '2026-01-01T00:00:00Z',
})

const detalle = (producto_id: number, variante_id: number | null = null): DetalleVentaRead => ({
  id: producto_id,
  producto_id,
  variante_id,
  cantidad: '2',
  precio_unitario_aplicado: '5000.00',
  costo_unitario_aplicado: '2000.00',
})

const venta = (overrides: Partial<VentaRead> = {}): VentaRead => ({
  id: 1,
  fecha: '2026-08-01T10:30:00Z',
  cliente_id: null,
  canal_venta: 'web',
  descuento_porcentaje: '0',
  estado: 'completada',
  es_regalo: false,
  total_venta: '10000.00',
  detalles: [],
  ...overrides,
})

const detalleRow = (overrides: Partial<VentasFormDetalle> = {}): VentasFormDetalle => ({
  producto_id: 1,
  variante_id: null,
  cantidad: 2,
  precio_unitario: 5000,
  ...overrides,
})

describe('sliceVentas (MOD-1 client-side limit, unbounded backend)', () => {
  it('keeps only the most recent `limit` ventas, newest first', () => {
    const ventas = [venta({ id: 1 }), venta({ id: 2 }), venta({ id: 3 }), venta({ id: 4 })]

    const sliced = sliceVentas(ventas, 2)

    expect(sliced.map((v) => v.id)).toEqual([4, 3])
  })

  it('returns everything (newest first) when the list fits the limit', () => {
    const ventas = [venta({ id: 1 }), venta({ id: 2 })]

    const sliced = sliceVentas(ventas, 100)

    expect(sliced.map((v) => v.id)).toEqual([2, 1])
  })

  it('returns an empty list for an empty response', () => {
    expect(sliceVentas([])).toEqual([])
  })
})

describe('buildVentaRows (MOD-1 client-side joins)', () => {
  const PRODUCTOS = [producto(1, 'Arepa de huevo'), producto(2, 'Jugo de naranja')]
  const VARIANTES = [variante(5, 1, 'Grande')]
  const CLIENTES = [cliente(7, 'Juan Pérez')]

  it('joins product names, variant labels, cliente names and detail counts', () => {
    const ventas = [
      venta({
        id: 10,
        cliente_id: 7,
        canal_venta: 'whatsapp',
        estado: 'completada',
        total_venta: '15000.00',
        detalles: [detalle(1, 5), detalle(2)],
      }),
    ]

    const rows = buildVentaRows(ventas, PRODUCTOS, VARIANTES, CLIENTES)

    expect(rows).toHaveLength(1)
    const row = rows[0]
    expect(row).toMatchObject({
      id: 10,
      cliente: 'Juan Pérez',
      canal_venta: 'whatsapp',
      estado: 'completada',
      total_venta: '15000.00',
      detalle_count: 2,
    })
    expect(row.detalles[0]).toMatchObject({ nombre: 'Arepa de huevo', variante: 'Grande' })
    expect(row.detalles[1]).toMatchObject({ nombre: 'Jugo de naranja', variante: '(base)' })
  })

  it('degrades missing joins: Producto #{id}, Variante #{id} and an em dash cliente', () => {
    const ventas = [
      venta({
        id: 11,
        cliente_id: null,
        detalles: [detalle(99, 77)],
      }),
    ]

    const rows = buildVentaRows(ventas, PRODUCTOS, VARIANTES, CLIENTES)

    expect(rows[0].cliente).toBe('—')
    expect(rows[0].detalles[0]).toMatchObject({
      nombre: 'Producto #99',
      variante: 'Variante #77',
    })
  })

  it('returns an empty list when there are no ventas', () => {
    expect(buildVentaRows([], PRODUCTOS, VARIANTES, CLIENTES)).toEqual([])
  })
})

describe('canalLabel / estadoLabel (MOD-1 display labels)', () => {
  it('maps known channels and estados to es-CO labels', () => {
    expect(canalLabel('web')).toBe('Web')
    expect(canalLabel('whatsapp')).toBe('WhatsApp')
    expect(canalLabel('instagram')).toBe('Instagram')
    expect(canalLabel('feria')).toBe('Feria')
    expect(estadoLabel('completada')).toBe('Completada')
    expect(estadoLabel('anulada')).toBe('Anulada')
  })

  it('passes unknown values through untouched', () => {
    expect(canalLabel('otro')).toBe('otro')
    expect(estadoLabel('pendiente')).toBe('pendiente')
  })
})

describe('createDetalleRow (MOD-1 dynamic line items)', () => {
  it('returns a fresh empty row with sensible defaults', () => {
    const row = createDetalleRow()

    expect(row).toEqual({ producto_id: null, variante_id: null, cantidad: 1, precio_unitario: 0 })
    // Two calls must NOT share a mutable reference (each row edits independently).
    expect(createDetalleRow()).not.toBe(row)
  })
})

describe('ventaSubtotal (MOD-1 total preview)', () => {
  it('sums cantidad * precio_unitario parsing Decimal-as-string prices', () => {
    const detalles = [
      detalleRow({ cantidad: 2, precio_unitario: 5000 }),
      detalleRow({ cantidad: 1, precio_unitario: 8000.5 }),
    ]

    expect(ventaSubtotal(detalles)).toBe(18000.5)
  })

  it('treats an unparseable price as zero contribution', () => {
    // NaN is what an empty el-input-number yields; parseDecimal rejects it.
    const detalles = [detalleRow({ cantidad: 3, precio_unitario: Number.NaN })]

    expect(ventaSubtotal(detalles)).toBe(0)
  })

  it('returns zero for empty detalles', () => {
    expect(ventaSubtotal([])).toBe(0)
  })
})

describe('computeTotalPreview (MOD-1 server-matching total)', () => {
  it('applies the percentage discount: subtotal * (1 - descuento/100)', () => {
    const detalles = [detalleRow({ cantidad: 2, precio_unitario: 5000 })]

    expect(computeTotalPreview(detalles, 10)).toBe(9000)
  })

  it('clamps descuento outside [0,100] to the bounds', () => {
    const detalles = [detalleRow({ cantidad: 2, precio_unitario: 5000 })]
    // subtotal 10000: negative -> no discount, >100 -> zero total.
    expect(computeTotalPreview(detalles, -5)).toBe(10000)
    expect(computeTotalPreview(detalles, 120)).toBe(0)
  })

  it('rounds to 2 decimals (same precision as the backend Decimal)', () => {
    const detalles = [detalleRow({ cantidad: 1, precio_unitario: 100 })]
    // 100 * (1 - 33.333/100) = 66.667 -> 66.67
    expect(computeTotalPreview(detalles, 33.333)).toBe(66.67)
  })

  it('returns zero when there are no detalles', () => {
    expect(computeTotalPreview([], 0)).toBe(0)
  })
})

describe('hasValidDetalles (MOD-1 min 1 detalle, cantidad > 0)', () => {
  it('rejects empty detalles', () => {
    expect(hasValidDetalles([])).toBe(false)
  })

  it('rejects rows without a product or with a zero/negative cantidad', () => {
    expect(hasValidDetalles([detalleRow({ producto_id: null })])).toBe(false)
    expect(hasValidDetalles([detalleRow({ cantidad: 0 })])).toBe(false)
    expect(hasValidDetalles([detalleRow({ cantidad: -1 })])).toBe(false)
  })

  it('accepts at least one complete row', () => {
    expect(hasValidDetalles([detalleRow({ producto_id: null }), detalleRow()])).toBe(true)
  })
})

describe('buildVentaPayload (MOD-1 POST /ventas body)', () => {
  it('builds the exact VentaCreate shape with cliente, canal, descuento and detalles', () => {
    const form = {
      cliente_id: 7,
      canal_venta: 'whatsapp' as const,
      descuento_porcentaje: 5,
      es_regalo: false,
      detalles: [
        detalleRow({ producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 }),
        detalleRow({ producto_id: 2, variante_id: null, cantidad: 1, precio_unitario: 8000 }),
      ],
    }

    const payload = buildVentaPayload(form)

    expect(payload).toEqual({
      cliente_id: 7,
      canal_venta: 'whatsapp',
      descuento_porcentaje: 5,
      es_regalo: false,
      detalles: [
        { producto_id: 1, variante_id: 5, cantidad: 2, precio_unitario: 5000 },
        { producto_id: 2, cantidad: 1, precio_unitario: 8000 },
      ],
    })
    // Variante id must be absent (not null) when the row has no variante.
    expect(payload.detalles[1]).not.toHaveProperty('variante_id')
  })

  it('omits cliente_id and drops incomplete rows', () => {
    const form = {
      cliente_id: null,
      canal_venta: 'feria' as const,
      descuento_porcentaje: 0,
      es_regalo: false,
      detalles: [
        detalleRow({ producto_id: null, cantidad: 1, precio_unitario: 5000 }),
        detalleRow({ producto_id: 3, cantidad: 2, precio_unitario: 6000 }),
      ],
    }

    const payload = buildVentaPayload(form)

    expect(payload).not.toHaveProperty('cliente_id')
    expect(payload.detalles).toEqual([{ producto_id: 3, cantidad: 2, precio_unitario: 6000 }])
  })

  it('serializes cantidad and precio_unitario as numbers (server Decimal accepts both)', () => {
    const form = {
      cliente_id: null,
      canal_venta: 'web' as const,
      descuento_porcentaje: 0,
      es_regalo: false,
      detalles: [detalleRow({ producto_id: 1, cantidad: 2, precio_unitario: 5000 })],
    }

    const payload = buildVentaPayload(form)

    expect(typeof payload.detalles[0].cantidad).toBe('number')
    expect(typeof payload.detalles[0].precio_unitario).toBe('number')
    expect(typeof payload.descuento_porcentaje).toBe('number')
  })
})
