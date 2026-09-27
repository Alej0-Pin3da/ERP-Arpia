<script setup lang="ts">
import { ref, computed } from 'vue'
import InputNumber from 'primevue/inputnumber'
import type { ProveedorRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  proveedores: ProveedorRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', payload: { tipo: string; id: number; nombre: string }): void
}>()

const maestros = useMaestros()

const filtroCategoriaProv = ref('TODOS')
const proveedoresFiltrados = computed(() => {
  if (filtroCategoriaProv.value === 'TODOS') return props.proveedores
  return props.proveedores.filter((p) => p.categoria === filtroCategoriaProv.value)
})

const modalProveedor = ref(false)
const modoEdicionProveedor = ref(false)
const provForm = ref<Partial<ProveedorRead>>({
  nombre: '',
  categoria: 'Telas Principales',
  ciudad: 'Pereira, Risaralda',
  contacto: '',
  telefono: '',
  email: '',
  tiempo_entrega_dias: 2,
  condicion_pago: 'Contado / Transferencia',
  calificacion: 5,
  activo: true,
  notas: '',
})

function sanitizeProveedorPayload(form: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const nombre = String(form.nombre ?? '').trim()
  if (nombre) out.nombre = nombre
  const categoria = String(form.categoria ?? '').trim()
  if (categoria) out.categoria = categoria
  const ciudad = String(form.ciudad ?? '').trim()
  out.ciudad = ciudad || null
  const emailRaw = String(form.email ?? '').trim()
  out.email = emailRaw || null
  const telRaw = String(form.telefono ?? '').trim()
  out.telefono = telRaw || null
  const cal = form.calificacion
  if (cal !== '' && cal !== null && cal !== undefined) {
    const n = Number(cal)
    if (!Number.isNaN(n)) out.calificacion = Math.max(0, Math.min(5, n))
  }
  const tiempo = form.tiempo_entrega_dias
  if (tiempo !== '' && tiempo !== null && tiempo !== undefined) {
    const n = Number(tiempo)
    if (!Number.isNaN(n)) out.tiempo_entrega_dias = Math.max(0, Math.round(n))
  }
  out.activo = form.activo !== false
  const notas = String(form.notas ?? '').trim()
  out.notas = notas || null
  return out
}

function abrirNuevoProveedor() {
  modoEdicionProveedor.value = false
  provForm.value = {
    nombre: '',
    categoria: 'Telas Principales',
    ciudad: 'Pereira, Risaralda',
    contacto: '',
    telefono: '',
    email: '',
    tiempo_entrega_dias: 2,
    condicion_pago: 'Contado / Transferencia',
    calificacion: 5,
    activo: true,
    notas: '',
  }
  modalProveedor.value = true
}

function abrirEditarProveedor(p: ProveedorRead) {
  modoEdicionProveedor.value = true
  provForm.value = { ...p }
  modalProveedor.value = true
}

async function guardarProveedor() {
  if (!provForm.value.nombre) {
    showToast('warn', 'Campo requerido', 'Ingresá el nombre del proveedor.')
    return
  }
  const payload = sanitizeProveedorPayload(provForm.value as unknown as Record<string, unknown>)
  try {
    if (modoEdicionProveedor.value && provForm.value.id) {
      await maestros.updateProveedor(provForm.value.id, payload)
    } else {
      await maestros.createProveedor(payload)
    }
    emit('actualizado')
    showToast('success', 'Proveedor guardado', `${provForm.value.nombre} guardado correctamente.`)
    modalProveedor.value = false
  } catch (e: unknown) {
    const msg = (e as any)?.response?.data?.detail ?? (e as Error)?.message ?? 'Error al guardar proveedor'
    const detail = Array.isArray(msg) ? msg.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : String(msg)
    showToast('error', 'Error 422', detail)
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
      <div>
        <h2 class="text-lg font-serif font-bold text-stone-100">Directorio Oficial de Proveedores</h2>
        <p class="text-xs text-stone-400 font-mono">Fábricas de telas, importadores de herrajes, hilaturas y talleres de serigrafía.</p>
      </div>

      <div class="flex items-center gap-3">
        <select
          id="filtro-categoria-proveedor"
          v-model="filtroCategoriaProv"
          class="bg-stone-950 border border-stone-700 text-stone-200 text-xs rounded-lg px-3 py-2 font-mono focus:border-amber-400 focus:outline-none"
        >
          <option value="TODOS">Todas las Categorías</option>
          <option value="Telas Principales">Telas Principales</option>
          <option value="Herrajes & Corsetería">Herrajes & Corsetería</option>
          <option value="Lonas & Estampación">Lonas & Estampación</option>
          <option value="Hilos & Accesorios">Hilos & Accesorios</option>
        </select>

        <button
          id="btn-nuevo-proveedor"
          @click="abrirNuevoProveedor"
          class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap"
        >
          <span>+</span> Nuevo Proveedor
        </button>
      </div>
    </div>

    <!-- Grid of Suppliers -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="prov in proveedoresFiltrados"
        :key="prov.id"
        :id="`card-proveedor-${prov.id}`"
        class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
      >
        <div>
          <div class="flex items-start justify-between gap-2">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-amber-300 border border-stone-700/60">
              {{ prov.categoria }}
            </span>
            <div class="flex items-center gap-1 text-amber-400 text-xs">
              <span>★</span>
              <span class="font-mono font-bold">{{ prov.calificacion }}</span>
            </div>
          </div>

          <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5 flex items-center gap-2">
            {{ prov.nombre }}
          </h3>
          <p class="text-xs text-stone-400 font-mono mt-0.5 flex items-center gap-1">
            <span>📍</span> {{ prov.ciudad }}
          </p>

          <div class="mt-3 bg-stone-950/70 p-2.5 rounded-lg border border-stone-800/80 space-y-1.5 text-xs font-mono">
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Contacto:</span>
              <span class="font-medium text-stone-200">{{ prov.contacto || 'No especificado' }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Teléfono/WhatsApp:</span>
              <span class="font-medium text-amber-300">{{ prov.telefono || 'Sin registro' }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Tiempo Entrega:</span>
              <span class="font-medium text-stone-200">{{ prov.tiempo_entrega_dias }} días hábiles</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span class="text-stone-500">Condición Pago:</span>
              <span class="font-medium text-emerald-400">{{ prov.condicion_pago }}</span>
            </div>
          </div>

          <p v-if="prov.notas" class="text-xs text-stone-400 mt-2.5 italic bg-stone-900/40 p-2 rounded border border-stone-800/50">
            "{{ prov.notas }}"
          </p>
        </div>

        <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-between">
          <a
            v-if="prov.telefono"
            :href="`https://wa.me/${(prov.telefono ?? '').replace(/[^0-9]/g, '')}`"
            target="_blank"
            class="text-xs text-emerald-400 hover:text-emerald-300 font-mono flex items-center gap-1"
          >
            <span>💬</span> WhatsApp
          </a>
          <span v-else class="text-xs text-stone-500 font-mono">Sin WhatsApp</span>

          <div class="flex items-center gap-2">
            <button
              :id="`btn-editar-prov-${prov.id}`"
              @click="abrirEditarProveedor(prov)"
              class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
            >
              Editar
            </button>
            <button
              :id="`btn-eliminar-prov-${prov.id}`"
              @click="emit('solicitar-eliminar', { tipo: 'proveedor', id: prov.id, nombre: prov.nombre })"
              class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
              title="Eliminar Proveedor"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL: PROVEEDOR -->
    <div
      v-if="modalProveedor"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionProveedor ? 'Editar Proveedor' : 'Nuevo Proveedor Textil / Insumos' }}
          </h3>
          <button @click="modalProveedor = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarProveedor" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre Comercial:</label>
            <input
              id="input-prov-nombre"
              v-model="provForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Atenea Bordados"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Categoría:</label>
              <select
                id="input-prov-cat"
                v-model="provForm.categoria"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="Telas Principales">Telas Principales</option>
                <option value="Herrajes & Corsetería">Herrajes & Corsetería</option>
                <option value="Lonas & Estampación">Lonas & Estampación</option>
                <option value="Hilos & Accesorios">Hilos & Accesorios</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Ciudad / Sede:</label>
              <input
                id="input-prov-ciudad"
                v-model="provForm.ciudad"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="Pereira, Risaralda"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Contacto / Asesor:</label>
              <input
                id="input-prov-contacto"
                v-model="provForm.contacto"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="Nombre del asesor"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Teléfono / WhatsApp:</label>
              <input
                id="input-prov-tel"
                v-model="provForm.telefono"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="+57 312 000 0000"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tiempo de Entrega (Días):</label>
              <InputNumber
                v-model="provForm.tiempo_entrega_dias"
                inputId="input-prov-dias"
                mode="decimal"
                locale="es-CO"
                :min="1"
                :step="1"
                :min-fraction-digits="0"
                :max-fraction-digits="0"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Condición de Pago:</label>
              <input
                id="input-prov-pago"
                v-model="provForm.condicion_pago"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="Contado / 30 días"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Notas / Especialidad:</label>
            <textarea
              id="input-prov-notas"
              v-model="provForm.notas"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Detalles sobre crédito, tiempos mínimos o calidad..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalProveedor = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Proveedor
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
