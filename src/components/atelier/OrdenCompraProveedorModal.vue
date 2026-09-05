<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { useInsumos } from '@/composables/useInsumos'
import * as comprasApi from '@/services/api/compras-insumos'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const insumosApi = useInsumos()
const guardando = ref(false)

const proveedorSeleccionado = ref<string>('Todos los Proveedores')
const proveedores = computed(() => {
  const set = new Set(itemsPedido.value.map((i) => i.proveedor).filter(Boolean))
  return ['Todos los Proveedores', ...Array.from(set)]
})

interface ItemCompra {
  id: number
  codigo: string
  nombre: string
  proveedor: string
  stock_actual: number
  stock_minimo: number
  unidad_medida: string
  costo_unitario: number
  cantidad_pedir: number
}

const itemsPedido = ref<ItemCompra[]>([])

async function inicializarItems() {
  if (isMock.value) {
    itemsPedido.value = (atelier.insumos as any[])
      .filter((i) => i.stock_actual <= i.stock_minimo * 1.5)
      .map((i) => ({
        id: i.id,
        codigo: i.codigo,
        nombre: i.nombre,
        proveedor: i.proveedor,
        stock_actual: i.stock_actual,
        stock_minimo: i.stock_minimo,
        unidad_medida: i.unidad_medida,
        costo_unitario: i.costo_unitario,
        cantidad_pedir: Math.max(10, Math.ceil(i.stock_minimo * 2 - i.stock_actual)),
      }))
    return
  }
  try {
    const r = await insumosApi.list({ limit: 100 })
    itemsPedido.value = ((r as any).items ?? [])
      .filter((i: any) => Number(i.stock_actual ?? 0) <= Number(i.stock_minimo ?? 0) * 1.5)
      .map((i: any) => ({
        id: i.id,
        codigo: i.codigo || `INS-${i.id}`,
        nombre: i.nombre,
        // InsumoRead no trae proveedor: se muestra la categoría.
        proveedor: (i as any).proveedor ?? i.nombre_categoria ?? '—',
        stock_actual: Number(i.stock_actual ?? 0),
        stock_minimo: Number(i.stock_minimo ?? 0),
        unidad_medida: i.unidad_medida,
        costo_unitario: Number(i.costo_promedio_actual ?? 0),
        cantidad_pedir: Math.max(10, Math.ceil(Number(i.stock_minimo ?? 0) * 2 - Number(i.stock_actual ?? 0))),
      }))
  } catch { itemsPedido.value = [] }
}

// Initialize whenever modal opens
watch(
  () => props.visible,
  (val) => {
    if (val) void inicializarItems()
  }
)

const itemsFiltrados = computed(() => {
  if (proveedorSeleccionado.value === 'Todos los Proveedores') {
    return itemsPedido.value
  }
  return itemsPedido.value.filter((i) => i.proveedor === proveedorSeleccionado.value)
})

const totalPresupuesto = computed(() => {
  return itemsFiltrados.value.reduce((acc, item) => acc + item.cantidad_pedir * item.costo_unitario, 0)
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

async function abastecerInventario() {
  if (isMock.value) {
    itemsFiltrados.value.forEach((item) => {
      const insumo = (atelier.insumos as any[]).find((i) => i.id === item.id)
      if (insumo) {
        insumo.stock_actual += item.cantidad_pedir
        insumo.valor_total = insumo.stock_actual * insumo.costo_unitario
      }
    })

    showToast(
      'success',
      'Orden de Compra Procesada',
      `Se abastecieron ${itemsFiltrados.value.length} insumos por un total de ${formatCOP(totalPresupuesto.value)}.`
    )
    emit('update:visible', false)
    return
  }
  const filas = itemsFiltrados.value.filter((item) => Number(item.cantidad_pedir) > 0)
  if (!filas.length) {
    showToast('warn', 'Sin cantidades', 'Indicá al menos una cantidad a pedir mayor a 0.')
    return
  }
  guardando.value = true
  let ok = 0
  let ultimoError = ''
  for (const item of filas) {
    try {
      await comprasApi.createCompraInsumo({
        insumo_id: item.id,
        cantidad_comprada: Number(item.cantidad_pedir),
        precio_unitario_compra: Number(item.costo_unitario) || 0,
      })
      ok++
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      ultimoError = typeof detail === 'string' ? detail : 'Error al registrar compra'
    }
  }
  guardando.value = false
  if (ok > 0) {
    showToast(
      'success',
      'Orden de Compra Procesada',
      `Se abastecieron ${ok}/${filas.length} insumos por un total de ${formatCOP(totalPresupuesto.value)}.${ok < filas.length ? ` Último error: ${ultimoError}` : ''}`
    )
    emit('update:visible', false)
  } else {
    showToast('error', 'No se pudo abastecer', ultimoError || 'Revisá los datos e intentá de nuevo.')
  }
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    modal
    header="Generador de Órdenes de Compra a Proveedores Textil"
    :style="{ width: '820px', maxWidth: '95vw' }"
    class="p-dialog-arpia"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="space-y-5 pt-1">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-stone-900 border border-stone-800">
        <div>
          <div class="text-xs font-mono font-bold text-amber-400 uppercase">
            Insumos Críticos & Sugerencias de Reposición
          </div>
          <div class="text-xs text-stone-300 mt-0.5">
            Cálculo automático de pedido para alcanzar el doble del stock de seguridad.
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-stone-400 font-mono">Filtrar por:</span>
          <Dropdown
            v-model="proveedorSeleccionado"
            :options="proveedores"
            class="text-xs w-48"
          />
        </div>
      </div>

      <!-- Materials List -->
      <div class="overflow-x-auto border border-stone-800 rounded-xl bg-stone-950/60 max-h-72 overflow-y-auto">
        <table class="w-full text-xs text-left border-collapse">
          <thead>
            <tr class="border-b border-stone-800 bg-stone-900/80 text-stone-400 font-mono uppercase text-[11px] sticky top-0 z-10">
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Insumo Textil</th>
              <th class="py-2.5 px-3">Proveedor</th>
              <th class="py-2.5 px-3">Stock Actual</th>
              <th class="py-2.5 px-3">Cant. a Pedir</th>
              <th class="py-2.5 px-3 text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60 font-mono">
            <tr v-for="item in itemsFiltrados" :key="item.id" class="hover:bg-stone-900/40">
              <td class="py-2.5 px-3 text-amber-400 font-bold">{{ item.codigo }}</td>
              <td class="py-2.5 px-3 text-stone-200 font-sans font-medium">{{ item.nombre }}</td>
              <td class="py-2.5 px-3 text-stone-400">{{ item.proveedor }}</td>
              <td class="py-2.5 px-3">
                <span :class="item.stock_actual <= item.stock_minimo ? 'text-red-400 font-bold' : 'text-amber-300'">
                  {{ item.stock_actual }} {{ item.unidad_medida }}
                </span>
                <span class="text-[10px] text-stone-500 block">mín: {{ item.stock_minimo }}</span>
              </td>
              <td class="py-2.5 px-3 w-32">
                <InputNumber
                  v-model="item.cantidad_pedir"
                  :min="1"
                  :suffix="` ${item.unidad_medida}`"
                  class="w-full text-xs"
                />
              </td>
              <td class="py-2.5 px-3 text-right text-stone-200 font-bold">
                {{ formatCOP(item.cantidad_pedir * item.costo_unitario) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Financial Total Bar -->
      <div class="flex items-center justify-between p-4 rounded-xl bg-amber-950/30 border border-amber-500/30">
        <div>
          <div class="text-[11px] text-stone-400 font-mono uppercase">Presupuesto Estimado de Compra:</div>
          <div class="text-xl font-serif font-bold text-amber-300">{{ formatCOP(totalPresupuesto) }}</div>
        </div>
        <div class="text-xs font-mono text-stone-400">
          {{ itemsFiltrados.length }} insumos seleccionados
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full pt-3 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          severity="secondary"
          outlined
          class="text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          label="Confirmar Abastecimiento a Taller"
          icon="pi pi-check-circle"
          size="small"
          class="p-button-warning text-xs font-semibold"
          :loading="guardando"
          @click="abastecerInventario"
        />
      </div>
    </template>
  </Dialog>
</template>
