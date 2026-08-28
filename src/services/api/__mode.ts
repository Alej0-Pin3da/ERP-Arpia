/**
 * Mode service — checks backend status via GET /__mode.
 */
import { client } from '@/api/client'

export interface ApiModeResponse {
  mode: 'mock' | 'real'
  db_connected: boolean
  version: string
}

export async function fetchApiMode(): Promise<ApiModeResponse> {
  const { data } = await client.get<ApiModeResponse>('/__mode')
  return data
}
