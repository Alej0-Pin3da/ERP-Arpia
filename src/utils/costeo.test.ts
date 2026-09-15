import { describe, it, expect } from 'vitest'
import { calcularCostosUnitarios } from './costeo'

describe('calcularCostosUnitarios', () => {
  it('prorratea totales del lote por unidad', () => {
    expect(
      calcularCostosUnitarios({ manoObra: 50000, energia: 8000, minutos: 600 }, 10),
    ).toEqual({ mano_obra: 5000, cif_energia: 800, tiempo_confeccion_min: 60 })
  })

  it('redondea $ a 2 decimales y minutos a entero', () => {
    // 100/3 = 33.333… → 33.33 ; 10/3 = 3.333… min → 3
    expect(
      calcularCostosUnitarios({ manoObra: 100, energia: 100, minutos: 10 }, 3),
    ).toEqual({ mano_obra: 33.33, cif_energia: 33.33, tiempo_confeccion_min: 3 })
  })

  it('acepta totales como string (el backend serializa Numeric así)', () => {
    expect(
      calcularCostosUnitarios({ manoObra: '50000.0000', energia: '8000.00', minutos: '600.00' }, 10),
    ).toEqual({ mano_obra: 5000, cif_energia: 800, tiempo_confeccion_min: 60 })
  })

  it('devuelve null con N = 0, negativo o faltante', () => {
    const totales = { manoObra: 50000, energia: 8000, minutos: 600 }
    expect(calcularCostosUnitarios(totales, 0)).toBeNull()
    expect(calcularCostosUnitarios(totales, -4)).toBeNull()
    expect(calcularCostosUnitarios(totales, null)).toBeNull()
    expect(calcularCostosUnitarios(totales, undefined)).toBeNull()
    expect(calcularCostosUnitarios(totales, Number.NaN)).toBeNull()
  })

  it('trata totales nulos como 0 en vez de NaN', () => {
    expect(
      calcularCostosUnitarios({ manoObra: null, energia: undefined, minutos: null }, 5),
    ).toEqual({ mano_obra: 0, cif_energia: 0, tiempo_confeccion_min: 0 })
  })
})
