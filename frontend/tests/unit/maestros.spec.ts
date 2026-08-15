/**
 * Maestros mapper tests (PR11, spec MOD-5 maestros part).
 *
 * Pure functions only, zero mocks:
 *  - `MAESTRO_ENTITIES` drives the generic CRUD table + form (per-entity
 *    column/field config for clientes / tipos-producto / categorias-insumos)
 *  - `buildMaestroPayload` (generic core): required fields always included,
 *    EMPTY optional fields serialize as `null` — needed so an edit that
 *    CLEARS an optional field actually nulls it server-side (the update
 *    schemas use exclude_unset, so omitting would silently keep the value)
 *  - the 6 per-entity typed builders (create + update) that the view uses to
 *    send the exact schema shapes
 */
import { describe, expect, it } from 'vitest'

import {
  buildCategoriaInsumoPayload,
  buildCategoriaInsumoUpdatePayload,
  buildClientePayload,
  buildClienteUpdatePayload,
  buildMaestroPayload,
  buildTipoProductoPayload,
  buildTipoProductoUpdatePayload,
  MAESTRO_ENTITIES,
  maestroEntityConfig,
  type MaestroField,
} from '@/utils/maestros'

const NAME_ONLY_FIELDS: MaestroField[] = [{ key: 'nombre', label: 'Nombre', required: true }]

const CLIENTE_FIELDS: MaestroField[] = [
  { key: 'nombre', label: 'Nombre', required: true },
  { key: 'documento_identidad', label: 'Documento de identidad' },
  { key: 'email', label: 'Email', inputType: 'email' },
  { key: 'telefono', label: 'Teléfono' },
]

describe('MAESTRO_ENTITIES config (MOD-5)', () => {
  it('defines the three maestros entities with es-CO titles', () => {
    expect(MAESTRO_ENTITIES.map((e) => e.key)).toEqual([
      'clientes',
      'tipos-producto',
      'categorias-insumos',
    ])
    expect(MAESTRO_ENTITIES.map((e) => e.title)).toEqual([
      'Clientes',
      'Tipos de producto',
      'Categorías de insumos',
    ])
  })

  it('clientes config mirrors the ClienteCreate schema (nombre required + 3 optionals)', () => {
    const cliente = maestroEntityConfig('clientes')
    expect(cliente?.fields.map((f) => f.key)).toEqual([
      'nombre',
      'documento_identidad',
      'email',
      'telefono',
    ])
    expect(cliente?.fields.find((f) => f.key === 'nombre')?.required).toBe(true)
    expect(cliente?.fields.find((f) => f.key === 'documento_identidad')?.required).toBeUndefined()
    // Table columns come from the same schema: optional columns render '—'.
    expect(cliente?.columns.map((c) => c.key)).toEqual([
      'nombre',
      'documento_identidad',
      'email',
      'telefono',
    ])
  })

  it('tipos-producto and categorias-insumos are name-only entities', () => {
    expect(maestroEntityConfig('tipos-producto')?.fields.map((f) => f.key)).toEqual(['nombre'])
    expect(maestroEntityConfig('categorias-insumos')?.fields.map((f) => f.key)).toEqual(['nombre'])
    expect(maestroEntityConfig('tipos-producto')?.singular).toBe('Tipo de producto')
    expect(maestroEntityConfig('categorias-insumos')?.singular).toBe('Categoría de insumos')
  })
})

describe('buildMaestroPayload (generic core)', () => {
  it('keeps required fields and serializes empty optional fields as null', () => {
    expect(
      buildMaestroPayload(CLIENTE_FIELDS, {
        nombre: 'Ana Torres',
        documento_identidad: '',
        email: '',
        telefono: '',
      }),
    ).toEqual({
      nombre: 'Ana Torres',
      documento_identidad: null,
      email: null,
      telefono: null,
    })
  })

  it('keeps filled optional fields and trims whitespace', () => {
    expect(
      buildMaestroPayload(CLIENTE_FIELDS, {
        nombre: '  Ana Torres ',
        documento_identidad: ' CC 123 ',
        email: 'ana@arpia.com.co',
        telefono: '3001234567',
      }),
    ).toEqual({
      nombre: 'Ana Torres',
      documento_identidad: 'CC 123',
      email: 'ana@arpia.com.co',
      telefono: '3001234567',
    })
  })

  it('handles name-only entities (single required field)', () => {
    expect(buildMaestroPayload(NAME_ONLY_FIELDS, { nombre: 'Alimentos' })).toEqual({
      nombre: 'Alimentos',
    })
  })
})

describe('per-entity typed payload builders', () => {
  it('buildClientePayload returns the exact ClienteCreate shape', () => {
    expect(
      buildClientePayload({
        nombre: 'Ana Torres',
        documento_identidad: '',
        email: 'ana@arpia.com.co',
        telefono: '',
      }),
    ).toEqual({
      nombre: 'Ana Torres',
      documento_identidad: null,
      email: 'ana@arpia.com.co',
      telefono: null,
    })
  })

  it('buildClienteUpdatePayload matches ClienteUpdate (same fields, all optional)', () => {
    expect(
      buildClienteUpdatePayload({
        nombre: 'Ana Torres R.',
        documento_identidad: 'CC 123',
        email: '',
        telefono: '3001234567',
      }),
    ).toEqual({
      nombre: 'Ana Torres R.',
      documento_identidad: 'CC 123',
      email: null,
      telefono: '3001234567',
    })
  })

  it('buildTipoProductoPayload / Update are name-only', () => {
    expect(buildTipoProductoPayload({ nombre: 'Alimentos' })).toEqual({ nombre: 'Alimentos' })
    expect(buildTipoProductoUpdatePayload({ nombre: 'Alimentos preparados' })).toEqual({
      nombre: 'Alimentos preparados',
    })
  })

  it('buildCategoriaInsumoPayload / Update are name-only', () => {
    expect(buildCategoriaInsumoPayload({ nombre: 'Granos' })).toEqual({ nombre: 'Granos' })
    expect(buildCategoriaInsumoUpdatePayload({ nombre: 'Granos y semillas' })).toEqual({
      nombre: 'Granos y semillas',
    })
  })
})
