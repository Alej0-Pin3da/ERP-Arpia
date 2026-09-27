import { describe, expect, it } from 'vitest'
import { getApiErrorDetail } from './api-error'

function axiosError(detail: unknown): unknown {
  return { response: { data: { detail } }, message: 'Request failed' }
}

describe('getApiErrorDetail', () => {
  it('returns string detail verbatim', () => {
    expect(getApiErrorDetail(axiosError('No encontrado'), 'fallback')).toBe('No encontrado')
  })

  it('joins validation-error arrays', () => {
    const e = axiosError([{ msg: 'campo requerido' }, { loc: ['x'] }])
    expect(getApiErrorDetail(e, 'fallback')).toBe('campo requerido; {"loc":["x"]}')
  })

  it('falls back to Error message without response', () => {
    expect(getApiErrorDetail(new Error('boom'), 'fallback')).toBe('boom')
  })

  it('falls back when nothing usable', () => {
    expect(getApiErrorDetail(null, 'fallback')).toBe('fallback')
    expect(getApiErrorDetail(axiosError(42), 'fallback')).toBe('fallback')
  })

  it('honors custom separator', () => {
    const e = axiosError([{ msg: 'a' }, { msg: 'b' }])
    expect(getApiErrorDetail(e, 'fallback', ', ')).toBe('a, b')
  })
})
