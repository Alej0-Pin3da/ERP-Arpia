/**
 * Composable: BOM tab state for ProductosView.
 *
 * Owns BOM insumo lines + BOM producto (combo) lines, their loading,
 * dialogs, and CRUD actions for the BOM tab. Requires the shared
 * `productosLookup` and `insumos` refs (read only) from useProductosCatalog
 * for display joins; they are passed in at call time, not re-fetched here.
 */
import { computed, ref } from 'vue'

import { productosApi } from '@/api/endpoints'
import { serverDetail } from '@/utils/api'
import { confirmAction } from '@/utils/confirm'
import { buildBomInsumoRows, buildBomProductoRows } from '@/utils/productos'
import { showToast } from '@/utils/toast'
import type { BomInsumoPayloadInput, BomInsumoRow, BomProductoPayloadInput, BomProductoRow } from '@/utils/productos'
import type { BomInsumoRead, BomProductoRead, InsumoRead, ProductoRead } from '@/types/api.d'

export function useProductosBom(
  insumos: Readonly<{ value: InsumoRead[] }>,
  productosLookup: Readonly<{ value: ProductoRead[] }>,
) {
  const bomProductoId = ref<number | null>(null)
  const bomInsumos = ref<BomInsumoRead[]>([])
  const bomProductos = ref<BomProductoRead[]>([])
  const bomLoading = ref(false)
  const savingBomInsumo = ref(false)
  const savingBomProducto = ref(false)
  const editingBomInsumo = ref<BomInsumoRow | null>(null)
  const editingBomProducto = ref<BomProductoRow | null>(null)
  const bomInsumoDialogVisible = ref(false)
  const bomProductoDialogVisible = ref(false)

  const bomInsumoRows = computed(() => buildBomInsumoRows(bomInsumos.value, insumos.value))
  const bomProductoRows = computed(() => buildBomProductoRows(bomProductos.value, productosLookup.value))

  async function loadBom(productoId: number): Promise<void> {
    bomLoading.value = true
    try {
      const [insumosList, productosList] = await Promise.all([
        productosApi.listBomInsumos({ producto_id: productoId }),
        productosApi.listBomProductos({ producto_id: productoId }),
      ])
      bomInsumos.value = insumosList
      bomProductos.value = productosList
    } catch {
      showToast('error', 'No se pudo cargar la receta del producto.')
    } finally {
      bomLoading.value = false
    }
  }

  async function onSelectBomProducto(productoId: number): Promise<void> {
    bomProductoId.value = productoId
    editingBomInsumo.value = null
    editingBomProducto.value = null
    await loadBom(productoId)
  }

  // --- BOM Insumo CRUD -------------------------------------------------------

  function openCreateBomInsumo(): void {
    editingBomInsumo.value = null
    bomInsumoDialogVisible.value = true
  }

  function onEditBomInsumo(row: BomInsumoRow): void {
    editingBomInsumo.value = row
    bomInsumoDialogVisible.value = true
  }

  function resetBomInsumoDialog(): void {
    editingBomInsumo.value = null
  }

  async function onSubmitBomInsumo(payload: BomInsumoPayloadInput): Promise<void> {
    if (bomProductoId.value === null) return
    savingBomInsumo.value = true
    try {
      if (editingBomInsumo.value !== null) {
        await productosApi.updateBomInsumo(
          { producto_id: bomProductoId.value, linea_id: editingBomInsumo.value.id },
          payload,
        )
        showToast('success', 'Línea de BOM actualizada correctamente')
        editingBomInsumo.value = null
      } else {
        await productosApi.createBomInsumo({ producto_id: bomProductoId.value }, payload)
        showToast('success', 'Línea de BOM agregada correctamente')
      }
      bomInsumoDialogVisible.value = false
      await loadBom(bomProductoId.value)
    } catch (err) {
      showToast('error', serverDetail(err) ?? 'No se pudo guardar la línea de BOM.')
    } finally {
      savingBomInsumo.value = false
    }
  }

  async function onDeleteBomInsumo(row: BomInsumoRow): Promise<void> {
    if (bomProductoId.value === null) return
    const choice = await confirmAction({
      message: `¿Eliminar la línea de insumo "${row.insumo}"?`,
      header: 'Confirmar eliminación',
      acceptLabel: 'Eliminar',
      rejectLabel: 'Cancelar',
    })
    if (choice !== 'accept') return
    try {
      await productosApi.deleteBomInsumo({ producto_id: bomProductoId.value, linea_id: row.id })
      showToast('success', 'Línea de BOM eliminada correctamente')
      await loadBom(bomProductoId.value)
    } catch (err) {
      showToast('error', serverDetail(err) ?? 'No se pudo eliminar la línea de BOM.')
    }
  }

  // --- BOM Producto (combo) CRUD ---------------------------------------------

  function openCreateBomProducto(): void {
    editingBomProducto.value = null
    bomProductoDialogVisible.value = true
  }

  function onEditBomProducto(row: BomProductoRow): void {
    editingBomProducto.value = row
    bomProductoDialogVisible.value = true
  }

  function resetBomProductoDialog(): void {
    editingBomProducto.value = null
  }

  async function onSubmitBomProducto(payload: BomProductoPayloadInput): Promise<void> {
    if (bomProductoId.value === null) return
    savingBomProducto.value = true
    try {
      if (editingBomProducto.value !== null) {
        await productosApi.updateBomProducto(
          { producto_id: bomProductoId.value, linea_id: editingBomProducto.value.id },
          payload,
        )
        showToast('success', 'Línea de combo actualizada correctamente')
        editingBomProducto.value = null
      } else {
        await productosApi.createBomProducto({ producto_id: bomProductoId.value }, payload)
        showToast('success', 'Línea de combo agregada correctamente')
      }
      bomProductoDialogVisible.value = false
      await loadBom(bomProductoId.value)
    } catch (err) {
      showToast('error', serverDetail(err) ?? 'No se pudo guardar la línea de combo.')
    } finally {
      savingBomProducto.value = false
    }
  }

  async function onDeleteBomProducto(row: BomProductoRow): Promise<void> {
    if (bomProductoId.value === null) return
    const choice = await confirmAction({
      message: `¿Eliminar la línea de combo "${row.producto}"?`,
      header: 'Confirmar eliminación',
      acceptLabel: 'Eliminar',
      rejectLabel: 'Cancelar',
    })
    if (choice !== 'accept') return
    try {
      await productosApi.deleteBomProducto({ producto_id: bomProductoId.value, linea_id: row.id })
      showToast('success', 'Línea de combo eliminada correctamente')
      await loadBom(bomProductoId.value)
    } catch (err) {
      showToast('error', serverDetail(err) ?? 'No se pudo eliminar la línea de combo.')
    }
  }

  return {
    bomProductoId,
    bomInsumos,
    bomProductos,
    bomInsumoRows,
    bomProductoRows,
    bomLoading,
    savingBomInsumo,
    savingBomProducto,
    editingBomInsumo,
    editingBomProducto,
    bomInsumoDialogVisible,
    bomProductoDialogVisible,
    onSelectBomProducto,
    openCreateBomInsumo,
    onEditBomInsumo,
    resetBomInsumoDialog,
    onSubmitBomInsumo,
    onDeleteBomInsumo,
    openCreateBomProducto,
    onEditBomProducto,
    resetBomProductoDialog,
    onSubmitBomProducto,
    onDeleteBomProducto,
  }
}
