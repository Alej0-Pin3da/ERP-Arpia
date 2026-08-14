/**
 * Composable: Productos catalog — table, CRUD, and nested variantes state.
 *
 * Owns all refs and async functions that the Productos tab of ProductosView
 * needs. Keeps the view template thin: it only binds, it does not logic.
 */
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { insumosApi, productosApi, tiposProductoApi } from '@/api/endpoints'
import { serverDetail } from '@/utils/api'
import { buildListParams } from '@/utils/pagination'
import { buildProductoRows } from '@/utils/productos'
import type {
  ProductoPayloadInput,
  ProductoRow,
  VariantePayloadInput,
} from '@/utils/productos'
import type { InsumoRead, ProductoRead, TipoProductoRead, VarianteProductoRead } from '@/types/api.d'

export function useProductosCatalog() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  // --- paginated table -------------------------------------------------------
  const productos = ref<ProductoRead[]>([])
  const productosTotal = ref(0)
  const productosPage = ref(1)
  const productosPageSize = ref(20)
  const productoQ = ref('')
  const filterTipoProductoId = ref<number | null>(null)
  const productosSortBy = ref<string | null>(null)
  const productosSortOrder = ref<'asc' | 'desc' | null>(null)

  // --- shared lookups (D3: full sets) ----------------------------------------
  const productosLookup = ref<ProductoRead[]>([])
  const tipos = ref<TipoProductoRead[]>([])
  const insumos = ref<InsumoRead[]>([])

  const productoRows = computed(() => buildProductoRows(productos.value, tipos.value))

  // --- CRUD dialog state -----------------------------------------------------
  const savingProducto = ref(false)
  const editingProducto = ref<ProductoRead | null>(null)
  const productoDialogVisible = ref(false)

  // --- nested variantes (lazy per selected product) --------------------------
  const selectedProducto = ref<ProductoRead | null>(null)
  const variantes = ref<VarianteProductoRead[]>([])
  const variantesLoading = ref(false)
  const savingVariante = ref(false)
  const editingVariante = ref<VarianteProductoRead | null>(null)
  const varianteDialogVisible = ref(false)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const [productosList, tiposList, insumosList, productosLookup_] = await Promise.all([
        productosApi.list(
          buildListParams({
            page: productosPage.value,
            pageSize: productosPageSize.value,
            filtros: { tipo_producto_id: filterTipoProductoId.value },
            q: productoQ.value,
            sortBy: productosSortBy.value ?? undefined,
            sortOrder: productosSortOrder.value ?? undefined,
          }),
        ),
        tiposProductoApi.list({ limit: 1000 }),
        insumosApi.list({ limit: 1000 }),
        productosApi.list({ limit: 1000 }),
      ])
      productos.value = productosList.items
      productosTotal.value = productosList.total
      tipos.value = tiposList.items
      insumos.value = insumosList.items
      productosLookup.value = productosLookup_.items
    } catch {
      error.value = 'No se pudo cargar la información de productos. Verifica la conexión con el servidor.'
    } finally {
      loading.value = false
    }
  }

  function onProductosSearch(): void {
    productosPage.value = 1
    void load()
  }

  function onProductosFilterChange(): void {
    productosPage.value = 1
    void load()
  }

  function onProductosTableSortChange(sort: { prop: string; order: 'asc' | 'desc' | null }): void {
    productosSortBy.value = sort.order === null ? null : sort.prop
    productosSortOrder.value = sort.order
    onProductosFilterChange()
  }

  // --- Producto CRUD ---------------------------------------------------------

  function openCreateProducto(): void {
    editingProducto.value = null
    productoDialogVisible.value = true
  }

  function onEditProducto(row: ProductoRow): void {
    const found = productos.value.find((p) => p.id === row.id)
    if (found) editingProducto.value = found
    productoDialogVisible.value = true
  }

  function resetProductoDialog(): void {
    editingProducto.value = null
  }

  function submitProducto(payload: ProductoPayloadInput): void {
    if (editingProducto.value === null) {
      void onCreateProducto(payload)
    } else {
      void onUpdateProducto(payload)
    }
  }

  async function onCreateProducto(payload: ProductoPayloadInput): Promise<void> {
    savingProducto.value = true
    try {
      await productosApi.create(payload)
      ElMessage.success('Producto creado correctamente')
      productoDialogVisible.value = false
      await load()
    } catch (err) {
      ElMessage.error(serverDetail(err) ?? 'No se pudo crear el producto.')
    } finally {
      savingProducto.value = false
    }
  }

  async function onUpdateProducto(payload: ProductoPayloadInput): Promise<void> {
    if (editingProducto.value === null) return
    savingProducto.value = true
    try {
      await productosApi.update({ producto_id: editingProducto.value.id }, payload)
      ElMessage.success('Producto actualizado correctamente')
      productoDialogVisible.value = false
      await load()
    } catch (err) {
      ElMessage.error(serverDetail(err) ?? 'No se pudo actualizar el producto.')
    } finally {
      savingProducto.value = false
    }
  }

  async function onDeleteProducto(row: ProductoRow): Promise<void> {
    try {
      await ElMessageBox.confirm(
        `¿Eliminar el producto "${row.nombre}"?`,
        'Confirmar eliminación',
        { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
      )
    } catch {
      return
    }
    try {
      await productosApi.delete({ producto_id: row.id })
      ElMessage.success('Producto eliminado correctamente')
      await load()
    } catch (err) {
      ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar el producto.')
    }
  }

  // --- Variantes (nested, admin) ---------------------------------------------

  async function loadVariantes(productoId: number): Promise<void> {
    variantesLoading.value = true
    try {
      variantes.value = await productosApi.listVariantes({ producto_id: productoId })
    } catch {
      ElMessage.error('No se pudieron cargar las variantes del producto.')
    } finally {
      variantesLoading.value = false
    }
  }

  async function onSelectVariantes(row: ProductoRow): Promise<void> {
    selectedProducto.value = productos.value.find((p) => p.id === row.id) ?? null
    editingVariante.value = null
    await loadVariantes(row.id)
  }

  function openCreateVariante(): void {
    editingVariante.value = null
    varianteDialogVisible.value = true
  }

  function onEditVariante(variante: VarianteProductoRead): void {
    editingVariante.value = variante
    varianteDialogVisible.value = true
  }

  function resetVarianteDialog(): void {
    editingVariante.value = null
  }

  async function onSubmitVariante(payload: VariantePayloadInput): Promise<void> {
    if (selectedProducto.value === null) return
    savingVariante.value = true
    try {
      if (editingVariante.value !== null) {
        await productosApi.updateVariante(
          { producto_id: selectedProducto.value.id, variante_id: editingVariante.value.id },
          payload,
        )
        ElMessage.success('Variante actualizada correctamente')
        editingVariante.value = null
      } else {
        await productosApi.createVariante({ producto_id: selectedProducto.value.id }, payload)
        ElMessage.success('Variante creada correctamente')
      }
      varianteDialogVisible.value = false
      await loadVariantes(selectedProducto.value.id)
    } catch (err) {
      ElMessage.error(serverDetail(err) ?? 'No se pudo guardar la variante.')
    } finally {
      savingVariante.value = false
    }
  }

  async function onDeleteVariante(variante: VarianteProductoRead): Promise<void> {
    if (selectedProducto.value === null) return
    try {
      await ElMessageBox.confirm(
        `¿Eliminar la variante "${variante.nombre_variante}"?`,
        'Confirmar eliminación',
        { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
      )
    } catch {
      return
    }
    try {
      await productosApi.deleteVariante({
        producto_id: selectedProducto.value.id,
        variante_id: variante.id,
      })
      ElMessage.success('Variante eliminada correctamente')
      await loadVariantes(selectedProducto.value.id)
    } catch (err) {
      ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar la variante.')
    }
  }

  return {
    // state — productos table
    loading,
    error,
    productos,
    productosTotal,
    productosPage,
    productosPageSize,
    productoQ,
    filterTipoProductoId,
    productosSortBy,
    productosSortOrder,
    productoRows,
    // state — lookups
    productosLookup,
    tipos,
    insumos,
    // state — producto dialog
    savingProducto,
    editingProducto,
    productoDialogVisible,
    // state — variantes
    selectedProducto,
    variantes,
    variantesLoading,
    savingVariante,
    editingVariante,
    varianteDialogVisible,
    // actions
    load,
    onProductosSearch,
    onProductosFilterChange,
    onProductosTableSortChange,
    openCreateProducto,
    onEditProducto,
    resetProductoDialog,
    submitProducto,
    onDeleteProducto,
    onSelectVariantes,
    openCreateVariante,
    onEditVariante,
    resetVarianteDialog,
    onSubmitVariante,
    onDeleteVariante,
  }
}
