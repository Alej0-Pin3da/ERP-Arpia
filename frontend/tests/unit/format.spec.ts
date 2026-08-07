/**
 * es-CO formatter tests (task 1.4, spec SHELL-2 "central es-CO Decimal
 * formatter"). All money/quantity fields from the API are JSON strings — the
 * formatter must handle Decimal-as-string, and degrade null/undefined/empty.
 */
import { describe, it, expect } from 'vitest'
import { formatMoney, parseDecimal, formatDate, formatDateTime } from '@/utils/format'

describe('formatMoney (Intl.NumberFormat es-CO, 2 decimals)', () => {
  it('formats a Decimal-as-string with es-CO grouping and 2 decimals', () => {
    expect(formatMoney('12345.6789')).toBe('$12.345,68')
  })

  it('rounds half away from zero to 2 decimals', () => {
    expect(formatMoney('999.995')).toBe('$1.000,00')
  })

  it('formats plain numbers', () => {
    expect(formatMoney(1234.5)).toBe('$1.234,50')
  })

  it('normalizes a comma decimal separator (client-typed input)', () => {
    expect(formatMoney('1234,56')).toBe('$1.234,56')
  })

  it('null / undefined / empty string all render "$0,00"', () => {
    expect(formatMoney(null)).toBe('$0,00')
    expect(formatMoney(undefined)).toBe('$0,00')
    expect(formatMoney('')).toBe('$0,00')
  })

  it('handles negative amounts', () => {
    expect(formatMoney('-250.50')).toBe('-$250,50')
  })

  it('handles a large integer-as-string', () => {
    expect(formatMoney('1000000000')).toBe('$1.000.000.000,00')
  })
})

describe('parseDecimal (safe parse)', () => {
  it('parses a Decimal string to a number', () => {
    expect(parseDecimal('12345.67')).toBe(12345.67)
  })

  it('parses a comma decimal string', () => {
    expect(parseDecimal('1234,56')).toBe(1234.56)
  })

  it('returns null for non-numeric input', () => {
    expect(parseDecimal('abc')).toBeNull()
    expect(parseDecimal(null)).toBeNull()
    expect(parseDecimal(undefined)).toBeNull()
    expect(parseDecimal('')).toBeNull()
  })
})

describe('formatDate / formatDateTime (ISO -> es-CO)', () => {
  it('formats an ISO date as dd/mm/yyyy', () => {
    expect(formatDate('2026-08-07')).toBe('07/08/2026')
  })

  it('formats a datetime as dd/mm/yyyy', () => {
    expect(formatDateTime('2026-08-07T14:30:00')).toBe('07/08/2026')
  })

  it('is timezone-stable for an offset datetime (Colombia UTC-5)', () => {
    expect(formatDateTime('2026-08-07T23:00:00-05:00')).toBe('07/08/2026')
  })

  it('returns null for unparseable input', () => {
    expect(formatDate('not-a-date')).toBeNull()
    expect(formatDateTime(null)).toBeNull()
  })
})
