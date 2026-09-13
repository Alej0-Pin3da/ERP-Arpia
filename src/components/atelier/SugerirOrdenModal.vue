<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, ref, onMounted } from 'vue'
import * as comprasApi from '@/services/api/compras-insumos'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { useInsumos } from '@/composables/useInsumos'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const insumosApi = useInsumos()
const insumos = ref<any[]>([])
async function cargarInsumos() {
  try {
    const r = await insumosApi.list({ limit: 100 })
    insumos.value = (r as any).items ?? []
  } catch { insumos.value = [] }
}
onMounted(() => { void cargarInsumos() })
const criticos = computed(() => (insumos.value as any[]).filter((i:any)=>Number(i.stock_actual??i.stock??0)<=Number(i.stock_minimo??0)))

const totalSugerido = computed(() => {
  return criticos.value.reduce((sum, item) => {
    const deficit = Math.max(0, item.stock_minimo * 2 - item.stock_actual)
    // P0-4: en REAL la API manda costo_promedio_actual (Numeric → string), no costo_unitario
    return sum + (deficit * Number(item.costo_unitario ?? item.costo_promedio_actual ?? 0))
  }, 0)
})

async function generarOrden() {
  for (const item of criticos.value) {
    const deficit = Math.max(0, item.stock_minimo * 2 - item.stock_actual)
    if (deficit <= 0) continue
    try {
      await comprasApi.createCompraInsumo({
        insumo_id: item.id,
        cantidad_comprada: deficit,
        precio_unitario_compra: Number(item.costo_unitario ?? item.costo_promedio_actual ?? 0),
      })
    } catch (e) { /* continue */ }
  }
  void cargarInsumos()
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
        <div class="hidden overflow-x-auto max-h-72 overflow-y-auto sm:block">
        <table class="w-full min-w-[640px] text-left text-xs border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/50">
              <th class="py-2.5 px-3 sticky left-0 z-10 bg-stone-950/95 min-w-[180px]">Insumo / Proveedor</th>
              <th class="py-2.5 px-3 text-right whitespace-nowrap">Stock Actual</th>
              <th class="py-2.5 px-3 text-right whitespace-nowrap">Mínimo</th>
              <th class="py-2.5 px-3 text-right whitespace-nowrap">Sugerido</th>
              <th class="py-2.5 px-3 text-right whitespace-nowrap">Total Est.</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/50 text-stone-200">
            <tr v-for="it in criticos" :key="it.id" class="hover:bg-stone-800/30">
              <td class="py-2.5 px-3 sticky left-0 z-10 bg-stone-900/95 min-w-[180px]">
                <div class="font-medium text-stone-100">{{ it.nombre }}</div>
                <div class="text-[11px] text-stone-400">{{ it.proveedor ?? it.nombre_categoria ?? '—' }}</div>
              </td>
              <td class="py-2.5 px-3 text-right font-mono text-red-400 font-bold whitespace-nowrap">{{ it.stock_actual }} {{ it.unidad_medida }}</td>
              <td class="py-2.5 px-3 text-right font-mono text-stone-400 whitespace-nowrap">{{ it.stock_minimo }} {{ it.unidad_medida }}</td>
              <td class="py-2.5 px-3 text-right font-mono font-bold text-amber-300 whitespace-nowrap">
                +{{ (it.stock_minimo * 2 - it.stock_actual).toFixed(1) }} {{ it.unidad_medida }}
              </td>
              <td class="py-2.5 px-3 text-right font-mono font-bold whitespace-nowrap">
                ${{ Math.round((it.stock_minimo * 2 - it.stock_actual) * Number(it.costo_unitario ?? it.costo_promedio_actual ?? 0)).toLocaleString('es-CO') }}
              </td>
            </tr>
          </tbody>
        </table>
        </div>
        <!-- Mobile cards: same criticos. No horizontal scroll. -->
        <div class="space-y-3 p-3 sm:hidden max-w-full min-w-0">
          <div v-for="it in criticos" :key="it.id" class="border border-stone-800 rounded-2xl p-4 space-y-1 min-w-0">
            <div class="font-bold text-sm text-stone-100">{{ it.nombre }}</div>
            <div class="text-xs text-stone-400">{{ it.proveedor ?? it.nombre_categoria ?? '—' }}</div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Stock</span>
              <span class="font-mono font-bold text-red-400">{{ it.stock_actual }} {{ it.unidad_medida }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Sugerido</span>
              <span class="font-mono font-bold text-amber-300">+{{ (it.stock_minimo * 2 - it.stock_actual).toFixed(1) }} {{ it.unidad_medida }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Total est.</span>
              <span class="font-mono font-bold text-stone-100">${{ Math.round((it.stock_minimo * 2 - it.stock_actual) * Number(it.costo_unitario ?? it.costo_promedio_actual ?? 0)).toLocaleString('es-CO') }}</span>
            </div>
          </div>
        </div>
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
