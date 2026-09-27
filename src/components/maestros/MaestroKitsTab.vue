<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { showToast } from '@/utils/toast'
import { getApiErrorDetail } from '@/utils/api-error'
import { useProductos } from '@/composables/useProductos'
import {
  addKitLinea,
  removeKitLinea,
  updateKit,
  type KitRead,
} from '@/services/api/kits'
import NuevoKitModal from './NuevoKitModal.vue'

defineProps<{
  kits: KitRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', target: { tipo: string; id: number; nombre: string }): void
}>()

const productosApi = useProductos()
const productosOptions = ref<Array<{ id: number; nombre: string }>>([])
const showNuevo = ref(false)
const precioEdit = ref<Record<number, number>>({})
const lineaProductoSel = ref<Record<number, number | null>>({})
const lineaCantidad = ref<Record<number, number>>({})

async function cargarProductos() {
  try {
    const r = await productosApi.list({ limit: 200 })
    productosOptions.value = (r.items ?? []).map((p) => ({ id: p.id, nombre: p.nombre }))
  } catch { productosOptions.value = [] }
}

onMounted(() => { void cargarProductos() })

function formatCOP(val: number | string): string {
  return `$${Math.round(Number(val ?? 0)).toLocaleString('es-CO')}`
}

function margenBadge(k: KitRead): string {
  if (!k.lineas.length) return 'text-stone-400 border-stone-700'
  return k.alerta_margen
    ? 'text-red-300 border-red-500/40 bg-red-500/10'
    : 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10'
}

async function guardarPrecio(k: KitRead) {
  const v = precioEdit.value[k.id]
  if (v == null) return
  try {
    await updateKit(k.id, { precio_promocional: v })
    showToast('success', 'Precio actualizado', `${k.nombre} → ${formatCOP(v)}.`)
    emit('actualizado')
  } catch (e: unknown) {
    showToast('error', 'No se pudo actualizar', getApiErrorDetail(e, 'Revisá el precio e intentá de nuevo.'))
  }
}

async function agregarLinea(k: KitRead) {
  const pid = lineaProductoSel.value[k.id]
  if (pid == null) {
    showToast('warn', 'Sin producto', 'Elegí un producto para sumar a la caja.')
    return
  }
  try {
    await addKitLinea(k.id, { producto_id: pid, cantidad: Math.max(1, Math.round(Number(lineaCantidad.value[k.id] ?? 1))) })
    showToast('success', 'Línea agregada', 'El costo y el margen se recalcularon.')
    lineaProductoSel.value[k.id] = null
    emit('actualizado')
  } catch (e: unknown) {
    showToast('error', 'No se pudo agregar', getApiErrorDetail(e, '¿Producto duplicado?'))
  }
}

async function quitarLinea(k: KitRead, lineaId: number) {
  try {
    await removeKitLinea(k.id, lineaId)
    showToast('info', 'Línea quitada', 'El costo y el margen se recalcularon.')
    emit('actualizado')
  } catch (e: unknown) {
    showToast('error', 'No se pudo quitar', getApiErrorDetail(e, 'Revisá la conexión.'))
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="text-xs text-stone-400">{{ kits.length }} caja(s) promocionales · el costo es en vivo, el margen alerta bajo 5%</div>
      <Button label="Nueva caja" icon="pi pi-plus" size="small" class="text-xs" @click="showNuevo = true" />
    </div>

    <div v-if="!kits.length" class="text-xs text-stone-500 rounded-xl border border-stone-800 bg-stone-950/60 p-4">
      Todavía no hay cajas. Creá la primera para campañas promocionales.
    </div>

    <div v-for="k in kits" :key="k.id" class="rounded-2xl border border-stone-800 bg-stone-900/80 p-4 space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2 min-w-0">
          <span class="font-bold text-sm text-stone-100 truncate">{{ k.nombre }}</span>
          <span v-if="!k.activo" class="px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase text-stone-500 border-stone-700">inactiva</span>
          <span class="px-2 py-0.5 rounded-full border text-[10px] font-bold" :class="margenBadge(k)">
            {{ !k.lineas.length ? 'sin productos' : k.alerta_margen ? `⚠ margen ${Number(k.margen_pct)}%` : `margen ${Number(k.margen_pct)}%` }}
          </span>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <span class="font-mono text-stone-400">costo {{ formatCOP(k.costo_total) }}</span>
          <span class="font-mono font-bold text-amber-300">{{ formatCOP(k.precio_promocional) }}</span>
          <button type="button" class="px-2 py-1 rounded-lg bg-stone-800 text-stone-400 text-[11px] hover:bg-red-900/50 hover:text-red-300" @click="emit('solicitar-eliminar', { tipo: 'kit', id: k.id, nombre: k.nombre })">Eliminar</button>
        </div>
      </div>

      <div v-if="k.lineas.length" class="overflow-x-auto">
        <table class="w-full text-[11px] text-stone-300 border-collapse">
          <thead>
            <tr class="text-stone-500 uppercase tracking-wider text-[10px] text-left">
              <th class="py-1 pr-2">Producto</th>
              <th class="py-1 pr-2 text-right">Cant.</th>
              <th class="py-1 pr-2 text-right">Costo U.</th>
              <th class="py-1 pr-2 text-right">Subtotal</th>
              <th class="py-1 text-right"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in k.lineas" :key="l.id" class="border-t border-stone-800/60">
              <td class="py-1 pr-2 truncate max-w-[220px]">{{ l.producto_nombre ?? `#${l.producto_id}` }}</td>
              <td class="py-1 pr-2 font-mono text-right">× {{ Number(l.cantidad) }}</td>
              <td class="py-1 pr-2 font-mono text-right">{{ formatCOP(l.costo_unitario) }}</td>
              <td class="py-1 pr-2 font-mono text-right">{{ formatCOP(l.subtotal) }}</td>
              <td class="py-1 text-right"><button type="button" class="text-stone-500 hover:text-red-300 text-xs" @click="quitarLinea(k, l.id)">✕</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-[11px] text-stone-500">Sin productos: sumá líneas abajo.</div>

      <div class="flex flex-wrap items-end gap-2 rounded-xl border border-stone-800/70 bg-stone-950/40 p-2">
        <div class="flex-1 min-w-[180px]">
          <Dropdown v-model="lineaProductoSel[k.id]" :options="productosOptions" option-label="nombre" option-value="id" placeholder="Sumar producto..." class="w-full text-xs" filter />
        </div>
        <div class="w-20">
          <InputNumber v-model="lineaCantidad[k.id]" :min="1" placeholder="Cant." class="w-full font-mono text-xs" />
        </div>
        <Button label="Sumar" size="small" class="text-xs" @click="agregarLinea(k)" />
        <div class="flex items-center gap-1 ml-auto">
          <InputNumber v-model="precioEdit[k.id]" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="0" :placeholder="`Promo ${formatCOP(k.precio_promocional)}`" class="w-36 font-mono text-xs" />
          <Button label="Precio" size="small" severity="secondary" class="text-xs" @click="guardarPrecio(k)" />
        </div>
      </div>
    </div>

    <NuevoKitModal :visible="showNuevo" :productos="productosOptions" @update:visible="showNuevo = $event" @creado="emit('actualizado')" />
  </div>
</template>
