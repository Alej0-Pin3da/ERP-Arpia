/**
 * Inventario module mapper tests (PR9, spec MOD-4).
 *
 * Pure functions in src/utils/inventario.ts:
 *  - `buildInsumosById` + `insumoNombre`: CompraInsumoRead rows carry only
 *    insumo_id — the name is joined client-side (GET /insumos) with an
 *    `Insumo #{id}` fallback when the insumo is gone.
 *  - `compraCostoTotal` + `buildCompraRows`: the backend CompraInsumoRead has
 *    NO costo_total field (verified against prod OpenAPI + backend routes), so
 *    the total is computed client-side as cantidad_comprada x
 *    precio_unitario_compra on the Decimal-as-string values; unparseable
 *    values degrade to null. Rows render newest first (backend lists id ASC).
 *  - `buildCompraPayload`: compra form -> CompraInsumoCreate body. The schema
 *    field names are `cantidad_comprada` / `precio_unitario_compra` (NOT
 *    cantidad/precio_unitario).
 *  - `buildInsumoPayload` / `buildInsumoUpdatePayload`: admin insumo master
 *    form -> InsumoCreate / InsumoUpdate bodies (PUT sends the full field set;
 *    the backend schema marks every update field optional).
 *  - `buildComprasListParams`: optional GET /compras-insumos?insumo_id filter
 *    — omitted from the query when unset.
 */
import { describe, expect, it } from 'vitest'

import {
  buildComprasListParams,
  buildCompraPayload,
  buildCompraRows,
  buildInsumosById,
  buildInsumoPayload,
  buildInsumoUpdatePayload,
  compraCostoTotal,
  insumoNombre,
} from '@/utils/inventario'
import type { components } from '@/types/api.d'

type InsumoRead = components['schemas']['InsumoRead']
type CompraInsumoRead = components['schemas']['CompraInsumoRead']

const INSUMOS: InsumoRead[] = [
  {
    id: 2,
    categoria_id: 1,
    nombre: 'Harina de maíz',
    unidad_medida: 'kg',
    stock_actual: '12.00',
    stock_minimo: '5.00',
    costo_promedio_actual: '2500.00',
    nombre_categoria: 'Granos',
  },
  {
    id: 3,
    categoria_id: 2,
    nombre: 'Aceite',
    unidad_medida: 'L',
    stock_actual: '8.00',
    stock_minimo: '3.00',
    costo_promedio_actual: '9800.00',
    nombre_categoria: 'Abarrotes',
  },
]

const COMPRAS: CompraInsumoRead[] = [
  {
    id: 1,
    insumo_id: 2,
    proveedor_id: null,
    fecha_compra: '2026-08-01T09:00:00Z',
    cantidad_comprada: '3.00',
    precio_unitario_compra: '2500.00',
  },
  {
    id: 2,
    insumo_id: 99, // no longer in the insumos catalog
    proveedor_id: null,
    fecha_compra: '2026-08-03T10:30:00Z',
    cantidad_comprada: '2.50',
    precio_unitario_compra: '1200.00',
  },
]

describe('inventario mappers (MOD-4)', () => {
  it('buildInsumosById indexes insumos by id for O(1) joins', () => {
    const byId = buildInsumosById(INSUMOS)
    expect(byId.size).toBe(2)
    expect(byId.get(2)?.nombre).toBe('Harina de maíz')
    expect(byId.get(99)).toBeUndefined()
  })

  it('insumoNombre returns the joined name, falling back to Insumo #{id}', () => {
    const byId = buildInsumosById(INSUMOS)
    expect(insumoNombre(byId, 2)).toBe('Harina de maíz')
    expect(insumoNombre(byId, 99)).toBe('Insumo #99')
  })

  it('compraCostoTotal multiplies Decimal-as-string quantity by unit price', () => {
    expect(compraCostoTotal('3.00', '2500.00')).toBe(7500)
    expect(compraCostoTotal('2.5', '1200.50')).toBe(3001.25)
  })

  it('compraCostoTotal degrades to null when either value is unparseable', () => {
    expect(compraCostoTotal('abc', '2500.00')).toBeNull()
    expect(compraCostoTotal('3.00', 'xyz')).toBeNull()
  })

  it('buildCompraRows joins insumo names, computes costo_total and sorts newest first', () => {
    const rows = buildCompraRows(COMPRAS, INSUMOS)

    expect(rows).toHaveLength(2)
    expect(rows[0]).toEqual({
      id: 2,
      fecha: '2026-08-03T10:30:00Z',
      insumo: 'Insumo #99', // missing insumo -> graceful fallback
      cantidad: '2.50',
      precio_unitario: '1200.00',
      costo_total: 3000,
    })
    expect(rows[1]).toEqual({
      id: 1,
      fecha: '2026-08-01T09:00:00Z',
      insumo: 'Harina de maíz',
      cantidad: '3.00',
      precio_unitario: '2500.00',
      costo_total: 7500,
    })
  })

  it('buildCompraPayload maps the form to CompraInsumoCreate (cantidad_comprada / precio_unitario_compra)', () => {
    expect(
      buildCompraPayload({ insumo_id: 3, cantidad: 2.5, precio_unitario: 4500 }),
    ).toEqual({
      insumo_id: 3,
      cantidad_comprada: 2.5,
      precio_unitario_compra: 4500,
    })
  })

  it('buildInsumoPayload maps the admin create form to InsumoCreate with trimmed text', () => {
    expect(
      buildInsumoPayload({
        nombre: '  Harina de maíz  ',
        categoria_id: 1,
        unidad_medida: ' kg ',
        stock_actual: 10,
        stock_minimo: 5,
        costo_promedio_actual: 3200,
      }),
    ).toEqual({
      categoria_id: 1,
      nombre: 'Harina de maíz',
      unidad_medida: 'kg',
      stock_actual: 10,
      stock_minimo: 5,
      costo_promedio_actual: 3200,
    })
  })

  it('buildInsumoUpdatePayload sends the full editable field set for PUT /insumos', () => {
    expect(
      buildInsumoUpdatePayload({
        nombre: 'Aceite',
        categoria_id: 2,
        unidad_medida: 'L',
        stock_actual: 8,
        stock_minimo: 3,
        costo_promedio_actual: 9800,
      }),
    ).toEqual({
      categoria_id: 2,
      nombre: 'Aceite',
      unidad_medida: 'L',
      stock_actual: 8,
      stock_minimo: 3,
      costo_promedio_actual: 9800,
    })
  })

  it('buildComprasListParams omits the insumo_id filter when unset', () => {
    expect(buildComprasListParams({ insumo_id: null })).toEqual({})
    expect(buildComprasListParams({ insumo_id: 5 })).toEqual({ insumo_id: 5 })
  })
})
