/**
 * Mode service — REAL-only. The backend no longer serves a mock mode;
 * GET /api/__mode always reports { mode: 'real' }.
 */
import { client } from '@/api/client'

export interface ApiModeResponse {
  mode: 'real'
  proxyTarget?: string | null
  time?: string
}

export async function fetchApiMode(): Promise<ApiModeResponse> {
  const { data } = await client.get<ApiModeResponse>('/api/__mode')
  return { ...data, mode: 'real' }
}
