/**
 * Maestros mappers + entity config (PR11, spec MOD-5 maestros part).
 *
 * The four master-data entities (clientes, proveedores, tipos-producto,
 * categorias-insumos) share one shape — `{nombre, ...optional text fields}`
 * — so ONE config-driven CRUD pattern serves them all:
 *
 *  - `MAESTRO_ENTITIES` is the per-entity column/field config that drives the
 *    generic table (MaestrosTable) and form (MaestroForm). Mirrors the
 *    backend schemas exactly (verified app/schemas/{cliente,proveedor,
 *    producto,categoria_insumo}.py): nombre is the only required field, the
 *    rest are optional strings.
 *  - `buildMaestroPayload` (generic core): required fields always included;
 *    EMPTY optional fields serialize as `null`. The update schemas use
 *    `exclude_unset`, so omitting a cleared optional field would silently
 *    keep the old value — an explicit null is what actually clears it.
 *  - the 8 per-entity builders are thin, typed wrappers over the generic
 *    core so the view sends the exact Create/Update schema shapes.
 *
 * Writes are ADMIN ONLY server-side (require_admin on every POST/PUT/DELETE,
 * verified routes/*.py); the UI hides the forms/actions for other roles.
 * DELETE answers 204; tipos-producto also 409 "in use" (IntegrityError).
 */
import type { components } from '@/types/api.d'

type ClienteCreate = components['schemas']['ClienteCreate']
type ClienteUpdate = components['schemas']['ClienteUpdate']
type ProveedorCreate = components['schemas']['ProveedorCreate']
type ProveedorUpdate = components['schemas']['ProveedorUpdate']
type TipoProductoCreate = components['schemas']['TipoProductoCreate']
type TipoProductoUpdate = components['schemas']['TipoProductoUpdate']
type CategoriaInsumoCreate = components['schemas']['CategoriaInsumoCreate']
type CategoriaInsumoUpdate = components['schemas']['CategoriaInsumoUpdate']

/** One form field (drives MaestroForm). Mirrors the entity's create schema. */
export interface MaestroField {
  /** API field name (also the table column key). */
  key: string
  /** es-CO form label. */
  label: string
  /** True for fields the backend requires (nombre on every entity). */
  required?: boolean
  /** Placeholder hint for the input. */
  placeholder?: string
  /** Native input type — email renders with keyboard/validation hints. */
  inputType?: 'text' | 'email'
}

/** One table column (drives MaestrosTable). */
export interface MaestroColumn {
  /** API field name — optional columns render an em dash when empty. */
  key: string
  /** es-CO header label. */
  label: string
  width?: number
  minWidth?: number
  align?: 'left' | 'center' | 'right'
}

/**
 * A list row from any of the four maestros entities: every Read schema is
 * `{id, ...}` plus strings/nullables, so this loose shape types the generic
 * table/form/rows without losing safety at the API boundary.
 */
export interface MaestroRow {
  id: number
  [key: string]: unknown
}

/** Per-entity config consumed by the generic table + form + view. */
export interface MaestroEntityConfig {
  /** Endpoint id (matches the view's entity tabs). */
  key: string
  /** Tab/title label. */
  title: string
  /** Singular es-CO name for messages ("Cliente creado correctamente"). */
  singular: string
  /** Empty-state text for the table. */
  emptyText: string
  columns: MaestroColumn[]
  fields: MaestroField[]
}

export const MAESTRO_ENTITIES: MaestroEntityConfig[] = [
  {
    key: 'clientes',
    title: 'Clientes',
    singular: 'Cliente',
    emptyText: 'Sin clientes registrados',
    columns: [
      { key: 'nombre', label: 'Nombre', minWidth: 200 },
      { key: 'documento_identidad', label: 'Documento', minWidth: 140 },
      { key: 'email', label: 'Email', minWidth: 180 },
      { key: 'telefono', label: 'Teléfono', minWidth: 130 },
    ],
    fields: [
      { key: 'nombre', label: 'Nombre', required: true, placeholder: 'Ej: Ana Torres' },
      { key: 'documento_identidad', label: 'Documento de identidad', placeholder: 'Ej: CC 123456789' },
      { key: 'email', label: 'Email', inputType: 'email', placeholder: 'Ej: ana@arpia.com.co' },
      { key: 'telefono', label: 'Teléfono', placeholder: 'Ej: 3001234567' },
    ],
  },
  {
    key: 'proveedores',
    title: 'Proveedores',
    singular: 'Proveedor',
    emptyText: 'Sin proveedores registrados',
    columns: [
      { key: 'nombre', label: 'Nombre', minWidth: 200 },
      { key: 'ubicacion', label: 'Ubicación', minWidth: 160 },
      { key: 'url', label: 'Sitio web', minWidth: 180 },
      { key: 'contacto', label: 'Contacto', minWidth: 150 },
    ],
    fields: [
      { key: 'nombre', label: 'Nombre', required: true, placeholder: 'Ej: Molino El Triunfo' },
      { key: 'ubicacion', label: 'Ubicación', placeholder: 'Ej: Medellín' },
      { key: 'url', label: 'Sitio web', placeholder: 'Ej: https://eltriunfo.com' },
      { key: 'contacto', label: 'Contacto', placeholder: 'Ej: Carlos Ramírez' },
    ],
  },
  {
    key: 'tipos-producto',
    title: 'Tipos de producto',
    singular: 'Tipo de producto',
    emptyText: 'Sin tipos de producto registrados',
    columns: [{ key: 'nombre', label: 'Nombre', minWidth: 240 }],
    fields: [{ key: 'nombre', label: 'Nombre', required: true, placeholder: 'Ej: Alimentos' }],
  },
  {
    key: 'categorias-insumos',
    title: 'Categorías de insumos',
    singular: 'Categoría de insumos',
    emptyText: 'Sin categorías de insumos registradas',
    columns: [{ key: 'nombre', label: 'Nombre', minWidth: 240 }],
    fields: [{ key: 'nombre', label: 'Nombre', required: true, placeholder: 'Ej: Granos' }],
  },
]

/** Lookup the config for one entity key (undefined for unknown keys). */
export function maestroEntityConfig(key: string): MaestroEntityConfig | undefined {
  return MAESTRO_ENTITIES.find((entity) => entity.key === key)
}

/**
 * Generic payload core over a field config. Required fields are always
 * included; EMPTY optional fields become `null` (so an edit that clears an
 * optional field actually clears it server-side — see module doc).
 */
export function buildMaestroPayload(
  fields: MaestroField[],
  values: Record<string, string>,
): Record<string, string | null> {
  const payload: Record<string, string | null> = {}
  for (const field of fields) {
    const value = (values[field.key] ?? '').trim()
    payload[field.key] = value === '' ? null : value
  }
  return payload
}

/** ClienteCreate / ClienteUpdate — nombre required; 3 optional contact fields. */
export function buildClientePayload(values: Record<string, string>): ClienteCreate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[0].fields,
    values,
  ) as unknown as ClienteCreate
}

export function buildClienteUpdatePayload(values: Record<string, string>): ClienteUpdate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[0].fields,
    values,
  ) as unknown as ClienteUpdate
}

/** ProveedorCreate / ProveedorUpdate — nombre required; ubicacion/url/contacto. */
export function buildProveedorPayload(values: Record<string, string>): ProveedorCreate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[1].fields,
    values,
  ) as unknown as ProveedorCreate
}

export function buildProveedorUpdatePayload(values: Record<string, string>): ProveedorUpdate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[1].fields,
    values,
  ) as unknown as ProveedorUpdate
}

/** TipoProductoCreate / Update — name only (409 on duplicate name server-side). */
export function buildTipoProductoPayload(values: Record<string, string>): TipoProductoCreate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[2].fields,
    values,
  ) as unknown as TipoProductoCreate
}

export function buildTipoProductoUpdatePayload(values: Record<string, string>): TipoProductoUpdate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[2].fields,
    values,
  ) as unknown as TipoProductoUpdate
}

/** CategoriaInsumoCreate / Update — name only. */
export function buildCategoriaInsumoPayload(values: Record<string, string>): CategoriaInsumoCreate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[3].fields,
    values,
  ) as unknown as CategoriaInsumoCreate
}

export function buildCategoriaInsumoUpdatePayload(
  values: Record<string, string>,
): CategoriaInsumoUpdate {
  return buildMaestroPayload(
    MAESTRO_ENTITIES[3].fields,
    values,
  ) as unknown as CategoriaInsumoUpdate
}
