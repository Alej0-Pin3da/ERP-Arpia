/**
 * Local-AI commercial copy service (V6 M5).
 * Read-only: fills the product description, saves via the normal flow.
 */
import { client } from '@/api/client'

export interface GenerarCopyResponse {
  producto_id: number
  producto_nombre: string
  texto: string
  modelo: string
}

export async function generarCopy(productoId: number): Promise<GenerarCopyResponse> {
  const { data } = await client.post<GenerarCopyResponse>('/ai/generar-copy', {
    producto_id: productoId,
  })
  return data
}
