import { client } from '@/api/client'

/** Mirrors `backend/app/schemas/usuario.py` (roles: admin|operador|consulta). */
export interface UsuarioRead {
  id: number
  nombre: string
  email: string
  rol: string
}

export interface UsuarioCreate {
  nombre: string
  email: string
  rol: string
  password: string
}

export interface UsuarioUpdate {
  nombre?: string
  email?: string
  rol?: string
  password?: string
}

export interface ListUsuariosParams {
  q?: string
  rol?: 'admin' | 'operador' | 'consulta'
  limit?: number
  offset?: number
}

export interface Paginated<T> { items: T[]; total: number }

export async function listUsuarios(params?: ListUsuariosParams): Promise<Paginated<UsuarioRead>> {
  const { data } = await client.get<Paginated<UsuarioRead>>('/usuarios', { params })
  return data
}

export async function getUsuario(id: number): Promise<UsuarioRead> {
  const { data } = await client.get<UsuarioRead>(`/usuarios/${id}`)
  return data
}

export async function createUsuario(payload: UsuarioCreate): Promise<UsuarioRead> {
  const { data } = await client.post<UsuarioRead>('/usuarios', payload)
  return data
}

export async function updateUsuario(id: number, payload: UsuarioUpdate): Promise<UsuarioRead> {
  const { data } = await client.patch<UsuarioRead>(`/usuarios/${id}`, payload)
  return data
}

export async function deleteUsuario(id: number): Promise<void> {
  await client.delete(`/usuarios/${id}`)
}

export async function changePassword(
  id: number,
  payload: { current_password: string; new_password: string },
): Promise<void> {
  await client.patch(`/usuarios/${id}/password`, payload)
}
