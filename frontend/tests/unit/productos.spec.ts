/**
 * Productos module mapper tests (PR10, spec MOD-5).
 *
 * Pure functions in src/utils/productos.ts:
 *  - `buildTiposProductoById` + `tipoProductoNombre`: ProductoRead rows carry
 *    only tipo_producto_id — the display name is joined client-side against
 *    GET /tipos-producto with a `Tipo #id` fallback when the tipo is gone.
 *  - `buildProductoRows`: the productos list rows (id, tipo label, nombre,
 *    requiere_fabricacion bool, the two Decimal-as-string money fields).
 *  - `buildProductoPayload` / `buildProductoUpdatePayload`: create/edit form
 *    -> ProductoCreate / ProductoUpdate bodies (PUT sends the full field set;
 *    the backend update schema marks every field optional).
 *  - `buildVariantePayload` / `buildVarianteUpdatePayload`: nested variante
 *    form -> VarianteProductoCreate / VarianteProductoUpdate. The backend
 *    VarianteProductoRead has NO costo_adicional — only nombre_variante +
 *    precio_venta (verified prod OpenAPI + backend routes/productos.py).
 *  - `buildBomInsumoRows`: BOM insumo lines join insumo name AND
 *    unidad_medida (BomInsumoRead has neither — only insumo_id).
 *  - `buildBomInsumoPayload` / `buildBomInsumoUpdatePayload`: BOM insumo form
 *    -> BomInsumoCreate / BomInsumoUpdate (cantidad_requerida +
 *    porcentaje_desperdicio; variante_id omitted when null).
 *  - `buildBomProductoRows` / `buildBomProductoPayload` /
 *    `buildBomProductoUpdatePayload`: combo contents join product name; the
 *    schema has NO desperdicio field on BomProducto — only cantidad.
 *  - `buildCostoTree` + `COSTO_TIPO_LABELS`: CostoProduccionRead
 *    {total, lineas[{tipo, ...}]} -> grouped tree (one group per tipo present,
 *    insumo -> producto -> operativos_fijos order, subtotal per group) plus
 *    the grand total passthrough.
 */
import { describe, expect, it } from 'vitest'

import {
  COSTO_TIPO_LABELS,
  buildBomInsumoPayload,
  buildBomInsumoRows,
  buildBomInsumoUpdatePayload,
  buildBomProductoPayload,
  buildBomProductoRows,
  buildBomProductoUpdatePayload,
  buildCostoTree,
  buildProductoPayload,
  buildProductoRows,
  buildProductoUpdatePayload,
  buildTiposProductoById,
  buildVariantePayload,
  buildVarianteUpdatePayload,
  tipoProductoNombre,
} from '@/utils/productos'
import type { components } from '@/types/api.d'

type ProductoRead = components['schemas']['ProductoRead']
type TipoProductoRead = components['schemas']['TipoProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']
type BomInsumoRead = components['schemas']['BomInsumoRead']
type BomProductoRead = components['schemas']['BomProductoRead']
type InsumoRead = components['schemas']['InsumoRead']
type CostoProduccionRead = components['schemas']['CostoProduccionRead']

const TIPOS: TipoProductoRead[] = [
  { id: 1, nombre: 'Alimentos' },
  { id: 2, nombre: 'Aseo' },
]

const PRODUCTOS: ProductoRead[] = [
  {
    id: 1,
    tipo_producto_id: 1,
    nombre: 'Arepa de choclo',
    requiere_fabricacion: true,
    costos_operativos_fijos: '5000.00',
    precio_venta_sugerido: '12000.00',
  },
  {
    id: 2,
    tipo_producto_id: 99, // tipo no longer exists
    nombre: 'Detergente',
    requiere_fabricacion: false,
    costos_operativos_fijos: '0.00',
    precio_venta_sugerido: '8000.00',
  },
]

const VARIANTES: VarianteProductoRead[] = [
  { id: 1, producto_id: 1, nombre_variante: 'Individual', precio_venta: '13000.00' },
  { id: 2, producto_id: 1, nombre_variante: 'Docena', precio_venta: null },
]

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
]

const BOM_INSUMOS: BomInsumoRead[] = [
  {
    id: 1,
    producto_id: 1,
    insumo_id: 1,
    variante_id: null,
    cantidad_requerida: '2.00',
    porcentaje_desperdicio: '5.00',
  },
  {
    id: 2,
    producto_id: 1,
    insumo_id: 99, // insumo no longer exists
    variante_id: 2,
    cantidad_requerida: '1.50',
    porcentaje_desperdicio: '0.00',
  },
]

const BOM_PRODUCTOS: BomProductoRead[] = [
  { id: 1, combo_id: 1, producto_incluido_id: 1, cantidad: '2.00' },
  { id: 2, combo_id: 1, producto_incluido_id: 88, cantidad: '3.00' }, // producto gone
]

const COSTO: CostoProduccionRead = {
  total: '15200.00',
  lineas: [
    { tipo: 'insumo', id: 1, nombre: 'Harina de maíz', cantidad: '2.10', costo_unitario: '2500.00', costo_total: '5250.00' },
    { tipo: 'operativos_fijos', id: 1, nombre: 'Arepa de choclo', cantidad: '1.00', costo_unitario: '5000.00', costo_total: '5000.00' },
    { tipo: 'producto', id: 2, nombre: 'Queso', cantidad: '1.00', costo_unitario: '4950.00', costo_total: '4950.00' },
  ],
}

describe('productos mappers (MOD-5)', () => {
  it('buildTiposProductoById indexes tipos by id for O(1) joins', () => {
    const byId = buildTiposProductoById(TIPOS)
    expect(byId.size).toBe(2)
    expect(byId.get(1)?.nombre).toBe('Alimentos')
    expect(byId.get(99)).toBeUndefined()
  })

  it('tipoProductoNombre returns the joined name, falling back to Tipo #{id}', () => {
    const byId = buildTiposProductoById(TIPOS)
    expect(tipoProductoNombre(byId, 1)).toBe('Alimentos')
    expect(tipoProductoNombre(byId, 99)).toBe('Tipo #99')
  })

  it('buildProductoRows joins the tipo label and keeps raw Decimal fields', () => {
    const rows = buildProductoRows(PRODUCTOS, TIPOS)

    expect(rows).toHaveLength(2)
    expect(rows[0]).toEqual({
      id: 1,
      tipo: 'Alimentos',
      nombre: 'Arepa de choclo',
      requiere_fabricacion: true,
      costos_operativos_fijos: '5000.00',
      precio_venta_sugerido: '12000.00',
    })
    expect(rows[1].tipo).toBe('Tipo #99') // missing tipo -> graceful fallback
  })

  it('buildProductoPayload maps the create form to ProductoCreate with trimmed nombre', () => {
    expect(
      buildProductoPayload({
        tipo_producto_id: 1,
        nombre: '  Arepa de choclo  ',
        requiere_fabricacion: true,
        costos_operativos_fijos: 5000,
        precio_venta_sugerido: 12000,
      }),
    ).toEqual({
      tipo_producto_id: 1,
      nombre: 'Arepa de choclo',
      requiere_fabricacion: true,
      costos_operativos_fijos: 5000,
      precio_venta_sugerido: 12000,
    })
  })

  it('buildProductoUpdatePayload sends the full editable field set for PUT /productos', () => {
    expect(
      buildProductoUpdatePayload({
        tipo_producto_id: 2,
        nombre: 'Detergente',
        requiere_fabricacion: false,
        costos_operativos_fijos: 0,
        precio_venta_sugerido: 8000,
      }),
    ).toEqual({
      tipo_producto_id: 2,
      nombre: 'Detergente',
      requiere_fabricacion: false,
      costos_operativos_fijos: 0,
      precio_venta_sugerido: 8000,
    })
  })

  it('buildVariantePayload omits precio_venta when null and keeps it when set', () => {
    expect(buildVariantePayload({ nombre_variante: 'Docena', precio_venta: null })).toEqual({
      nombre_variante: 'Docena',
    })
    expect(buildVariantePayload({ nombre_variante: 'Individual', precio_venta: 13000 })).toEqual({
      nombre_variante: 'Individual',
      precio_venta: 13000,
    })
  })

  it('buildVarianteUpdatePayload trims the name and omits a cleared precio_venta', () => {
    expect(
      buildVarianteUpdatePayload({ nombre_variante: '  Docena  ', precio_venta: null }),
    ).toEqual({ nombre_variante: 'Docena' })
    expect(
      buildVarianteUpdatePayload({ nombre_variante: 'Docena', precio_venta: 13500 }),
    ).toEqual({ nombre_variante: 'Docena', precio_venta: 13500 })
  })

  it('buildBomInsumoRows joins insumo name and unidad_medida, falling back gracefully', () => {
    const rows = buildBomInsumoRows(BOM_INSUMOS, INSUMOS)

    expect(rows).toHaveLength(2)
    expect(rows[0]).toEqual({
      id: 1,
      insumo: 'Harina de maíz',
      unidad_medida: 'kg',
      cantidad_requerida: '2.00',
      porcentaje_desperdicio: '5.00',
    })
    expect(rows[1]).toEqual({
      id: 2,
      insumo: 'Insumo #99',
      unidad_medida: '—',
      cantidad_requerida: '1.50',
      porcentaje_desperdicio: '0.00',
    })
  })

  it('buildBomInsumoPayload maps to BomInsumoCreate, omitting variante_id when null', () => {
    expect(
      buildBomInsumoPayload({
        insumo_id: 1,
        variante_id: null,
        cantidad_requerida: 2,
        porcentaje_desperdicio: 5,
      }),
    ).toEqual({
      insumo_id: 1,
      cantidad_requerida: 2,
      porcentaje_desperdicio: 5,
    })
    expect(
      buildBomInsumoPayload({
        insumo_id: 1,
        variante_id: 2,
        cantidad_requerida: 1.5,
        porcentaje_desperdicio: 0,
      }),
    ).toEqual({
      insumo_id: 1,
      variante_id: 2,
      cantidad_requerida: 1.5,
      porcentaje_desperdicio: 0,
    })
  })

  it('buildBomInsumoUpdatePayload sends the full editable field set for PUT', () => {
    expect(
      buildBomInsumoUpdatePayload({
        insumo_id: 2,
        variante_id: 2,
        cantidad_requerida: 2.5,
        porcentaje_desperdicio: 10,
      }),
    ).toEqual({
      insumo_id: 2,
      variante_id: 2,
      cantidad_requerida: 2.5,
      porcentaje_desperdicio: 10,
    })
  })

  it('buildBomProductoRows joins the included product name, falling back to Producto #{id}', () => {
    const rows = buildBomProductoRows(BOM_PRODUCTOS, PRODUCTOS)

    expect(rows).toHaveLength(2)
    expect(rows[0]).toEqual({ id: 1, producto: 'Arepa de choclo', cantidad: '2.00' })
    expect(rows[1]).toEqual({ id: 2, producto: 'Producto #88', cantidad: '3.00' })
  })

  it('buildBomProductoPayload maps to BomProductoCreate', () => {
    expect(buildBomProductoPayload({ producto_incluido_id: 2, cantidad: 3 })).toEqual({
      producto_incluido_id: 2,
      cantidad: 3,
    })
  })

  it('buildBomProductoUpdatePayload sends the full editable field set for PUT', () => {
    expect(buildBomProductoUpdatePayload({ producto_incluido_id: 3, cantidad: 4 })).toEqual({
      producto_incluido_id: 3,
      cantidad: 4,
    })
  })

  it('COSTO_TIPO_LABELS provides es-CO labels for every line tipo', () => {
    expect(COSTO_TIPO_LABELS).toEqual({
      insumo: 'Insumos',
      producto: 'Productos',
      operativos_fijos: 'Costos operativos fijos',
    })
  })

  it('buildCostoTree groups lineas by tipo (insumo -> producto -> operativos_fijos) with subtotals', () => {
    const tree = buildCostoTree(COSTO)

    expect(tree.total).toBe('15200.00')
    expect(tree.groups.map((g) => g.tipo)).toEqual(['insumo', 'producto', 'operativos_fijos'])
    expect(tree.groups[0].label).toBe('Insumos')
    expect(tree.groups[0].subtotal).toBe(5250)
    expect(tree.groups[1].subtotal).toBe(4950)
    expect(tree.groups[2].subtotal).toBe(5000)
    expect(tree.groups[0].lineas).toHaveLength(1)
    expect(tree.groups[0].lineas[0].nombre).toBe('Harina de maíz')
  })

  it('buildCostoTree skips tipos with no lineas and handles an empty breakdown', () => {
    const partial: CostoProduccionRead = { total: '5000.00', lineas: COSTO.lineas.slice(1) }
    const tree = buildCostoTree(partial)
    expect(tree.groups.map((g) => g.tipo)).toEqual(['producto', 'operativos_fijos'])

    const empty = buildCostoTree({ total: '0.00', lineas: [] })
    expect(empty.groups).toEqual([])
    expect(empty.total).toBe('0.00')
  })
})
