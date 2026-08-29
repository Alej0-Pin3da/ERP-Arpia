<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMode } from '@/composables/useMode'
import * as devolucionesApi from '@/services/api/devoluciones'

const { isMock } = useMode()
const devoluciones = ref([

  {
    id: 1,
    codigo: 'GAR-001',
    prenda: 'Corset Nocturna Brocado',
    cliente: 'Carolina Gómez',
    motivo: 'Ajuste de varillas laterales por reducción de talle',
    tipo: 'Ajuste a Medida (Garantía Atelier)',
    estado: 'En Modificación',
    fecha: '2026-08-19',
  },
])
const devolucionesReal = ref<any[]>([])
async function cargarDevolucionesReales() {
  if (isMock.value) return
  try {
    const r = await devolucionesApi.listDevoluciones({ limit: 100 })
    devolucionesReal.value = (r as any).items ?? []
  } catch { devolucionesReal.value = [] }
}
onMounted(() => { void cargarDevolucionesReales() })
watch(isMock, () => { void cargarDevolucionesReales() })
const devolucionesDisplay = computed(() => isMock.value ? devoluciones.value : (devolucionesReal.value.length ? devolucionesReal.value.map((d: any, idx: number) => ({
  id: d.id,
  codigo: `GAR-${d.id}`,
  prenda: `Venta #${d.venta_id}`,
  cliente: `Cliente ${d.venta_id}`,
  motivo: d.motivo || 'Ajuste Atelier',
  tipo: d.tipo || 'Garantía',
  estado: d.estado || 'Registrada',
  fecha: d.creado_en || '',
})) : []))
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Garantías & Ajustes de Taller
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Control de calce, adaptaciones post-entrega y garantías de corsetería de autor.
      </p>
    </div>

    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
      <table class="w-full text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3">Código</th>
            <th class="py-2.5 px-3">Prenda</th>
            <th class="py-2.5 px-3">Cliente</th>
            <th class="py-2.5 px-3">Motivo / Tipo de Ajuste</th>
            <th class="py-2.5 px-3">Estado</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!devolucionesDisplay.length">
                <td colspan="5" class="py-8 text-center text-stone-500">
                  <i class="pi pi-inbox text-2xl mb-2 block" />
                  Sin garantías registradas en modo {{ isMock ? 'MOCK' : 'REAL' }}.
                  <span v-if="!isMock" class="block text-[11px] mt-1">Los datos vienen de <code>GET /api/v1/devoluciones</code>.</span>
                </td>
              </tr>
          <tr v-for="d in devolucionesDisplay" :key="d.id">
            <td class="py-3 px-3 text-amber-400 font-bold">{{ d.codigo }}</td>
            <td class="py-3 px-3 font-serif font-semibold text-stone-200">{{ d.prenda }}</td>
            <td class="py-3 px-3 text-stone-300">{{ d.cliente }}</td>
            <td class="py-3 px-3 text-stone-400">{{ d.motivo }} ({{ d.tipo }})</td>
            <td class="py-3 px-3">
              <span class="px-2.5 py-1 rounded bg-amber-950/80 text-amber-300 border border-amber-500/30 text-[10px]">
                {{ d.estado }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
