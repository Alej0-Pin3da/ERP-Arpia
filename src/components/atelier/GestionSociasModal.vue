<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type SociaAtelier } from '@/stores/atelier'
import { showToast } from '@/utils/toast'
import { useMode } from '@/composables/useMode'
import { useSocios } from '@/composables/useSocios'

const props = defineProps<{
  visible: boolean
  sociaEditar?: SociaAtelier | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardada', socia: SociaAtelier): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const sociosApi = useSocios()

const isEditing = computed(() => !!props.sociaEditar)

// Form fields
const nombre = ref('')
const rol = ref('')
const porcentaje = ref(30)
const esFondoTaller = ref(false)
const telefono = ref('')
const email = ref('')
const banco = ref('Bancolombia')
const tipoCuenta = ref('Ahorros')
const numeroCuenta = ref('')
const titularCuenta = ref('')
const activo = ref(true)
const notas = ref('')

const guardando = ref(false)

const sumaPorcentajesActuales = computed(() => {
  const sociasSrc = isMock.value ? atelier.socias : [] as any[]
  const otros = sociasSrc.filter((s) => s.activo && (!props.sociaEditar || s.id !== props.sociaEditar.id))
  const sumOtros = otros.reduce((acc, s) => acc + s.porcentaje, 0)
  return sumOtros + (porcentaje.value || 0)
})

// El backend solo acepta Literal["AHORROS","CORRIENTE","OTRA"]: el texto
// libre ("Nequi", "Digital"...) se nulificaba silenciosamente en REAL.
const TIPOS_CUENTA = ['AHORROS', 'CORRIENTE', 'OTRA'] as const
const tiposCuentaOptions = [
  { label: 'Ahorros', value: 'AHORROS' },
  { label: 'Corriente', value: 'CORRIENTE' },
  { label: 'Otra', value: 'OTRA' },
]
function toTipoLiteral(v: unknown): 'AHORROS' | 'CORRIENTE' | 'OTRA' {
  const u = String(v ?? '').trim().toUpperCase()
  return (TIPOS_CUENTA as readonly string[]).includes(u) ? (u as 'AHORROS' | 'CORRIENTE' | 'OTRA') : 'AHORROS'
}

function initForm() {
  if (props.sociaEditar) {
    const s = props.sociaEditar
    nombre.value = s.nombre
    rol.value = s.rol
    porcentaje.value = s.porcentaje
    esFondoTaller.value = Boolean(s.es_fondo_taller)
    telefono.value = s.telefono || ''
    email.value = s.email || ''
    banco.value = s.banco || 'Bancolombia'
    // En REAL el backend solo acepta el Literal: se normaliza al cargarlo.
    tipoCuenta.value = isMock.value ? (s.tipo_cuenta || 'Ahorros') : toTipoLiteral(s.tipo_cuenta)
    numeroCuenta.value = s.numero_cuenta || ''
    titularCuenta.value = s.titular_cuenta || s.nombre
    activo.value = s.activo
    notas.value = s.notas || ''
  } else {
    nombre.value = ''
    rol.value = 'Socia Colaboradora'
    porcentaje.value = 20
    esFondoTaller.value = false
    telefono.value = ''
    email.value = ''
    banco.value = 'Bancolombia'
    tipoCuenta.value = isMock.value ? 'Ahorros' : 'AHORROS'
    numeroCuenta.value = ''
    titularCuenta.value = ''
    activo.value = true
    notas.value = ''
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) initForm()
  },
  { immediate: true },
)

async function guardar() {
  if (guardando.value) return
  if (!nombre.value.trim()) {
    showToast('warn', 'Campo requerido', 'Por favor ingrese el nombre de la socia.')
    return
  }

  // isMock ? atelier shape (porcentaje) : API shape (porcentaje_participacion + Literal tipo_cuenta)
  // En REAL el dropdown ya entrega el Literal; esto es red de seguridad.
  const rawTipo = toTipoLiteral(tipoCuenta.value)
  const tipoCuentaLiteral = rawTipo as 'AHORROS' | 'CORRIENTE' | 'OTRA'

  if (isMock.value) {
    const payload: Partial<SociaAtelier> = {
      nombre: nombre.value.trim(),
      rol: rol.value.trim() || 'Socia Colaboradora',
      porcentaje: Number(porcentaje.value) || 0,
      es_fondo_taller: esFondoTaller.value,
      telefono: telefono.value.trim(),
      email: email.value.trim(),
      banco: banco.value.trim(),
      tipo_cuenta: tipoCuenta.value.trim(),
      numero_cuenta: numeroCuenta.value.trim(),
      titular_cuenta: titularCuenta.value.trim() || nombre.value.trim(),
      activo: activo.value,
      notas: notas.value.trim(),
    }
    if (isEditing.value && props.sociaEditar) {
      const act = atelier.actualizarSocia(props.sociaEditar.id, payload)
      if (act) {
        showToast('success', 'Socia Actualizada', `Perfil de ${act.nombre} actualizado correctamente.`)
        emit('guardada', act)
      }
    } else {
      const nueva = atelier.crearSocia(payload)
      showToast('success', 'Socia Registrada', `${nueva.nombre} ha sido añadida con ${nueva.porcentaje}% de participación.`)
      emit('guardada', nueva)
    }
    emit('update:visible', false)
    return
  }

  // Real API
  const apiPayload = {
    nombre: nombre.value.trim(),
    porcentaje_participacion: Number(porcentaje.value) || 0,
    rol: rol.value.trim() || null,
    es_fondo_taller: esFondoTaller.value,
    telefono: telefono.value.trim() || null,
    email: email.value.trim() || null,
    banco: banco.value.trim() || null,
    tipo_cuenta: tipoCuentaLiteral,
    numero_cuenta: numeroCuenta.value.trim() || null,
    titular_cuenta: titularCuenta.value.trim() || nombre.value.trim(),
    activo: activo.value,
    notas: notas.value.trim() || null,
  }
  guardando.value = true
  try {
    if (isEditing.value && props.sociaEditar) {
      const updated = await sociosApi.update(props.sociaEditar.id, apiPayload)
      showToast('success', 'Socia Actualizada', `Perfil de ${(updated as SociaAtelier).nombre ?? apiPayload.nombre} actualizado.`)
      emit('guardada', updated as unknown as SociaAtelier)
    } else {
      const created = await sociosApi.create(apiPayload)
      showToast('success', 'Socia Registrada', `${(created as SociaAtelier).nombre ?? apiPayload.nombre} registrada con ${apiPayload.porcentaje_participacion}%.`)
      emit('guardada', created as unknown as SociaAtelier)
    }
    emit('update:visible', false)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al guardar socia'
    showToast('error', 'Error', String(msg))
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="isEditing ? `✏️ Editar Socia: ${sociaEditar?.nombre}` : '✨ Registrar Nueva Socia o Fondo de Reparto'"
    :style="{ width: '90vw', maxWidth: '650px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1 text-xs text-stone-200">
      <!-- General Info -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-stone-900/70 p-3.5 rounded-xl border border-stone-800">
        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold text-amber-300 uppercase tracking-wider mb-1">
            Nombre Completo / Denominación *
          </label>
          <InputText v-model="nombre" class="w-full text-xs" placeholder="Ej: Margarita Restrepo (Margara)" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-300 uppercase tracking-wider mb-1">
            Rol en el Atelier
          </label>
          <InputText v-model="rol" class="w-full text-xs" placeholder="Ej: Jefa de Confección & Moldería" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1 font-mono">
            % de Participación en Utilidades *
          </label>
          <InputNumber
            v-model="porcentaje"
            suffix="%"
            :min="0"
            :max="100"
            class="w-full text-xs font-mono"
          />
        </div>

        <!-- Percentage Warning / Balance -->
        <div class="sm:col-span-2 p-2.5 rounded-lg border font-mono text-[11px] flex items-center justify-between"
          :class="sumaPorcentajesActuales === 100 ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300' : 'bg-amber-950/40 border-amber-500/40 text-amber-300'"
        >
          <span>Suma total de cuotas activas: <strong>{{ sumaPorcentajesActuales }}%</strong></span>
          <span>{{ sumaPorcentajesActuales === 100 ? '✅ Reparto Exacto (100%)' : '⚠️ Ajustar para sumar 100%' }}</span>
        </div>
      </div>

      <!-- Bank Details -->
      <div class="bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 space-y-3">
        <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider font-mono">
          Datos de Transferencia Bancaria / Liquidación
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Entidad Bancaria / Plataforma
            </label>
            <InputText v-model="banco" class="w-full text-xs" placeholder="Ej: Bancolombia / Nequi / Daviplata" />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Tipo de Cuenta
            </label>
            <Dropdown v-if="!isMock" v-model="tipoCuenta" :options="tiposCuentaOptions" option-label="label" option-value="value" class="w-full text-xs" />
            <InputText v-else v-model="tipoCuenta" class="w-full text-xs" placeholder="Ahorros / Corriente / Digital" />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Número de Cuenta
            </label>
            <InputText v-model="numeroCuenta" class="w-full text-xs font-mono" placeholder="312-445892-11" />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Titular de la Cuenta
            </label>
            <InputText v-model="titularCuenta" class="w-full text-xs" placeholder="Nombre titular" />
          </div>
        </div>
      </div>

      <!-- Contact and Flags -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <div>
          <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
            Teléfono / WhatsApp
          </label>
          <InputText v-model="telefono" class="w-full text-xs font-mono" placeholder="+57 312 000 0000" />
        </div>

        <div>
          <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
            Correo Electrónico
          </label>
          <InputText v-model="email" class="w-full text-xs" placeholder="socia@atelierarpia.com" />
        </div>

        <div class="sm:col-span-2 flex flex-wrap items-center gap-6 pt-2">
          <div class="flex items-center gap-2">
            <Checkbox v-model="esFondoTaller" :binary="true" input-id="chkFondo" />
            <label for="chkFondo" class="text-xs text-stone-300 cursor-pointer">
              Es el Fondo de Reinversión del Taller (40%)
            </label>
          </div>

          <div class="flex items-center gap-2">
            <Checkbox v-model="activo" :binary="true" input-id="chkActivo" />
            <label for="chkActivo" class="text-xs text-emerald-400 font-bold cursor-pointer">
              Socia Activa en Repartos
            </label>
          </div>
        </div>

        <div class="sm:col-span-2">
          <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
            Notas & Responsabilidades
          </label>
          <Textarea v-model="notas" rows="2" class="w-full text-xs" placeholder="Funciones, acuerdos internos..." />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          :label="isEditing ? 'Guardar Cambios' : 'Registrar Socia'"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold px-4"
          :loading="guardando"
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
