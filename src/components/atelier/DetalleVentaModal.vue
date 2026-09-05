<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { type VentaAtelier, useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { useClientes } from '@/composables/useClientes'

const props = defineProps<{
  visible: boolean
  venta: VentaAtelier | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'editar', venta: VentaAtelier): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const clientesApi = useClientes()
const clienteReal = ref<any>(null)

async function cargarCliente() {
  clienteReal.value = null
  if (isMock.value || !props.venta?.cliente_id) return
  try {
    clienteReal.value = await clientesApi.get(props.venta.cliente_id)
  } catch { clienteReal.value = null }
}
watch(() => props.venta, () => { void cargarCliente() }, { immediate: true })
watch(isMock, () => { void cargarCliente() })

const clienteVinculado = computed(() => {
  if (!props.venta?.cliente_id) return null
  if (!isMock.value) return clienteReal.value
  return atelier.clientes.find((c) => c.id === props.venta?.cliente_id) || null
})

const telefonoLimpio = computed(() => String(clienteVinculado.value?.telefono || '').replace(/\D/g, ''))

const margenPct = computed(() => {
  if (!props.venta) return 0
  if (props.venta.margen_pct && props.venta.margen_pct !== 0) return props.venta.margen_pct
  if (props.venta.total_venta > 0) return Number(((props.venta.ganancia_neta / props.venta.total_venta) * 100).toFixed(1))
  return 0
})
const reinversion40 = computed(() => props.venta?.reinversion_40 || Math.round((props.venta?.ganancia_neta ?? 0) * 0.4))
const margarita30 = computed(() => props.venta?.margarita_30 || Math.round((props.venta?.ganancia_neta ?? 0) * 0.3))
const valqui30 = computed(() => props.venta?.valqui_30 || Math.round((props.venta?.ganancia_neta ?? 0) * 0.3))

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function imprimirRecibo() {
  window.print()
}

function compartirWhatsApp() {
  if (!props.venta) return
  const v = props.venta
  const lineasPrendas = v.items
    .map((it) => `• ${it.cantidad}x ${it.nombre_prenda} (${it.talla}, ${it.color}) - ${formatCOP(it.subtotal)}`)
    .join('%0A')

  const msg = `*ATELIER ARPÍA - COMPROBANTE DE COMPRA*%0A%0A` +
    `*Código:* ${v.codigo}%0A` +
    `*Fecha:* ${v.fecha}%0A` +
    `*Cliente:* ${v.cliente_nombre}%0A` +
    `*Canal:* ${v.canal}%0A%0A` +
    `*Prendas:*%0A${lineasPrendas}%0A%0A` +
    (v.descuento_valor > 0 ? `*Descuento:* -${formatCOP(v.descuento_valor)} (${v.descuento_porcentaje}%)%0A` : '') +
    `*TOTAL FACTURADO:* ${formatCOP(v.total_venta)}%0A` +
    `*Método de Pago:* ${v.metodo_pago}%0A%0A` +
    `¡Gracias por apoyar la corsetería y confección de autor de Atelier Arpía! ✨🖤`

  const phone = telefonoLimpio.value
  if (!phone) return
  const url = `https://wa.me/${phone}?text=${msg}`
  window.open(url, '_blank')
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="`🧾 Comprobante de Venta: ${venta?.codigo || ''}`"
    :style="{ width: '92vw', maxWidth: '680px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div v-if="venta" class="space-y-6 pt-1 text-stone-200">
      <!-- Luxury Brand Header -->
      <div class="bg-gradient-to-b from-stone-900 to-stone-950 p-5 rounded-2xl border border-amber-500/30 text-center relative overflow-hidden shadow-xl">
        <div class="absolute -top-12 -right-12 w-32 h-32 bg-amber-500/10 rounded-full blur-2xl"></div>
        <div class="flex items-center justify-center gap-2 mb-2">
          <img src="/arpia-05-1-100x100.png" alt="Arpía Emblem" class="w-10 h-10 object-contain drop-shadow-[0_0_8px_rgba(217,119,6,0.5)]" />
          <span class="font-serif text-xl font-bold tracking-widest text-amber-300 uppercase">
            Atelier Arpía
          </span>
        </div>
        <p class="text-[11px] text-stone-400 font-serif italic tracking-wide m-0">
          Alta Corsetería & Lencería de Autor • Pereira, Colombia
        </p>

        <div class="mt-4 pt-3 border-t border-stone-800/80 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
          <div>
            <span class="text-stone-500">Recibo:</span>
            <span class="text-amber-400 font-bold ml-1">{{ venta.codigo }}</span>
          </div>
          <div>
            <span class="text-stone-500">Fecha:</span>
            <span class="text-stone-300 ml-1">{{ venta.fecha }}</span>
          </div>
          <div>
            <span class="text-stone-500">Canal:</span>
            <span class="text-stone-300 ml-1">{{ venta.canal }}</span>
          </div>
          <div>
            <span
              class="px-2 py-0.5 rounded text-[10px] font-bold border"
              :class="venta.estado === 'COMPLETADA' ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/30' : venta.estado === 'PENDIENTE' ? 'bg-amber-950/80 text-amber-300 border-amber-500/30' : 'bg-rose-950/80 text-rose-300 border-rose-500/30'"
            >
              {{ venta.estado }}
            </span>
          </div>
        </div>
      </div>

      <!-- Customer Info Card -->
      <div class="bg-stone-900/70 p-4 rounded-xl border border-stone-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div>
          <div class="text-[10px] text-stone-400 uppercase font-bold tracking-wider font-mono">Cliente / Destinataria</div>
          <div class="text-base font-serif font-bold text-stone-100 mt-0.5">{{ venta.cliente_nombre }}</div>
          <div v-if="clienteVinculado" class="text-stone-400 text-[11px] mt-1 font-mono">
            📞 {{ clienteVinculado.telefono }} | ✉️ {{ clienteVinculado.email }} | 📍 {{ clienteVinculado.ciudad || 'Pereira' }}
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Button
            v-if="telefonoLimpio"
            label="Enviar por WhatsApp"
            icon="pi pi-whatsapp"
            size="small"
            class="p-button-outlined p-button-success text-xs font-semibold"
            @click="compartirWhatsApp"
          />
        </div>
      </div>

      <!-- Line Items Table -->
      <div class="bg-stone-900/60 rounded-xl border border-stone-800 overflow-hidden">
        <div class="px-4 py-2.5 bg-stone-950/80 border-b border-stone-800 text-[11px] font-bold text-amber-300 uppercase tracking-wider font-mono">
          Prendas Confeccionadas & Artículos
        </div>

        <table class="w-full text-xs text-left border-collapse font-mono">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 text-[11px]">
              <th class="py-2.5 px-4 font-normal">Descripción</th>
              <th class="py-2.5 px-3 font-normal text-center">Talla</th>
              <th class="py-2.5 px-3 font-normal text-center">Color</th>
              <th class="py-2.5 px-3 font-normal text-right">Cant.</th>
              <th class="py-2.5 px-3 font-normal text-right">Precio Unit.</th>
              <th class="py-2.5 px-4 font-normal text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60">
            <tr v-for="it in venta.items" :key="it.id" class="hover:bg-stone-800/30">
              <td class="py-3 px-4 font-serif font-semibold text-stone-100">{{ it.nombre_prenda }}</td>
              <td class="py-3 px-3 text-center">
                <span class="px-2 py-0.5 rounded bg-stone-800 text-amber-300 border border-stone-700 text-[10px]">
                  {{ it.talla }}
                </span>
              </td>
              <td class="py-3 px-3 text-center text-stone-300 text-[11px]">{{ it.color }}</td>
              <td class="py-3 px-3 text-right font-bold text-stone-200">{{ it.cantidad }}</td>
              <td class="py-3 px-3 text-right text-stone-300">{{ formatCOP(it.precio_unitario) }}</td>
              <td class="py-3 px-4 text-right font-bold text-amber-400">{{ formatCOP(it.subtotal) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Financial Totals & Partner Breakdown -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Totals breakdown -->
        <div class="bg-stone-900/80 p-4 rounded-xl border border-stone-800 space-y-2 font-mono text-xs">
          <div class="flex justify-between text-stone-400">
            <span>Subtotal Bruto:</span>
            <span class="text-stone-200 font-bold">{{ formatCOP(venta.subtotal) }}</span>
          </div>

          <div v-if="venta.descuento_valor > 0" class="flex justify-between text-rose-400">
            <span>Descuento aplicado ({{ venta.descuento_porcentaje }}%):</span>
            <span class="font-bold">-{{ formatCOP(venta.descuento_valor) }}</span>
          </div>

          <div class="flex justify-between text-stone-400 border-t border-stone-800 pt-2">
            <span>Método de Pago:</span>
            <span class="text-stone-200">{{ venta.metodo_pago }}</span>
          </div>

          <div class="flex justify-between text-base font-bold text-amber-400 border-t border-amber-500/30 pt-2">
            <span>TOTAL FACTURADO:</span>
            <span>{{ formatCOP(venta.total_venta) }}</span>
          </div>

          <div v-if="venta.observaciones" class="mt-3 pt-2 border-t border-stone-800/80 text-[11px] text-stone-400 italic">
            <strong>Notas:</strong> {{ venta.observaciones }}
          </div>
        </div>

        <!-- Taller Internal Profit & Partner Distribution -->
        <div class="bg-gradient-to-br from-stone-950 via-stone-900 to-amber-950/40 p-4 rounded-xl border border-amber-500/40 space-y-2 font-mono text-xs">
          <div class="text-[10px] font-bold text-amber-400 uppercase tracking-wider pb-1 border-b border-stone-800">
            Análisis Financiero & Liquidación Socias
          </div>

          <div class="flex justify-between text-stone-400">
            <span>Costo Total Insumos & Confección:</span>
            <span class="text-stone-300">{{ formatCOP(venta.costo_total) }}</span>
          </div>

          <div class="flex justify-between text-emerald-400 font-bold">
            <span>Ganancia Neta Atelier:</span>
            <span>{{ formatCOP(venta.ganancia_neta) }} ({{ margenPct }}%)</span>
          </div>

          <div class="mt-3 pt-2 border-t border-stone-800/80 space-y-1.5 text-[11px]">
            <div class="flex justify-between text-amber-300 font-semibold">
              <span>🏛️ Fondo Reinversión Atelier (40%):</span>
              <span>{{ formatCOP(reinversion40) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🪡 Margara Confección (30%):</span>
              <span>{{ formatCOP(margarita30) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🎨 Valqui Diseño (30%):</span>
              <span>{{ formatCOP(valqui30) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-2 pt-3 border-t border-stone-800 w-full">
        <Button
          label="Imprimir Recibo"
          icon="pi pi-print"
          size="small"
          class="p-button-outlined p-button-secondary text-xs"
          @click="imprimirRecibo"
        />

        <div class="flex items-center gap-2">
          <Button
            label="Editar Venta"
            icon="pi pi-pencil"
            size="small"
            class="p-button-outlined p-button-warning text-xs"
            @click="venta && emit('editar', venta)"
          />
          <Button
            label="Cerrar"
            icon="pi pi-times"
            size="small"
            class="p-button-secondary text-xs"
            @click="emit('update:visible', false)"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
