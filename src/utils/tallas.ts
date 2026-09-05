/**
 * Talla code mapping between UI labels and the backend.
 *
 * Backend `clientes.talla_habitual/superior/inferior` are `max_length=10`,
 * but the UI works with long display labels ("Sin Talla (Tote Bags)" = 21
 * chars). Persist the short code in REAL mode; keep long labels in MOCK.
 */
export const TALLA_SIN_TALLA = 'SIN_TALLA'
export const TALLA_UNICA = 'UNICA'

export function toTallaCode(value: string | null | undefined): string | null {
  if (!value) return null
  if (value.includes('Sin Talla') || value === TALLA_SIN_TALLA) return TALLA_SIN_TALLA
  if (
    value.includes('Talla Unica') ||
    value.includes('Talla Única') ||
    value === TALLA_UNICA
  )
    return TALLA_UNICA
  return value
}

export function fromTallaCode(value: string | null | undefined, fallback = 'S'): string {
  if (value === TALLA_SIN_TALLA) return 'Sin Talla (Tote Bags)'
  if (value === TALLA_UNICA) return 'Talla Unica / Surtido'
  return value || fallback
}
