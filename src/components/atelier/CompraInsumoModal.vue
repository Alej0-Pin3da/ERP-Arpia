<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import { useAtelierStore, type InsumoAtelier } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  insumo: InsumoAtelier | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const atelier = useAtelierStore()
const cantidad = ref(10)
const costoUnitario = ref(0)

watch(
  () => props.insumo,
  (val) => {
    if (val) {
      costoUnitario.value = val.costo_unitario
      cantidad.value = Math.max(5, val.stock_minimo * 2)
    }
  },
  { immediate: true },
)

function registrar() {
  if (!props.insumo) return
  atelier.agregarCompraInsumo(props.insumo.id, cantidad.value, costoUnitario.value)
  showToast('success', 'Compra registrada', `Se sumaron ${cantidad.value} ${props.insumo.unidad_medida} a ${props.insumo.nombre}.`)
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="insumo ? `📦 Registrar Compra • ${insumo.nombre}` : 'Registrar Compra'"
    :style="{ width: '90vw', maxWidth: '480px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div v-if="insumo" class="space-y-4 pt-1">
      <div class="bg-stone-900/80 border border-stone-800 rounded-xl p-3 text-xs space-y-1">
        <div class="flex justify-between text-stone-400">
          <span>Proveedor:</span> <strong class="text-stone-200">{{ insumo.proveedor }}</strong>
        </div>
        <div class="flex justify-between text-stone-400">
          <span>Stock Actual:</span> <strong class="text-amber-400">{{ insumo.stock_actual }} {{ insumo.unidad_medida }}</strong>
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Cantidad a Ingresar ({{ insumo.unidad_medida }})</label>
        <InputNumber v-model="cantidad" :min="0.1" :max-fraction-digits="2" class="w-full font-mono" />
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Costo Unitario Factura ($ COP)</label>
        <InputNumber v-model="costoUnitario" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
      </div>

      <div class="bg-stone-950/70 border border-stone-800 rounded-lg p-2.5 flex justify-between items-center text-xs">
        <span class="text-stone-400 uppercase font-bold">Total Factura:</span>
        <span class="font-mono text-sm font-bold text-amber-300">
          ${{ Math.round(cantidad * costoUnitario).toLocaleString('es-CO') }}
        </span>
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cancelar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button label="Registrar Entrada" icon="pi pi-check" class="p-button-warning font-semibold" @click="registrar" />
      </div>
    </div>
  </Dialog>
</template>
