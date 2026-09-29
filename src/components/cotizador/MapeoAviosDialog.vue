<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { showToast } from '@/utils/toast'
import { getApiErrorDetail } from '@/utils/api-error'
import { listInsumos } from '@/services/api/insumos'
import { createBomInsumo } from '@/services/api/bom'

const props = defineProps<{
  visible: boolean
  productoId: number | null
  montoAvios: number
  montoEmpaque: number
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'creado', lineas: number): void
}>()

interface OpcionInsumo {
  label: string
  value: number
  costo: number
  unidad: string
}

interface FilaMapeo {
  grupo: 'avios' | 'empaque'
  insumoId: number | null
  cantidad: number
  desperdicio: number
}

const opciones = ref<OpcionInsumo[]>([])
const cargandoMaestro = ref(false)
const filas = ref<FilaMapeo[]>([])
const grupoNueva = ref<'avios' | 'empaque'>('avios')
const guardando = ref(false)

function formatCOP(val: number): string {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

async function cargarMaestro(): Promise<void> {
  cargandoMaestro.value = true
  try {
    const r = await listInsumos({ limit: 500 })
    opciones.value = (r.items ?? []).map((i) => ({
      label: `${i.nombre} — $${Number(i.costo_promedio_actual ?? 0).toLocaleString('es-CO')}/${i.unidad_medida}`,
      value: i.id,
      costo: Number(i.costo_promedio_actual ?? 0),
      unidad: i.unidad_medida,
    }))
  } catch {
    opciones.value = []
  } finally {
    cargandoMaestro.value = false
  }
}

watch(() => props.visible, (v) => {
  if (v) {
    void cargarMaestro()
    if (!filas.value.length) agregarFila()
  }
})

function agregarFila(): void {
  filas.value.push({ grupo: grupoNueva.value, insumoId: null, cantidad: 1, desperdicio: 0 })
}

function quitarFila(idx: number): void {
  filas.value.splice(idx, 1)
}

function costoDe(insumoId: number | null): number {
  if (insumoId == null) return 0
  return opciones.value.find((o) => o.value === insumoId)?.costo ?? 0
}

function estimFila(f: FilaMapeo): number {
  return f.cantidad * (1 + f.desperdicio / 100) * costoDe(f.insumoId)
}

const totalAvios = computed(() => filas.value.filter((f) => f.grupo === 'avios').reduce((a, f) => a + estimFila(f), 0))
const totalEmpaque = computed(() => filas.value.filter((f) => f.grupo === 'empaque').reduce((a, f) => a + estimFila(f), 0))
const filasValidas = computed(() => filas.value.filter((f) => f.insumoId != null && f.cantidad > 0))

async function confirmar(): Promise<void> {
  if (props.productoId == null) {
    showToast('warn', 'Sin receta', 'Elegí una receta BOM para llevarle los herrajes.')
    return
  }
  if (!filasValidas.value.length) {
    showToast('warn', 'Sin filas', 'Elegí al menos un insumo real con cantidad mayor a 0.')
    return
  }
  guardando.value = true
  let ok = 0
  let fallos = 0
  for (const f of filasValidas.value) {
    try {
      await createBomInsumo(props.productoId, {
        insumo_id: f.insumoId as number,
        cantidad_requerida: f.cantidad,
        porcentaje_desperdicio: f.desperdicio,
        detalle: f.grupo === 'avios' ? 'Herrajes auditoría cotizador' : 'Empaque auditoría cotizador',
      })
      ok += 1
    } catch (e: unknown) {
      fallos += 1
      showToast('error', 'No se pudo crear una línea', getApiErrorDetail(e, 'Revisá el insumo e intentá de nuevo.'))
    }
  }
  guardando.value = false
  if (ok > 0) {
    showToast('success', 'Herrajes al BOM', `${ok} línea(s) creada(s) en la receta; el costo real ya las incluye.`)
    filas.value = []
    emit('creado', ok)
    emit('update:visible', false)
  }
  if (fallos > 0 && ok === 0) {
    showToast('error', 'Sin líneas creadas', 'Ninguna línea pudo guardarse; revisá la conexión.')
  }
}
</script>

<template>
  <Dialog :visible="visible" modal header="Llevar herrajes al BOM" class="w-[min(640px,94vw)]" @update:visible="emit('update:visible', $event)">
    <div class="space-y-4">
      <p class="text-[11px] text-stone-400 m-0">
        Elegí el insumo real del maestro por cada grupo y la cantidad que lleva la prenda.
        Cada fila crea una línea en el BOM de la receta (a precio del maestro, no al monto auditado).
        Referencia auditada: Herrajes {{ formatCOP(montoAvios) }} · Empaque {{ formatCOP(montoEmpaque) }}.
      </p>

      <div v-if="cargandoMaestro" class="text-xs text-stone-500">Cargando insumos del maestro...</div>

      <div v-else class="space-y-2">
        <div v-for="(f, i) in filas" :key="i" class="rounded-xl border border-stone-800 bg-stone-950/60 p-3 space-y-2">
          <div class="flex items-center justify-between gap-2">
            <div class="flex gap-1 text-[11px] font-bold">
              <button type="button" class="px-2 py-1 rounded-lg" :class="f.grupo === 'avios' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-stone-800 text-stone-400'" @click="f.grupo = 'avios'">Herrajes</button>
              <button type="button" class="px-2 py-1 rounded-lg" :class="f.grupo === 'empaque' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-stone-800 text-stone-400'" @click="f.grupo = 'empaque'">Empaque</button>
            </div>
            <button type="button" class="px-2 py-1 rounded-lg bg-stone-800 text-stone-400 text-[11px] hover:bg-red-900/50 hover:text-red-300" @click="quitarFila(i)">✕</button>
          </div>
          <Dropdown v-model="f.insumoId" :options="opciones" option-label="label" option-value="value" placeholder="Elegí insumo real del maestro" class="w-full text-xs" filter />
          <div class="flex items-end gap-2">
            <div class="flex-1">
              <label class="block text-[10px] text-stone-500 mb-1">Cantidad por prenda</label>
              <InputNumber v-model="f.cantidad" :min="0" class="w-full font-mono text-xs" />
            </div>
            <div class="w-24">
              <label class="block text-[10px] text-stone-500 mb-1">Merma %</label>
              <InputNumber v-model="f.desperdicio" :min="0" class="w-full font-mono text-xs" />
            </div>
            <div class="font-mono text-xs text-emerald-300 whitespace-nowrap">≈ {{ formatCOP(estimFila(f)) }}</div>
          </div>
        </div>
        <button type="button" class="px-3 py-1.5 rounded-lg bg-stone-800 text-stone-200 text-xs font-bold hover:bg-stone-700" @click="agregarFila">+ Agregar fila</button>
      </div>

      <div class="flex items-center justify-between text-xs border-t border-stone-800 pt-3">
        <span class="text-stone-400">Mapeado: Herrajes <strong class="text-stone-200 font-mono">{{ formatCOP(totalAvios) }}</strong> · Empaque <strong class="text-stone-200 font-mono">{{ formatCOP(totalEmpaque) }}</strong></span>
        <span class="text-stone-500 text-[10px]">No tiene que calzar al centavo: el BOM valoriza a precio del maestro.</span>
      </div>

      <div class="flex justify-end gap-2">
        <Button label="Cancelar" severity="secondary" text size="small" @click="emit('update:visible', false)" />
        <Button label="Crear líneas en el BOM" icon="pi pi-save" size="small" :loading="guardando" @click="confirmar" />
      </div>
    </div>
  </Dialog>
</template>
