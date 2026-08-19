/**
 * Composable: Costo tab state for ProductosView.
 *
 * Owns the producto/variante selectors, the cost tree loading and result state
 * for the Costo tab. Read-only: no mutations — only fetches the cost breakdown.
 */
import { ref } from 'vue'

import { productosApi } from '@/api/endpoints'
import { buildCostoTree } from '@/utils/productos'
import { showToast } from '@/utils/toast'
import type { CostoTree } from '@/utils/productos'
import type { CostoProduccionRead, VarianteProductoRead } from '@/types/api.d'

export function useProductosCosto() {
  const costoProductoId = ref<number | null>(null)
  const costoVarianteId = ref<number | null>(null)
  const costoProductoVariantes = ref<VarianteProductoRead[]>([])
  const costoTree = ref<CostoTree | null>(null)
  const costoLoading = ref(false)

  async function loadCostoVariantes(productoId: number): Promise<void> {
    try {
      costoProductoVariantes.value = await productosApi.listVariantes({ producto_id: productoId })
    } catch {
      costoProductoVariantes.value = []
    }
  }

  async function loadCosto(): Promise<void> {
    if (costoProductoId.value === null) return
    costoLoading.value = true
    try {
      const costo: CostoProduccionRead = await productosApi.costo(
        { producto_id: costoProductoId.value },
        costoVarianteId.value === null ? undefined : { variante_id: costoVarianteId.value },
      )
      costoTree.value = buildCostoTree(costo)
    } catch {
      costoTree.value = null
      showToast('error', 'No se pudo calcular el costo de producción.')
    } finally {
      costoLoading.value = false
    }
  }

  async function onSelectCostoProducto(productoId: number): Promise<void> {
    costoProductoId.value = productoId
    costoVarianteId.value = null
    costoTree.value = null
    await loadCostoVariantes(productoId)
    await loadCosto()
  }

  function onCostoVarianteChange(): void {
    void loadCosto()
  }

  return {
    costoProductoId,
    costoVarianteId,
    costoProductoVariantes,
    costoTree,
    costoLoading,
    onSelectCostoProducto,
    onCostoVarianteChange,
  }
}
