/* eslint-disable @typescript-eslint/no-explicit-any */
<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import * as comprasApi from '@/services/api/compras-insumos'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { useInsumos } from '@/composables/useInsumos'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const insumosApi = useInsumos()
const insumosRealList = ref<any[]>([])
async function cargarInsumosSugerir() {
  if (isMock.value) return
  try {
    const r = await insumosApi.list({ limit: 100 })
    insumosRealList.value = (r as any).items ?? []
  } catch { insumosRealList.value = [] }
}
onMounted(() => { void cargarInsumosSugerir() })
watch(isMock, () => { void cargarInsumosSugerir() })
const criticosReal = computed(() => (insumosRealList.value as any[]).filter((i:any)=>(i.stock_actual??i.stock??0)<=(i.stock_minimo??0)))

const criticos = computed(() => isMock.value ? atelier.insumosCriticos : (criticosReal.value as any))

const totalSugerido = computed(() => {
  return criticos.value.reduce((sum, item) => {
    const deficit = Math.max(0, item.stock_minimo * 2 - item.stock_actual)
    return sum + (deficit * item.costo_unitario)
  }, 0)
})

async function generarOrden() {
  if (isMock.value) {
    criticos.value.forEach((item) => {
      const deficit = Math.max(0, item.stock_minimo * 2 - item.stock_actual)
      atelier.agregarCompraInsumo(item.id, deficit)
    })
  } else {
    for (const item of criticos.value) {
      const deficit = Math.max(0, item.stock_minimo * 2 - item.stock_actual)
      if (deficit <= 0) continue
      try {
        await comprasApi.createCompraInsumo({
          insumo_id: item.id,
          cantidad_comprada: deficit,
          precio_unitario_compra: item.costo_unitario ?? item.costo_promedio_actual ?? 0,
        })
      } catch (e) { /* continue */ }
    }
    void cargarInsumosSugerir()
  }
  showToast('success', 'Orden de Compra Procesada', 'Se ha reabastecido el stock de los insumos críticos sugeridos.')
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="📦 Sugerir Orden de Compra de Insumos"
    :style="{ width: '90vw', maxWidth: '640px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div class="bg-amber-950/20 border border-amber-500/20 rounded-xl p-3 text-xs text-amber-200/90 flex items-start gap-2">
        <i class="pi pi-exclamation-triangle text-amber-400 text-base flex-shrink-0 mt-0.5" />
        <span>Se han detectado <strong>{{ criticos.length }} materias primas</strong> por debajo del stock mínimo de seguridad del atelier.</span>
      </div>

      <div class="border border-stone-800 rounded-xl overflow-hidden bg-stone-900/50">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/50">
              <th class="py-2.5 px-3">Insumo / Proveedor</th>
              <th class="py-2.5 px-3 text-right">Stock Actual</th>
              <th class="py-2.5 px-3 text-right">Mínimo</th>
              <th class="py-2.5 px-3 text-right">Sugerido</th>
              <th class="py-2.5 px-3 text-right">Total Est.</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/50 text-stone-200">
            <tr v-for="it in criticos" :key="it.id" class="hover:bg-stone-800/30">
              <td class="py-2.5 px-3">
                <div class="font-medium text-stone-100">{{ it.nombre }}</div>
                <div class="text-[11px] text-stone-400">{{ it.proveedor }}</div>
              </td>
              <td class="py-2.5 px-3 text-right font-mono text-red-400 font-bold">{{ it.stock_actual }} {{ it.unidad_medida }}</td>
              <td class="py-2.5 px-3 text-right font-mono text-stone-400">{{ it.stock_minimo }} {{ it.unidad_medida }}</td>
              <td class="py-2.5 px-3 text-right font-mono font-bold text-amber-300">
                +{{ (it.stock_minimo * 2 - it.stock_actual).toFixed(1) }} {{ it.unidad_medida }}
              </td>
              <td class="py-2.5 px-3 text-right font-mono font-bold">
                ${{ Math.round((it.stock_minimo * 2 - it.stock_actual) * it.costo_unitario).toLocaleString('es-CO') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex justify-between items-center bg-stone-950/80 border border-stone-800 rounded-xl p-3 text-xs">
        <span class="text-stone-400 uppercase font-bold">Inversión Estimada en Reposición:</span>
        <span class="font-mono text-base font-extrabold text-amber-300">${{ Math.round(totalSugerido).toLocaleString('es-CO') }}</span>
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cerrar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button label="Generar Orden de Compra" icon="pi pi-shopping-cart" class="p-button-warning font-semibold" @click="generarOrden" />
      </div>
    </div>
  </Dialog>
</template>
