import { client } from '@/api/client'

export type EstadoTermometro = 'sin_datos' | 'sin_configurar' | 'alerta' | 'en_camino' | 'superada'

export interface TermometroRead {
  periodo: string
  estado: EstadoTermometro
  ventas_netas: number | string
  costos_netos: number | string
  margen_pct: number | string
  costos_fijos: number | string
  meta_ventas: number | string | null
  avance_pct: number | string | null
  faltante: number | string | null
  utilidad_extra: number | string | null
  n_ventas: number
  n_devoluciones: number
}

export async function getTermometro(): Promise<TermometroRead> {
  const { data } = await client.get<TermometroRead>('/finanzas/punto-equilibrio')
  return data
}
