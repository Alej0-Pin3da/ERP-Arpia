/**
 * parseColumnFilter unit tests (header column filters).
 *
 * Normalizes an el-table `filter-change` column payload (array of selected
 * raw values, empty when cleared — Element Plus 2.9) into a single value.
 */
import { describe, expect, it } from 'vitest'

import { parseColumnFilter } from '@/utils/table-filters'

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