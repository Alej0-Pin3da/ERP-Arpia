<script setup lang="ts">
import { ref } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useAtelierStore, type LiquidacionSocias, type LiquidacionSociaItem } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  liquidacion: LiquidacionSocias | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'editar', liq: LiquidacionSocias): void
}>()

const atelier = useAtelierStore()

const modalPagoVisible = ref(false)
const sociaPagoSeleccionada = ref<LiquidacionSociaItem | null>(null)
const comprobanteInput = ref('')

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function abrirRegistroPago(item: LiquidacionSociaItem) {
  sociaPagoSeleccionada.value = item
  comprobanteInput.value = item.comprobante_transferencia || `TR-${Date.now().toString().slice(-6)}`
  modalPagoVisible.value = true
}

function confirmarPagoSocia() {
  if (!props.liquidacion || !sociaPagoSeleccionada.value) return

  atelier.marcarPagoSociaItem(
    props.liquidacion.id,
    sociaPagoSeleccionada.value.socia_id,
    comprobanteInput.value.trim()
  )

  showToast(
    'success',
    'Pago Registrado',
    `Se marcó como PAGADO el monto de ${formatCOP(sociaPagoSeleccionada.value.monto_neto_pagar)} para ${sociaPagoSeleccionada.value.nombre_socia}.`
  )

  modalPagoVisible.value = false
}

function imprimirActa() {
  showToast('info', 'Impresión de Acta', 'Generando formato imprimible del Acta de Reparto de Socias.')
  if (typeof window !== 'undefined') {
    window.print()
  }
}

function compartirWhatsApp() {
  if (!props.liquidacion) return
  const l = props.liquidacion
  const fecha = l.fecha_cierre

  let mensaje = `*ACTA DE LIQUIDACIÓN Y REPARTO DE UTILIDADES - ATELIER ARPÍA*\n`
  mensaje += `📜 *Código:* ${l.codigo}\n`
  mensaje += `📅 *Periodo:* ${l.periodo} (Cierre: ${fecha})\n`
  mensaje += `💰 *Ventas Totales:* ${formatCOP(l.total_ventas_brutas)}\n`
  mensaje += `✂️ *Costos Insumos:* ${formatCOP(l.costo_taller_insumos)}\n`
  mensaje += `🏢 *Gastos Operativos:* ${formatCOP(l.gastos_operativos)}\n`
  mensaje += `✨ *Utilidad Neta Total:* ${formatCOP(l.utilidad_neta_total)}\n`
  mensaje += `------------------------------------\n`
  mensaje += `*DISTRIBUCIÓN OFICIAL DE SOCIAS:*\n`

  l.distribucion.forEach((d) => {
    mensaje += `\n• *${d.nombre_socia}* (${d.porcentaje}%):\n`
    mensaje += `  - Cuota Bruta: ${formatCOP(d.monto_bruto)}\n`
    if (d.deduccion_anticipos > 0) {
      mensaje += `  - Anticipos Descontados: -${formatCOP(d.deduccion_anticipos)}\n`
    }
    mensaje += `  - *Neto a Transferir:* ${formatCOP(d.monto_neto_pagar)}\n`
    mensaje += `  - Estado: ${d.estado_pago === 'PAGADO' ? '✅ PAGADO' : '⏳ PENDIENTE'}\n`
    if (d.banco_destino) {
      mensaje += `  - Cuenta: ${d.banco_destino}\n`
    }
  })

  mensaje += `\n------------------------------------\n`
  mensaje += `Atelier Arpía • Corsetería & Alta Costura de Autor`

  const url = `https://wa.me/?text=${encodeURIComponent(mensaje)}`
  window.open(url, '_blank')
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="`📜 Acta Oficial de Reparto de Socias: ${liquidacion?.codigo}`"
    :style="{ width: '92vw', maxWidth: '820px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div v-if="liquidacion" class="space-y-6 pt-1 text-xs text-stone-200 printable-area">
      <!-- Header Banner / Luxury Branding -->
      <div class="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-stone-900 via-stone-950 to-stone-900 p-6 text-center relative overflow-hidden">
        <div class="absolute -right-8 -bottom-8 w-36 h-36 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />
        <div class="text-[10px] font-mono tracking-widest uppercase text-amber-400 font-bold">
          Atelier Arpía • Alta Costura & Corsetería
        </div>
        <h2 class="text-xl sm:text-2xl font-serif font-bold text-stone-100 mt-1">
          Acta de Liquidación y Reparto de Utilidades
        </h2>
        <div class="text-xs text-stone-400 font-mono mt-1">
          {{ liquidacion.periodo }} | Cierre Oficial: {{ liquidacion.fecha_cierre }}
        </div>

        <div class="mt-4 flex flex-wrap items-center justify-center gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider"
            :class="{
              'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40': liquidacion.estado === 'PAGADA',
              'bg-amber-500/20 text-amber-300 border border-amber-500/40': liquidacion.estado === 'APROBADA',
              'bg-stone-800 text-stone-300 border border-stone-700': liquidacion.estado === 'BORRADOR',
            }"
          >
            Estado: {{ liquidacion.estado }}
          </span>
          <span class="text-xs font-mono text-stone-400">Código: {{ liquidacion.codigo }}</span>
        </div>
      </div>

      <!-- Financial Metrics Summary (4 Blocks) -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
        <div class="p-3.5 rounded-xl bg-stone-900/80 border border-stone-800">
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">Ventas Brutas</div>
          <div class="text-base font-serif font-bold text-stone-100 mt-1">
            {{ formatCOP(liquidacion.total_ventas_brutas) }}
          </div>
        </div>

        <div class="p-3.5 rounded-xl bg-stone-900/80 border border-stone-800">
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">Costos Insumos</div>
          <div class="text-base font-serif font-bold text-rose-400 mt-1">
            -{{ formatCOP(liquidacion.costo_taller_insumos) }}
          </div>
        </div>

        <div class="p-3.5 rounded-xl bg-stone-900/80 border border-stone-800">
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">Gastos Fijos/Op.</div>
          <div class="text-base font-serif font-bold text-rose-400 mt-1">
            -{{ formatCOP(liquidacion.gastos_operativos) }}
          </div>
        </div>

        <div class="p-3.5 rounded-xl bg-amber-950/40 border border-amber-500/40">
          <div class="text-[10px] text-amber-300 uppercase tracking-wider font-bold">Utilidad Neta Total</div>
          <div class="text-base font-serif font-bold text-amber-300 mt-1">
            {{ formatCOP(liquidacion.utilidad_neta_total) }}
          </div>
        </div>
      </div>

      <!-- Detailed Breakdown Cards / Table -->
      <div class="bg-stone-900/90 rounded-2xl border border-stone-800 p-5 space-y-4">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-sm font-serif font-bold text-amber-300 flex items-center gap-2">
            <i class="pi pi-users text-amber-400" />
            Desglose de Liquidación por Socia y Fondo de Taller
          </h3>
          <span class="text-[11px] font-mono text-stone-400">Regla: 40% Taller / 30% Margara / 30% Valqui</span>
        </div>

        <div class="space-y-3">
          <div
            v-for="d in liquidacion.distribucion"
            :key="d.socia_id"
            class="p-4 rounded-xl border transition-all"
            :class="d.estado_pago === 'PAGADO' ? 'bg-stone-950/60 border-emerald-500/30' : 'bg-stone-950/90 border-stone-800'"
          >
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-stone-800/80 pb-3">
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-serif font-bold text-stone-100 text-sm">{{ d.nombre_socia }}</span>
                  <span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                    {{ d.porcentaje }}%
                  </span>
                </div>
                <div class="text-[11px] text-stone-400 font-mono mt-0.5">{{ d.rol_socia }}</div>
              </div>

              <div class="flex items-center gap-2">
                <span
                  class="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider"
                  :class="d.estado_pago === 'PAGADO' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'"
                >
                  {{ d.estado_pago === 'PAGADO' ? '✅ Transferido / Pagado' : '⏳ Pendiente de Pago' }}
                </span>
                <Button
                  v-if="d.estado_pago !== 'PAGADO'"
                  label="Registrar Pago"
                  icon="pi pi-check-circle"
                  size="small"
                  class="p-button-warning text-[11px] py-1 px-2.5"
                  @click="abrirRegistroPago(d)"
                />
              </div>
            </div>

            <!-- Numbers Breakdown -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 font-mono text-xs">
              <div>
                <span class="text-stone-400 text-[10px] block">Cuota Bruta ({{ d.porcentaje }}%):</span>
                <span class="text-stone-200 font-semibold">{{ formatCOP(d.monto_bruto) }}</span>
              </div>

              <div>
                <span class="text-stone-400 text-[10px] block">Deducción Anticipos:</span>
                <span class="text-rose-400 font-semibold">
                  {{ d.deduccion_anticipos > 0 ? `-${formatCOP(d.deduccion_anticipos)}` : '$0' }}
                </span>
              </div>

              <div>
                <span class="text-amber-400 text-[10px] block font-bold">Monto Neto a Transferir:</span>
                <span class="text-emerald-400 font-bold text-sm">{{ formatCOP(d.monto_neto_pagar) }}</span>
              </div>

              <div>
                <span class="text-stone-400 text-[10px] block">Datos de Cuenta / Pago:</span>
                <span class="text-stone-300 text-[11px] truncate block">{{ d.banco_destino || 'Efectivo / Caja Taller' }}</span>
              </div>
            </div>

            <!-- Payment reference if paid -->
            <div v-if="d.estado_pago === 'PAGADO'" class="mt-2.5 pt-2 border-t border-stone-800/60 flex items-center justify-between text-[11px] font-mono text-stone-400">
              <span>Fecha Pago: {{ d.fecha_pago || 'Confirmado' }}</span>
              <span v-if="d.comprobante_transferencia" class="text-amber-300">
                Comprobante: {{ d.comprobante_transferencia }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Notes / Signatures Section -->
      <div class="bg-stone-900/60 p-4 rounded-xl border border-stone-800 space-y-3 font-mono">
        <div class="text-[11px] text-stone-400 uppercase font-bold tracking-wider">
          Observaciones y Conformidad de Cierre:
        </div>
        <p class="text-stone-300 text-xs italic bg-stone-950/70 p-3 rounded-lg border border-stone-800/80">
          {{ liquidacion.observaciones || 'Liquidación conforme a los acuerdos del Atelier. Fondos debidamente asignados para reposición de insumos y cuotas de socias.' }}
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-stone-800 text-center">
          <div class="p-3 bg-stone-950/60 rounded-xl border border-stone-800/60">
            <div class="h-10 border-b border-stone-700/60 flex items-end justify-center pb-1 text-stone-500 font-serif italic text-sm">
              Margarita Restrepo
            </div>
            <div class="text-[11px] font-bold text-stone-300 mt-1">🪡 Margarita Restrepo (Margara)</div>
            <div class="text-[10px] text-stone-400">Co-fundadora Confección & Taller</div>
          </div>

          <div class="p-3 bg-stone-950/60 rounded-xl border border-stone-800/60">
            <div class="h-10 border-b border-stone-700/60 flex items-end justify-center pb-1 text-stone-500 font-serif italic text-sm">
              Valeria Quintero
            </div>
            <div class="text-[11px] font-bold text-stone-300 mt-1">🎨 Valeria Quintero (Valqui)</div>
            <div class="text-[10px] text-stone-400">Co-fundadora Dirección & Diseño</div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-stone-800">
        <Button
          label="Editar Liquidación"
          icon="pi pi-pencil"
          size="small"
          class="p-button-outlined p-button-secondary text-xs"
          @click="liquidacion && emit('editar', liquidacion)"
        />

        <div class="flex items-center gap-2">
          <Button
            label="Compartir WhatsApp"
            icon="pi pi-whatsapp"
            size="small"
            class="p-button-success text-xs font-semibold"
            @click="compartirWhatsApp"
          />
          <Button
            label="Imprimir Acta"
            icon="pi pi-print"
            size="small"
            class="p-button-secondary text-xs"
            @click="imprimirActa"
          />
          <Button
            label="Cerrar"
            icon="pi pi-times"
            size="small"
            class="p-button-text p-button-secondary text-xs"
            @click="emit('update:visible', false)"
          />
        </div>
      </div>
    </template>
  </Dialog>

  <!-- Modal Registrar Pago Socia -->
  <Dialog
    v-model:visible="modalPagoVisible"
    modal
    header="💸 Registrar Pago / Transferencia a Socia"
    :style="{ width: '90vw', maxWidth: '450px' }"
  >
    <div v-if="sociaPagoSeleccionada" class="space-y-4 pt-1 text-xs">
      <div class="bg-stone-900/80 p-3 rounded-xl border border-stone-800 space-y-1 font-mono">
        <div class="text-stone-400 text-[10px]">Beneficiaria:</div>
        <div class="font-serif font-bold text-stone-100 text-sm">{{ sociaPagoSeleccionada.nombre_socia }}</div>
        <div class="text-amber-300 font-bold text-base mt-1">
          Monto: {{ formatCOP(sociaPagoSeleccionada.monto_neto_pagar) }}
        </div>
        <div class="text-[10px] text-stone-400 mt-1">
          Cuenta: {{ sociaPagoSeleccionada.banco_destino || 'Efectivo Taller' }}
        </div>
      </div>

      <div>
        <label class="block text-[11px] font-bold text-stone-300 uppercase tracking-wider mb-1 font-mono">
          N° Comprobante / Referencia de Transferencia
        </label>
        <InputText
          v-model="comprobanteInput"
          placeholder="Ej: NEQ-109283 / BC-88123"
          class="w-full text-xs font-mono"
        />
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="modalPagoVisible = false"
        />
        <Button
          label="Confirmar Pago"
          icon="pi pi-check"
          size="small"
          class="p-button-success text-xs font-semibold"
          @click="confirmarPagoSocia"
        />
      </div>
    </template>
  </Dialog>
</template>
