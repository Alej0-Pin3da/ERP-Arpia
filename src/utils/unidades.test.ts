import { describe, expect, it } from 'vitest'
import { METROS_POR_YARDA, normalizarAMetros } from './unidades'

describe('normalizarAMetros', () => {
  it('pasa metros tal cual', () => {
    expect(normalizarAMetros(234, 'm')).toBe(234)
    expect(normalizarAMetros(10, 'metros')).toBe(10)
    expect(normalizarAMetros(5, 'MTS')).toBe(5)
  })

  it('convierte cm dividiendo entre 100 (caso 23.400 cm -> 234 m)', () => {
    expect(normalizarAMetros(23400, 'cm')).toBe(234)
    expect(normalizarAMetros(504, 'cm')).toBeCloseTo(5.04, 10)
  })

  it('convierte mm dividiendo entre 1000', () => {
    expect(normalizarAMetros(2000, 'mm')).toBe(2)
  })

  it('convierte yardas a metros reales', () => {
    expect(normalizarAMetros(100, 'yarda')).toBeCloseTo(100 * METROS_POR_YARDA, 10)
    expect(normalizarAMetros(10, 'yardas')).toBeCloseTo(9.144, 10)
    expect(normalizarAMetros(10, 'yd')).toBeCloseTo(9.144, 10)
  })

  it('devuelve null para unidades no-longitud (jamás van a metros)', () => {
    for (const u of ['un', 'doc', 'par', 'pza', 'kg', 'rollo', '']) {
      expect(normalizarAMetros(100, u)).toBeNull()
    }
  })

  it('es tolerante a mayúsculas, espacios y nulos', () => {
    expect(normalizarAMetros(100, ' CM ')).toBe(1)
    expect(normalizarAMetros(100, null)).toBeNull()
    expect(normalizarAMetros(Number.NaN, 'm')).toBeNull()
  })
})
