<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, onMounted, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { useProductos } from '@/composables/useProductos'
import { usePrendas } from '@/composables/usePrendas'
import { client } from '@/api/client'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'prenda-ingresada'): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const productosApi = useProductos()
const prendasApi = usePrendas()

const productoId = ref<number | null>(null)
const varianteId = ref<number | null>(null)
const tallaMock = ref<string>('Sin talla')
const cantidad = ref<number>(1)
const costoReal = ref<number>(0)
const precioVenta = ref<number>(0)
const estado = ref<string>('disponible')
const ubicacion = ref<string>('Showroom')
const guardando = ref(false)

const productosReal = ref<any[]>([])
const variantesReal = ref<{ id: number; nombre_variante: string }[]>([])

async function cargarProductos() {
  if (isMock.value) return
  try {
    const r = await productosApi.list({ limit: 100 })
    productosReal.value = (r.items as any) ?? []
  } catch { productosReal.value = [] }
}
onMounted(() => { void cargarProductos() })
watch(isMock, () => { void cargarProductos() })

const productosOptions = computed(() => {
  const src = isMock.value ? (atelier as any).recetas : productosReal.value
  return (src as any[]).map((p) => ({
    label: `${p.nombre} (${p.codigo ?? `PRD-${p.id}`})`,
    value: p.id,
  }))
})

const variantesOptions = computed(() => [
  { label: 'Sin talla (genérica)', value: null },
  ...variantesReal.value.map((v) => ({ label: v.nombre_variante, value: v.id })),
])

const estadosOptions = [
  { label: 'Disponible (perchero)', value: 'disponible' },
  { label: 'Reservada (pedido)', value: 'reservada' },
  { label: 'Vendida', value: 'vendida' },
  { label: 'Defectuosa', value: 'defectuosa' },
]

const tallasMockOptions = ['Sin talla', 'XXS', 'XS', 'S', 'M', 'L', 'XL'].map((t) => ({ label: t, value: t }))

async function onProductoChange() {
  varianteId.value = null
  variantesReal.value = []
  if (productoId.value == null) return
  const src = isMock.value ? (atelier as any).recetas : productosReal.value
  const p = (src as any[]).find((x) => x.id === productoId.value)
  if (p) {
    const pv = Number(p.precio_venta_sugerido ?? p.precio_venta ?? 0)
    if (Number.isFinite(pv) && pv > 0) precioVenta.value = Math.round(pv)
    const ct = Number(p.costo_total_unitario ?? p.costos_operativos_fijos ?? p.costo_insumos ?? 0)
    if (Number.isFinite(ct) && ct > 0) costoReal.value = Math.round(ct)
  }
  if (!isMock.value) {
    try {
      const { data } = await client.get<{ id: number; nombre_variante: string }[]>(`/productos/${productoId.value}/variantes`)
      variantesReal.value = data ?? []
    } catch { variantesReal.value = [] }
  }
}

function resetForm() {
  productoId.value = null
  varianteId.value = null
  tallaMock.value = 'Sin talla'
  cantidad.value = 1
  costoReal.value = 0
  precioVenta.value = 0
  estado.value = 'disponible'
  ubicacion.value = 'Showroom'
}

async function guardar() {
  if (productoId.value == null) {
    showToast('warn', 'Seleccioná un modelo', 'Elegí el modelo del catálogo para registrar sus unidades al perchero.')
    return
  }
  const n = Math.max(1, Math.round(Number(cantidad.value) || 1))
  guardando.value = true
  try {
    for (let i = 0; i < n; i++) {
      await prendasApi.create({
        variante_id: isMock.value ? null : varianteId.value,
        talla: isMock.value ? (tallaMock.value === 'Sin talla' ? null : tallaMock.value) : undefined,
        estado: estado.value,
        ubicacion: ubicacion.value.trim() || null,
        costo_real: Number(costoReal.value) || 0,
        precio_venta: Number(precioVenta.value) || 0,
      })
    }
    showToast('success', 'Prenda ingresada', `${n} unidad(es) del modelo registradas en estado ${estado.value}.`)
    emit('prenda-ingresada')
    emit('update:visible', false)
    resetForm()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    showToast('error', 'No se pudo ingresar', typeof detail === 'string' ? detail : 'Revisá los datos e intentá de nuevo.')
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="👗 Ingresar Prenda Confeccionada al Perchero"
    :style="{ width: '90vw', maxWidth: '520px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Modelo del catálogo *</label>
        <Dropdown
          v-model="productoId"
          :options="productosOptions"
          option-label="label"
          option-value="value"
          placeholder="Seleccionar modelo para registrar unidades..."
          class="w-full"
          @change="onProductoChange"
        />
      </div>

      <div v-if="!isMock">
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Variante / Talla</label>
        <Dropdown
          v-model="varianteId"
          :options="variantesOptions"
          option-label="label"
          option-value="value"
          placeholder="Sin talla (genérica)"
          class="w-full"
        />
      </div>
      <div v-else>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Talla</label>
        <Dropdown
          v-model="tallaMock"
          :options="tallasMockOptions"
          option-label="label"
          option-value="value"
          class="w-full"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Unidades</label>
          <InputNumber v-model="cantidad" :min="1" :max-fraction-digits="0" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Ubicación</label>
          <InputText v-model="ubicacion" placeholder="Showroom" class="w-full" />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Costo Real ($ COP)</label>
          <InputNumber v-model="costoReal" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Precio Venta ($ COP)</label>
          <InputNumber v-model="precioVenta" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Estado inicial</label>
        <Dropdown v-model="estado" :options="estadosOptions" option-label="label" option-value="value" class="w-full" />
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cancelar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button label="Ingresar al Perchero" icon="pi pi-check" class="p-button-warning font-semibold" :loading="guardando" @click="guardar" />
      </div>
    </div>
  </Dialog>
</template>
