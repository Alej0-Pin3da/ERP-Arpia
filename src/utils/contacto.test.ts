import { describe, it, expect } from 'vitest'
import { ARPIA_WHATSAPP, waUrl } from './contacto'

describe('waUrl', () => {
  it('usa el número oficial cuando no hay teléfono', () => {
    expect(waUrl(null, 'hola')).toBe(`https://wa.me/${ARPIA_WHATSAPP}?text=hola`)
    expect(waUrl('', 'hola')).toBe(`https://wa.me/${ARPIA_WHATSAPP}?text=hola`)
  })

  it('sanea el teléfono a solo dígitos', () => {
    expect(waUrl('+57 321-726-5049', 'hola')).toBe('https://wa.me/573217265049?text=hola')
  })

  it('respeta un teléfono válido distinto', () => {
    expect(waUrl('3001234567', 'hola')).toBe('https://wa.me/3001234567?text=hola')
  })
})
