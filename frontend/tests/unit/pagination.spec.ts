/**
 * Unit tests for buildListParams (ui-mantenimiento PR1, T5).
 *
 * The helper derives the backend query params from the view's pagination
 * state: page/pageSize -> limit/offset, filter objects are forwarded (empty
 * values dropped) and q is added only when non-empty (spec FE-1/FE-2).
 */
import { describe, expect, it } from 'vitest'

import { buildListParams } from '@/utils/pagination'

describe('buildListParams', () => {
  it('maps page/pageSize to limit/offset (1-based page)', () => {
    expect(buildListParams({ page: 1, pageSize: 25 })).toEqual({
      limit: 25,
      offset: 0,
    })
    expect(buildListParams({ page: 3, pageSize: 10 })).toEqual({
      limit: 10,
      offset: 20,
    })
  })

  it('applies defaults (page 1, pageSize 50)', () => {
    expect(buildListParams()).toEqual({ limit: 50, offset: 0 })
  })

  it('forwards typed filters and drops empty values', () => {
    const params = buildListParams({
      page: 1,
      pageSize: 20,
      filtros: { tipo_producto_id: 7, estado: 'anulada', canal_venta: '' },
    })
    expect(params).toEqual({
      limit: 20,
      offset: 0,
      tipo_producto_id: 7,
      estado: 'anulada',
    })
  })

  it('adds q only when non-empty', () => {
    expect(buildListParams({ q: 'maria', page: 2, pageSize: 15 }).q).toBe('maria')
    expect(buildListParams({ q: '', page: 1, pageSize: 15 }).q).toBeUndefined()
    expect(buildListParams({ page: 1, pageSize: 15 }).q).toBeUndefined()
  })

  it('combines filters and q (AND semantics go to the backend)', () => {
    const params = buildListParams({
      page: 2,
      pageSize: 30,
      filtros: { rol: 'operador' },
      q: 'juan',
    })
    expect(params).toEqual({ limit: 30, offset: 30, rol: 'operador', q: 'juan' })
  })
})
