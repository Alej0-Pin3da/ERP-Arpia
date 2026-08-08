/**
 * Productos module mappers (PR10, spec MOD-5).
 *
 * Pure functions over the productos module:
 *  - `buildTiposProductoById` + `tipoProductoNombre`: ProductoRead rows carry
 *    only tipo_producto_id — the display name is joined client-side against
 *    GET /tipos-producto with a `Tipo #{id}` fallback when the tipo is gone
 *    (design "Missing joins MUST degrade").
 *  - `buildProductoRows`: the productos list rows — the tipo label join plus
 *    the raw Decimal-as-string money fields (formatted at render time).
 *  - `buildProductoPayload` / `buildProductoUpdatePayload`: create/edit form
 *    -> ProductoCreate / ProductoUpdate bodies. The PUT schema marks every
 *    field optional but accepts the full editable set (same pattern as
 *    inventario's InsumoUpdate).
 *  - `buildVariantePayload` / `buildVarianteUpdatePayload`: nested variante
 *    form -> VarianteProductoCreate / VarianteProductoUpdate. NOTE: the
 *    backend VarianteProductoRead has NO `costo_adicional` — only
 *    nombre_variante + precio_venta (verified prod OpenAPI + backend
 *    routes/productos.py + schemas/producto.py), so the form maps those two.
 *  - `buildBomInsumoRows`: BOM insumo lines join insumo name AND
 *    unidad_medida (BomInsumoRead carries only insumo_id).
 *  - `buildBomInsumoPayload` / `buildBomInsumoUpdatePayload`: BOM insumo form
 *    -> BomInsumoCreate / BomInsumoUpdate. Schema names: cantidad_requerida +
 *    porcentaje_desperdicio; variante_id is OPTIONAL and omitted when null
 *    (the base rule row for all variants).
 *  - `buildBomProductoRows` / `buildBomProductoPayload` /
 *    `buildBomProductoUpdatePayload`: combo contents join the included product
 *    name. NOTE: the schema has NO desperdicio field on BomProducto — only
 *    producto_incluido_id + cantidad (verified backend schemas/bom.py).
 *  - `buildCostoTree` + `COSTO_TIPO_LABELS`: CostoProduccionRead
 *    {total, lineas[{tipo, id, nombre, cantidad, costo_unitario,
 *    costo_total}]} -> a tree grouped by tipo (insumo -> producto ->
 *    operativos_fijos order, subtotal per group) plus the grand total.
 */
import type { components } from '@/types/api.d'
import { parseDecimal } from './format'

type ProductoRead = components['schemas']['ProductoRead']
type TipoProductoRead = components['schemas']['TipoProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']
type VarianteProductoCreate = components['schemas']['VarianteProductoCreate']
type VarianteProductoUpdate = components['schemas']['VarianteProductoUpdate']
type BomInsumoRead = components['schemas']['BomInsumoRead']
type BomInsumoCreate = components['schemas']['BomInsumoCreate']
type BomInsumoUpdate = components['schemas']['BomInsumoUpdate']
type BomProductoRead = components['schemas']['BomProductoRead']
type BomProductoCreate = components['schemas']['BomProductoCreate']
type BomProductoUpdate = components['schemas']['BomProductoUpdate']
type InsumoRead = components['schemas']['InsumoRead']
type CostoProduccionRead = components['schemas']['CostoProduccionRead']
type CostoLineaRead = components['schemas']['CostoLineaRead']
export type ProductoCreate = components['schemas']['ProductoCreate']
export type ProductoUpdate = components['schemas']['ProductoUpdate']

/** Map of tipo id -> TipoProductoRead for O(1) client-side joins. */
export function buildTiposProductoById(tipos: TipoProductoRead[]): Map<number, TipoProductoRead> {
  return new Map(tipos.map((t) => [t.id, t]))
}

/**
 * Tipo display name for a product join. Degrades gracefully when the tipo no
 * longer exists: `Tipo #{id}`.
 */
export function tipoProductoNombre(
  tiposById: Map<number, TipoProductoRead>,
  tipoProductoId: number,
): string {
  return tiposById.get(tipoProductoId)?.nombre ?? `Tipo #${tipoProductoId}`
}

/** A productos list row with its joined tipo label (MOD-5). */
export interface ProductoRow {
  id: number
  /** Tipo name, or `Tipo #{id}` when the tipo is gone. */
  tipo: string
  nombre: string
  requiere_fabricacion: boolean
  /** Raw Decimal-as-string money fields (formatted at render time). */
  costos_operativos_fijos: string
  precio_venta_sugerido: string
}

/** MOD-5: join productos with their tipo labels for the list table. */
export function buildProductoRows(
  productos: ProductoRead[],
  tipos: TipoProductoRead[],
): ProductoRow[] {
  const tiposById = buildTiposProductoById(tipos)

  return productos.map((p) => ({
    id: p.id,
    tipo: tipoProductoNombre(tiposById, p.tipo_producto_id),
    nombre: p.nombre,
    requiere_fabricacion: p.requiere_fabricacion,
    costos_operativos_fijos: p.costos_operativos_fijos,
    precio_venta_sugerido: p.precio_venta_sugerido,
  }))
}

/** The productos create/edit form model (maps to ProductoCreate). */
export interface ProductoPayloadInput {
  tipo_producto_id: number | null
  nombre: string
  requiere_fabricacion: boolean
  /** >= 0 (el-input-number value). */
  costos_operativos_fijos: number | null
  /** >= 0 (el-input-number value). */
  precio_venta_sugerido: number | null
}

/** MOD-5: create form -> ProductoCreate POST body. */
export function buildProductoPayload(form: ProductoPayloadInput): ProductoCreate {
  return {
    tipo_producto_id: form.tipo_producto_id as number,
    nombre: form.nombre.trim(),
    requiere_fabricacion: form.requiere_fabricacion,
    costos_operativos_fijos: form.costos_operativos_fijos as number,
    precio_venta_sugerido: form.precio_venta_sugerido as number,
  }
}

/** MOD-5: edit form -> ProductoUpdate PUT body (full editable set). */
export function buildProductoUpdatePayload(form: ProductoPayloadInput): ProductoUpdate {
  return buildProductoPayload(form)
}

/** The nested variante form model (maps to VarianteProductoCreate). */
export interface VariantePayloadInput {
  nombre_variante: string
  /** Optional; omitted from the body when null. */
  precio_venta: number | null
}

/** MOD-5: variante form -> VarianteProductoCreate body (precio_venta omitted
 *  when null — the schema default). */
export function buildVariantePayload(form: VariantePayloadInput): VarianteProductoCreate {
  const body: VarianteProductoCreate = { nombre_variante: form.nombre_variante.trim() }
  if (form.precio_venta !== null) body.precio_venta = form.precio_venta
  return body
}

/** MOD-5: variante edit -> VarianteProductoUpdate body. */
export function buildVarianteUpdatePayload(form: VariantePayloadInput): VarianteProductoUpdate {
  return buildVariantePayload(form)
}

/** A BOM insumo line row with its joined insumo name + unidad (MOD-5). */
export interface BomInsumoRow {
  id: number
  /** Insumo name, or `Insumo #{id}` when the insumo is gone. */
  insumo: string
  /** Insumo unidad_medida, or '—' when the insumo is gone. */
  unidad_medida: string
  /** Raw Decimal-as-string fields (formatted at render time). */
  cantidad_requerida: string
  porcentaje_desperdicio: string
}

/**
 * MOD-5: join BOM insumo lines with insumo names AND unidades (BomInsumoRead
 * carries only insumo_id — the name and unidad come from GET /insumos).
 */
export function buildBomInsumoRows(
  lineas: BomInsumoRead[],
  insumos: InsumoRead[],
): BomInsumoRow[] {
  const insumosById = new Map(insumos.map((i) => [i.id, i]))

  return lineas.map((l) => {
    const insumo = insumosById.get(l.insumo_id)
    return {
      id: l.id,
      insumo: insumo?.nombre ?? `Insumo #${l.insumo_id}`,
      unidad_medida: insumo?.unidad_medida ?? '—',
      cantidad_requerida: l.cantidad_requerida,
      porcentaje_desperdicio: l.porcentaje_desperdicio,
    }
  })
}

/** The BOM insumo line form model (maps to BomInsumoCreate). */
export interface BomInsumoPayloadInput {
  insumo_id: number | null
  /** Optional per-variant override; omitted from the body when null. */
  variante_id: number | null
  /** > 0 (el-input-number value). */
  cantidad_requerida: number | null
  /** 0..100 (el-input-number value). */
  porcentaje_desperdicio: number | null
}

/** MOD-5: BOM insumo form -> BomInsumoCreate body (variante_id omitted when
 *  null — the base rule row applies to all variants). */
export function buildBomInsumoPayload(form: BomInsumoPayloadInput): BomInsumoCreate {
  const body: BomInsumoCreate = {
    insumo_id: form.insumo_id as number,
    cantidad_requerida: form.cantidad_requerida as number,
    porcentaje_desperdicio: form.porcentaje_desperdicio as number,
  }
  if (form.variante_id !== null) body.variante_id = form.variante_id
  return body
}

/** MOD-5: BOM insumo edit -> BomInsumoUpdate PUT body (full editable set). */
export function buildBomInsumoUpdatePayload(form: BomInsumoPayloadInput): BomInsumoUpdate {
  return buildBomInsumoPayload(form)
}

/** A combo-content row with its joined product name (MOD-5). */
export interface BomProductoRow {
  id: number
  /** Included product name, or `Producto #{id}` when the product is gone. */
  producto: string
  /** Raw Decimal-as-string quantity (formatted at render time). */
  cantidad: string
}

/** MOD-5: join combo contents with the included product names. NOTE: the
 *  BomProducto schema has NO desperdicio field — only cantidad. */
export function buildBomProductoRows(
  lineas: BomProductoRead[],
  productos: ProductoRead[],
): BomProductoRow[] {
  const productosById = new Map(productos.map((p) => [p.id, p]))

  return lineas.map((l) => ({
    id: l.id,
    producto: productosById.get(l.producto_incluido_id)?.nombre ?? `Producto #${l.producto_incluido_id}`,
    cantidad: l.cantidad,
  }))
}

/** The combo-content form model (maps to BomProductoCreate). */
export interface BomProductoPayloadInput {
  producto_incluido_id: number | null
  /** > 0 (el-input-number value). */
  cantidad: number | null
}

/** MOD-5: combo form -> BomProductoCreate body. */
export function buildBomProductoPayload(form: BomProductoPayloadInput): BomProductoCreate {
  return {
    producto_incluido_id: form.producto_incluido_id as number,
    cantidad: form.cantidad as number,
  }
}

/** MOD-5: combo edit -> BomProductoUpdate PUT body (full editable set). */
export function buildBomProductoUpdatePayload(form: BomProductoPayloadInput): BomProductoUpdate {
  return buildBomProductoPayload(form)
}

/** es-CO section labels for the cost tree, keyed by CostoLineaRead.tipo. */
export const COSTO_TIPO_LABELS: Record<CostoLineaRead['tipo'], string> = {
  insumo: 'Insumos',
  producto: 'Productos',
  operativos_fijos: 'Costos operativos fijos',
}

/** The stable tree order: insumos first, then combo products, then fixed costs. */
const COSTO_TIPO_ORDER: CostoLineaRead['tipo'][] = ['insumo', 'producto', 'operativos_fijos']

/** One grouped cost tree section (MOD-5). */
export interface CostoTreeGroup {
  tipo: CostoLineaRead['tipo']
  /** es-CO label from COSTO_TIPO_LABELS. */
  label: string
  /** Sum of the lineas' costo_total (unparseable values count as 0). */
  subtotal: number
  lineas: CostoLineaRead[]
}

/** The full cost tree: grouped lineas + the grand total passthrough. */
export interface CostoTree {
  /** Raw Decimal-as-string grand total (formatted at render time). */
  total: string
  groups: CostoTreeGroup[]
}

/**
 * MOD-5: group CostoProduccionRead.lineas by tipo (stable insumo -> producto
 * -> operativos_fijos order) and sum each group's costo_total. Tipos with no
 * lineas are omitted; an empty breakdown yields zero groups.
 */
export function buildCostoTree(costo: CostoProduccionRead): CostoTree {
  const groups = COSTO_TIPO_ORDER.map((tipo) => {
    const lineas = costo.lineas.filter((l) => l.tipo === tipo)
    if (lineas.length === 0) return null
    const subtotal = lineas.reduce((sum, l) => {
      const parsed = parseDecimal(l.costo_total)
      return sum + (parsed === null ? 0 : parsed)
    }, 0)
    return { tipo, label: COSTO_TIPO_LABELS[tipo], subtotal, lineas }
  }).filter((g): g is CostoTreeGroup => g !== null)

  return { total: costo.total, groups }
}
