/**
 * parseColumnFilter unit tests (header column filters).
 *
 * Normalizes an el-table `filter-change` column payload (array of selected
 * raw values, empty when cleared — Element Plus 2.9) into a single value.
 */
import { describe, expect, it } from 'vitest'

import { parseColumnFilter, parsePrimeVueFilters, parsePrimeVueSort } from '@/utils/table-filters'

describe('parseColumnFilter', () => {
  it('returns the first selected value from an el-table payload', () => {
    expect(parseColumnFilter(['feria'])).toBe('feria')
    expect(parseColumnFilter([2])).toBe(2)
    expect(parseColumnFilter([true])).toBe(true)
  })

  it('returns null when the filter is cleared (empty array)', () => {
    expect(parseColumnFilter([])).toBeNull()
  })

  it('returns null for non-array payloads', () => {
    expect(parseColumnFilter(undefined)).toBeNull()
    expect(parseColumnFilter(null)).toBeNull()
    expect(parseColumnFilter('feria')).toBeNull()
  })

  it('unwraps legacy payloads that pass full option objects', () => {
    expect(parseColumnFilter([{ text: 'Feria', value: 'feria' }, { text: 'Web', value: 'web' }])).toBe(
      'feria',
    )
    expect(parseColumnFilter([{ text: 'Granos', value: 1 }])).toBe(1)
  })

  it('returns null when the first element is not a filter value shape', () => {
    expect(parseColumnFilter([{ foo: 'bar' }])).toBeNull()
    expect(parseColumnFilter([{ value: null }])).toBeNull()
  })
})

describe('parsePrimeVueFilters', () => {
  it('maps a single constraint to a per-column array of raw values', () => {
    expect(parsePrimeVueFilters({ canal_venta: { value: 'web', matchMode: 'equals' } })).toEqual({
      canal_venta: ['web'],
    })
  })

  it('maps a multi-constraint array preserving order', () => {
    expect(parsePrimeVueFilters({ estado: [{ value: 'completada' }, { value: 'anulada' }] })).toEqual({
      estado: ['completada', 'anulada'],
    })
  })

  it('maps multiple columns independently', () => {
    expect(
      parsePrimeVueFilters({
        canal_venta: { value: 'web' },
        estado: { value: null },
      }),
    ).toEqual({ canal_venta: ['web'], estado: [null] })
  })

  it('keeps a null value as [null] so parseColumnFilter normalizes it to null', () => {
    const normalized = parsePrimeVueFilters({ canal_venta: { value: null } })
    expect(normalized).toEqual({ canal_venta: [null] })
    expect(parseColumnFilter(normalized.canal_venta)).toBeNull()
  })

  it('preserves {text,value} option objects for the parseColumnFilter unwrap', () => {
    const normalized = parsePrimeVueFilters({ canal_venta: { value: { text: 'Feria', value: 'feria' } } })
    expect(normalized).toEqual({ canal_venta: [{ text: 'Feria', value: 'feria' }] })
    expect(parseColumnFilter(normalized.canal_venta)).toBe('feria')
  })

  it('returns an empty record for an empty filters payload', () => {
    expect(parsePrimeVueFilters({})).toEqual({})
  })
})

describe('parsePrimeVueSort', () => {
  it('maps sortOrder 1 to asc', () => {
    expect(parsePrimeVueSort({ sortField: 'fecha', sortOrder: 1 })).toEqual({ prop: 'fecha', order: 'asc' })
  })

  it('maps sortOrder -1 to desc', () => {
    expect(parsePrimeVueSort({ sortField: 'fecha', sortOrder: -1 })).toEqual({ prop: 'fecha', order: 'desc' })
  })

  it('maps sortOrder 0 to null', () => {
    expect(parsePrimeVueSort({ sortField: 'fecha', sortOrder: 0 })).toEqual({ prop: 'fecha', order: null })
  })

  it('maps an undefined sortOrder to null', () => {
    expect(parsePrimeVueSort({ sortField: 'fecha' })).toEqual({ prop: 'fecha', order: null })
  })

  it('defaults the prop to an empty string when no sortField is present', () => {
    expect(parsePrimeVueSort({})).toEqual({ prop: '', order: null })
  })
})