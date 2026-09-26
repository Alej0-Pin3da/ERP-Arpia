/** Número oficial del taller (fallback cuando la clienta no tiene teléfono). */
export const ARPIA_WHATSAPP = '573217265049'

/** URL wa.me con teléfono saneado (solo dígitos) y texto ya codificado. */
export function waUrl(phone: string | null | undefined, encodedText: string): string {
  const clean = (phone || '').replace(/\D/g, '') || ARPIA_WHATSAPP
  return `https://wa.me/${clean}?text=${encodedText}`
}
