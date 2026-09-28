import { describe, expect, it } from 'vitest'
import {
  METROS_POR_YARDA,
  TOPE_COSTO_HILOS,
  TOPE_HILO_METROS,
  diffCantidadesBOM,
  esLineaSospechosa,
  estimarHilos,
  fueAutoajustada,
  metrosHiloDeLinea,
  metrosTelaDeLineas,
  normalizarAMetros,
  redondearCentavos,
  subtotalLineaMaterial,
  subtotalMateriales,
} from './unidades'

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

describe('matemática del cotizador (paridad con backend)', () => {
  it('subtotal por línea con desperdicio propio', () => {
    expect(
      subtotalLineaMaterial({ cantidad: 2, precio_unitario: 10000, desperdicio_pct: 10 }),
    ).toBeCloseTo(22000, 10)
  })

  it('subtotal total redondea HALF_UP igual que _calcular (3 × 0.7933 = 2.38)', () => {
    expect(
      subtotalMateriales([{ cantidad: 3, precio_unitario: 0.7933, desperdicio_pct: 0 }]),
    ).toBe(2.38)
    expect(redondearCentavos(2.3799)).toBe(2.38)
  })

  it('metros de tela excluyen mercería aunque venga en cm', () => {
    const lineas = [
      { cantidad: 234, unidad_medida: 'cm', esTela: true }, // 2.34 m
      { cantidad: 504, unidad_medida: 'cm', esTela: false }, // encaje: no cuenta
      { cantidad: 2, unidad_medida: 'un', esTela: false },
    ]
    expect(metrosTelaDeLineas(lineas)).toBeCloseTo(2.34, 10)
  })

  it('marca líneas sospechosas de más de 50 m', () => {
    expect(esLineaSospechosa({ cantidad: 23400, unidad_medida: 'cm' })).toBe(true)
    expect(esLineaSospechosa({ cantidad: 234, unidad_medida: 'cm' })).toBe(false)
    expect(esLineaSospechosa({ cantidad: 2, unidad_medida: 'm' })).toBe(false)
  })
})

describe('tope y doble escala de hilos (Falda Emily)', () => {
  it('23.400 cm con doble escala se computan como 2,34 m para hilos', () => {
    expect(metrosHiloDeLinea({ cantidad: 23400, unidad_medida: 'cm', esTela: true })).toBeCloseTo(2.34, 10)
    expect(fueAutoajustada({ cantidad: 23400, unidad_medida: 'cm', esTela: true })).toBe(true)
  })

  it('cm normales (234 cm = 2,34 m) no se autoajustan', () => {
    expect(metrosHiloDeLinea({ cantidad: 234, unidad_medida: 'cm', esTela: true })).toBeCloseTo(2.34, 10)
    expect(fueAutoajustada({ cantidad: 234, unidad_medida: 'cm', esTela: true })).toBe(false)
  })

  it('el costo de hilo jamás supera $2.000 (tope automático)', () => {
    expect(estimarHilos(234, 2)).toEqual({ metros: 500, costo: 1000, conTope: false })
    expect(estimarHilos(234, 8)).toEqual({ metros: 500, costo: TOPE_COSTO_HILOS, conTope: true })
    expect(estimarHilos(2.34, 2)).toEqual({ metros: 281, costo: 562, conTope: false })
    expect(TOPE_HILO_METROS).toBe(500)
  })
})

describe('diff de cantidades BOM (Fase 2)', () => {
  it('detecta solo líneas del BOM con cantidad cambiada', () => {
    const diff = diffCantidadesBOM([
      { cantidad: 5, bomLineaId: 1, cantidadOriginal: 2, nombre: 'Tela' },
      { cantidad: 2, bomLineaId: 2, cantidadOriginal: 2, nombre: 'Forro' },
      { cantidad: 9, nombre: 'Extra manual' },
    ])
    expect(diff).toEqual([{ bomLineaId: 1, nombre: 'Tela', antes: 2, ahora: 5 }])
  })

  it('ignora líneas sin rastreo o sin cambios', () => {
    expect(diffCantidadesBOM([])).toEqual([])
    expect(diffCantidadesBOM([{ cantidad: 1 }])).toEqual([])
  })
})
