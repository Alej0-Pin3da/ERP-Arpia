<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { showToast } from '@/utils/toast'
import { getApiErrorDetail } from '@/utils/api-error'
import { createKit, type KitLineaCreate } from '@/services/api/kits'

export interface ProductoOpcion {
  id: number
  nombre: string
}

const props = defineProps<{
  visible: boolean
  productos: ProductoOpcion[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'creado'): void
}>()

const nombre = ref('')
const precioPromocional = ref<number>(0)
const lineas = ref<Array<{ producto_id: number | null; cantidad: number }>>([])
const productoSel = ref<number | null>(null)
const cantidadSel = ref<number>(1)
const guardando = ref(false)

function reset() {
  nombre.value = ''
  precioPromocional.value = 0
  lineas.value = []
  productoSel.value = null
  cantidadSel.value = 1
}

watch(() => props.visible, (v) => { if (v) reset() })

function agregarLinea() {
  if (productoSel.value == null) {
    showToast('warn', 'Sin producto', 'Elegí un producto del catálogo.')
    return
  }
  if (lineas.value.some((l) => l.producto_id === productoSel.value)) {
    showToast('warn', 'Duplicado', 'Ese producto ya está en la caja.')
    return
  }
  lineas.value.push({ producto_id: productoSel.value, cantidad: Math.max(1, Math.round(Number(cantidadSel.value) || 1)) })
  productoSel.value = null
  cantidadSel.value = 1
}

function quitarLinea(idx: number) {
  lineas.value.splice(idx, 1)
}

function nombreProducto(id: number | null): string {
  return props.productos.find((p) => p.id === id)?.nombre ?? `#${id}`
}

async function guardar() {
  if (!nombre.value.trim()) {
    showToast('warn', 'Sin nombre', 'Poné nombre a la caja (ej. Caja Promo Madre).')
    return
  }
  if (!lineas.value.length) {
    showToast('warn', 'Sin productos', 'Agregá al menos un producto a la caja.')
    return
  }
  guardando.value = true
  try {
    const payload: KitLineaCreate[] = lineas.value.map((l) => ({
      producto_id: l.producto_id as number,
      cantidad: l.cantidad,
    }))
    await createKit({ nombre: nombre.value.trim(), precio_promocional: precioPromocional.value, lineas: payload })
    showToast('success', 'Caja creada', `${nombre.value.trim()} guardada con ${payload.length} producto(s).`)
    emit('creado')
    emit('update:visible', false)
  } catch (e: unknown) {
    showToast('error', 'No se pudo crear', getApiErrorDetail(e, 'Revisá los datos e intentá de nuevo.'))
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <Dialog :visible="visible" modal header="Nueva Caja / Kit Promocional" class="w-[min(560px,94vw)]" @update:visible="emit('update:visible', $event)">
    <div class="space-y-4">
      <div>
        <label class="block text-[11px] text-stone-400 mb-1">Nombre de la caja</label>
        <InputText v-model="nombre" placeholder="Caja Promo Madre" class="w-full text-xs" />
      </div>
      <div>
        <label class="block text-[11px] text-stone-400 mb-1">Precio promocional final ($)</label>
        <InputNumber v-model="precioPromocional" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="0" class="w-full font-mono text-xs" />
        <p class="text-[10px] text-stone-500 m-0 mt-1">El servidor valida el margen mínimo del 5% y avisa si no se cumple (no bloquea).</p>
      </div>
      <div class="rounded-xl border border-stone-800 bg-stone-950/60 p-3 space-y-2">
        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-400">Productos de la caja ({{ lineas.length }})</div>
        <div class="flex items-end gap-2">
          <div class="flex-1">
            <Dropdown v-model="productoSel" :options="productos" option-label="nombre" option-value="id" placeholder="Elegí producto" class="w-full text-xs" filter />
          </div>
          <div class="w-24">
            <InputNumber v-model="cantidadSel" :min="1" class="w-full font-mono text-xs" />
          </div>
          <Button label="Añadir" size="small" class="text-xs" @click="agregarLinea" />
        </div>
        <div v-if="!lineas.length" class="text-[11px] text-stone-500">Todavía no hay productos.</div>
        <div v-for="(l, i) in lineas" :key="`${l.producto_id}-${i}`" class="flex items-center justify-between gap-2 text-xs text-stone-300">
          <span class="truncate">{{ nombreProducto(l.producto_id) }} <span class="text-stone-500">× {{ l.cantidad }}</span></span>
          <button type="button" class="px-2 py-1 rounded-lg bg-stone-800 text-stone-400 text-[11px] hover:bg-red-900/50 hover:text-red-300" @click="quitarLinea(i)">✕</button>
        </div>
      </div>
      <div class="flex justify-end gap-2">
        <Button label="Cancelar" severity="secondary" text size="small" @click="emit('update:visible', false)" />
        <Button label="Crear caja" icon="pi pi-save" size="small" :loading="guardando" @click="guardar" />
      </div>
    </div>
  </Dialog>
</template>
