<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { useInsumos } from '@/composables/useInsumos'
import { useProduccion } from '@/composables/useProduccion'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'ir-insumos'): void
}>()

interface Alerta {
  id: string
  titulo: string
  detalle: string
  tono: 'critico' | 'info'
}

const alertas = ref<Alerta[]>([])
const cargando = ref(false)
const sinDatos = ref(false)

async function cargarAlertas() {
  cargando.value = true
  sinDatos.value = false
  try {
    const insumosApi = useInsumos()
    const produccionApi = useProduccion()
    const [ir, pr] = await Promise.all([
      insumosApi.list({ limit: 100 }),
      produccionApi.list({ limit: 100 }),
    ])
    const items: Alerta[] = []
    const insumos = ((ir as unknown as { items?: unknown[] }).items ?? []) as Record<string, unknown>[]
    for (const i of insumos) {
      const stock = Number(i.stock_actual ?? i.stock ?? 0)
      const minimo = Number(i.stock_minimo ?? 0)
      if (stock <= minimo) {
        items.push({
          id: `ins-${String(i.id)}`,
          titulo: `Stock Crítico: ${String(i.nombre ?? '—')}`,
          detalle: `Quedan ${stock} ${String(i.unidad_medida ?? '')} disponibles y el mínimo es de ${minimo}.`,
          tono: 'critico',
        })
      }
    }
    const pedidos = ((pr as unknown as { items?: unknown[] }).items ?? []) as Record<string, unknown>[]
    for (const p of pedidos.slice(0, 5)) {
      items.push({
        id: `ped-${String(p.id)}`,
        titulo: `Orden ORD-${String(p.id)} — ${String(p.estado ?? '—')}`,
        detalle: `${String(p.nombre_producto ?? p.nombre_variante ?? '—')}`,
        tono: 'info',
      })
    }
    alertas.value = items
    sinDatos.value = items.length === 0
  } catch {
    // Sin backend disponible: estado vacío, nunca tarjetas inventadas.
    alertas.value = []
    sinDatos.value = true
  } finally {
    cargando.value = false
  }
}

watch(() => props.visible, (v) => { if (v) void cargarAlertas() })
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="🔔 Notificaciones de Operaciones"
    :style="{ width: '90vw', maxWidth: '480px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-3 pt-1">
      <div v-if="cargando" class="text-center py-6 text-xs text-stone-500">Cargando alertas…</div>
      <div v-else-if="sinDatos || !alertas.length" class="text-center py-6 text-xs text-stone-500 border border-stone-800 rounded-xl">
        Sin registro — pendiente: no hay alertas de inventario o producción disponibles.
      </div>
      <div
        v-for="a in alertas"
        :key="a.id"
        class="bg-stone-900/80 border rounded-xl p-3 text-xs flex items-start gap-3"
        :class="a.tono === 'critico' ? 'border-amber-500/30' : 'border-stone-800'"
      >
        <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 font-bold" :class="a.tono === 'critico' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'">
          {{ a.tono === 'critico' ? '⚠️' : '✂️' }}
        </div>
        <div class="space-y-1">
          <div class="font-bold text-stone-100">{{ a.titulo }}</div>
          <div class="text-stone-400 leading-relaxed">{{ a.detalle }}</div>
          <button
            v-if="a.tono === 'critico'"
            type="button"
            class="text-amber-400 hover:underline font-bold text-[11px] pt-1 block"
            @click="emit('ir-insumos'); emit('update:visible', false)"
          >
            Ver en Inventario →
          </button>
        </div>
      </div>

      <div class="flex justify-end pt-2">
        <Button label="Entendido" severity="secondary" size="small" @click="emit('update:visible', false)" />
      </div>
    </div>
  </Dialog>
</template>
