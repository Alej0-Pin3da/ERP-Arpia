/**
 * useMaestros — REAL-only adapter over /api/v1/maestros.
 * Every operation delegates to src/services/api/maestros.ts
 * (FastAPI + Postgres). No in-memory mock path remains.
 * Mirrors useClientes / useSocios / useFinanzas; MaestrosView.vue stays intact.
 */
import { useMode } from './useMode'
import * as api from '@/services/api/maestros'

export function useMaestros() {
  const { isMock, mode } = useMode()

  // Proveedores
  async function listProveedores(params: api.ListParams = {}) {
    return api.listProveedores(params)
  }
  async function createProveedor(payload: Record<string, unknown>) {
    return api.createProveedor(payload)
  }
  async function updateProveedor(id: number, payload: Record<string, unknown>) {
    return api.updateProveedor(id, payload)
  }
  async function removeProveedor(id: number) {
    return api.deleteProveedor(id)
  }

  // Categorias
  async function listCategorias(params: api.ListParams = {}) {
    return api.listCategorias(params)
  }
  async function createCategoria(payload: Record<string, unknown>) {
    return api.createCategoria(payload)
  }
  async function updateCategoria(id: number, payload: Record<string, unknown>) {
    return api.updateCategoria(id, payload)
  }
  async function removeCategoria(id: number) {
    return api.deleteCategoria(id)
  }

  // Ubicaciones
  async function listUbicaciones(params: api.ListParams = {}) {
    return api.listUbicaciones(params)
  }
  async function createUbicacion(payload: Record<string, unknown>) {
    return api.createUbicacion(payload)
  }
  async function updateUbicacion(id: number, payload: Record<string, unknown>) {
    return api.updateUbicacion(id, payload)
  }
  async function removeUbicacion(id: number) {
    return api.deleteUbicacion(id)
  }

  // Canales
  async function listCanales(params: api.ListParams = {}) {
    return api.listCanales(params)
  }
  async function createCanal(payload: Record<string, unknown>) {
    return api.createCanal(payload)
  }
  async function updateCanal(id: number, payload: Record<string, unknown>) {
    return api.updateCanal(id, payload)
  }
  async function removeCanal(id: number) {
    return api.deleteCanal(id)
  }

  // Metodos
  async function listMetodosPago(params: api.ListParams = {}) {
    return api.listMetodosPago(params)
  }
  async function createMetodo(payload: Record<string, unknown>) {
    return api.createMetodo(payload)
  }
  async function updateMetodo(id: number, payload: Record<string, unknown>) {
    return api.updateMetodo(id, payload)
  }
  async function removeMetodo(id: number) {
    return api.deleteMetodo(id)
  }

  // Tallas
  async function listTallas(params: api.ListParams = {}) {
    return api.listTallas(params)
  }
  async function createTalla(payload: Record<string, unknown>) {
    return api.createTalla(payload)
  }
  async function updateTalla(id: number, payload: Record<string, unknown>) {
    return api.updateTalla(id, payload)
  }
  async function removeTalla(id: number) {
    return api.deleteTalla(id)
  }

  // Productos sin talla
  async function listProductosSinTalla(params: api.ListParams = {}) {
    return api.listProductosSinTalla(params)
  }
  async function createProductoSinTalla(payload: Record<string, unknown>) {
    return api.createProductoSinTalla(payload)
  }
  async function updateProductoSinTalla(id: number, payload: Record<string, unknown>) {
    return api.updateProductoSinTalla(id, payload)
  }
  async function removeProductoSinTalla(id: number) {
    return api.deleteProductoSinTalla(id)
  }

  // Categorias de producto (master Categoría/Línea de la Ficha, 0037)
  async function listCategoriasProducto(params: api.ListParams = {}) {
    return api.listCategoriasProducto(params)
  }
  async function createCategoriaProducto(payload: Record<string, unknown>) {
    return api.createCategoriaProducto(payload)
  }
  async function updateCategoriaProducto(id: number, payload: Record<string, unknown>) {
    return api.updateCategoriaProducto(id, payload)
  }
  async function removeCategoriaProducto(id: number) {
    return api.deleteCategoriaProducto(id)
  }

  // Parametros singleton
  async function getParametros() {
    return api.getParametros()
  }
  async function updateParametros(payload: Record<string, unknown>) {
    return api.updateParametros(payload)
  }

  return {
    isMock,
    mode,
    // proveedores
    listProveedores,
    createProveedor,
    updateProveedor,
    removeProveedor,
    // categorias
    listCategorias,
    createCategoria,
    updateCategoria,
    removeCategoria,
    // categorias de producto
    listCategoriasProducto,
    createCategoriaProducto,
    updateCategoriaProducto,
    removeCategoriaProducto,
    // ubicaciones
    listUbicaciones,
    createUbicacion,
    updateUbicacion,
    removeUbicacion,
    // canales
    listCanales,
    createCanal,
    updateCanal,
    removeCanal,
    // metodos
    listMetodosPago,
    createMetodo,
    updateMetodo,
    removeMetodo,
    // tallas
    listTallas,
    createTalla,
    updateTalla,
    removeTalla,
    // sin talla
    listProductosSinTalla,
    createProductoSinTalla,
    updateProductoSinTalla,
    removeProductoSinTalla,
    // parametros
    getParametros,
    updateParametros,
  }
}
