<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import { useMode } from '@/composables/useMode'
import { useOmisiones } from '@/composables/useOmisiones'
import { showToast } from '@/utils/toast'

const { isMock } = useMode()
const omisionesApi = useOmisiones()
const omisiones = ref<any[]>([
  {
    id: 1,
    fecha: '2026-08-20 14:30',
    usuario: 'Camila Modista',
    evento: 'Descuento manual de merma en encaje Chantilly por falla de estiramiento',
    impacto: '-0.35m Tela',
  },
  {
    id: 2,
    fecha: '2026-08-18 10:15',
    usuario: 'Valeria Arpía',
    evento: 'Ajuste de precio de cotización especial para clienta VIP',
    impacto: 'Descuento $40.000 COP',
  },
])

const omisionesReal = ref<any[]>([])
async function cargarOmisionesReales() {
  if (isMock.value) return
  try {
    const r = await omisionesApi.list({ limit: 100 })
    omisionesReal.value = (r as any).items ?? []
  } catch { omisionesReal.value = [] }
}
onMounted(() => { void cargarOmisionesReales() })
watch(isMock, () => { void cargarOmisionesReales() })
const omisionesDisplay = computed(() => isMock.value ? omisiones.value : (omisionesReal.value.length ? omisionesReal.value.map((o: any) => ({
  id: o.id,
  fecha: o.creado_en || '',
  usuario: o.hoja || 'Sistema',
  evento: o.mensaje || o.fase || 'Omisión',
  impacto: o.nivel || '',
  resuelta: Boolean(o.resuelta),
})) : []))

const resolviendoId = ref<number | null>(null)

async function marcarResuelta(o: { id: number }) {
  resolviendoId.value = o.id
  try {
    await omisionesApi.resolve(o.id, true)
    showToast('success', 'Omisión resuelta', `Omisión #${o.id} marcada como resuelta.`)
    await cargarOmisionesReales()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    showToast('error', 'No se pudo resolver', typeof detail === 'string' ? detail : 'Revisá permisos (solo admin) e intentá de nuevo.')
  } finally {
    resolviendoId.value = null
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Bitácora de Omisiones & Ajustes Especiales
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Registro auditable de modificaciones de merma, excepciones en precios y cambios de patrón.
      </p>
    </div>

    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4 overflow-hidden">
      <div class="hidden overflow-x-auto md:block">
      <table class="w-full min-w-[640px] text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3 sticky left-0 z-10 bg-stone-950/95 whitespace-nowrap">Fecha</th>
            <th class="py-2.5 px-3 whitespace-nowrap">Responsable</th>
            <th class="py-2.5 px-3 min-w-[180px]">Detalle del Evento</th>
            <th class="py-2.5 px-3 text-right whitespace-nowrap">Impacto</th>
            <th class="py-2.5 px-3 text-center whitespace-nowrap">Estado</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!omisionesDisplay.length">
                <td colspan="5" class="py-8 text-center text-stone-500">
                  <i class="pi pi-inbox text-2xl mb-2 block" />
                  Sin omisiones registradas en modo {{ isMock ? 'MOCK' : 'REAL' }}.
                  <span v-if="!isMock" class="block text-[11px] mt-1">Los datos vienen de <code>GET /api/v1/omisiones</code>.</span>
                </td>
              </tr>
          <tr v-for="o in omisionesDisplay" :key="o.id">
            <td class="py-3 px-3 text-stone-400 sticky left-0 z-10 bg-stone-900/95 whitespace-nowrap">{{ o.fecha }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold whitespace-nowrap">{{ o.usuario }}</td>
            <td class="py-3 px-3 text-stone-300 min-w-[180px]">{{ o.evento }}</td>
            <td class="py-3 px-3 text-right text-stone-400 font-semibold whitespace-nowrap">{{ o.impacto }}</td>
            <td class="py-3 px-3 text-center whitespace-nowrap">
              <span
                v-if="(o as any).resuelta"
                class="px-2.5 py-1 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 text-[10px]"
              >
                Resuelta
              </span>
              <Button
                v-else
                label="Resolver"
                icon="pi pi-check"
                size="small"
                text
                class="text-emerald-400 text-xs"
                :loading="resolviendoId === o.id"
                @click="marcarResuelta(o)"
              />
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <!-- Mobile cards: same omisionesDisplay. No horizontal scroll. -->
      <div class="space-y-3 md:hidden max-w-full min-w-0">
        <div v-if="!omisionesDisplay.length" class="text-center py-8 text-sm text-stone-500">Sin omisiones registradas en modo {{ isMock ? 'MOCK' : 'REAL' }}.</div>
        <div v-for="o in omisionesDisplay" :key="o.id" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="font-bold text-sm text-amber-300 min-w-0">{{ o.usuario }}</div>
            <span class="text-xs text-stone-500 shrink-0">{{ o.fecha }}</span>
          </div>
          <div class="text-sm text-stone-300">{{ o.evento }}</div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Impacto</span>
            <span class="font-mono font-semibold text-stone-200">{{ o.impacto }}</span>
          </div>
          <div>
            <span v-if="(o as any).resuelta" class="inline-block px-2.5 py-1 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 text-xs">Resuelta</span>
            <Button v-else label="Resolver" icon="pi pi-check" size="small" text class="text-emerald-400 text-sm min-h-[40px]" :loading="resolviendoId === o.id" @click="marcarResuelta(o)" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
