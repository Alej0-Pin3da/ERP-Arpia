<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'
import { useDevoluciones } from '@/composables/useDevoluciones'
import type { DevolucionCreatePayload } from '@/services/api/devoluciones'

const { isMock } = useMode()
const devolucionesApi = useDevoluciones()
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
    const r = await devolucionesApi.list({ limit: 100 })
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
  estado: d.estado || 'draft',
  // DevolucionRead manda `fecha` (no `creado_en`); se aceptan alias por compat.
  fecha: (d.fecha ?? d.creado_en ?? d.created_at ?? '') as string,
})) : []))

// --- Create devolucion (P0-1) ---
const showCreateDialog = ref(false)
const saving = ref(false)
const formVentaId = ref<number | null>(null)
const formTipo = ref<'total' | 'parcial'>('total')
const formMotivo = ref('')
interface FormItem { producto_id: number | null; cantidad: number; precio: number }
const formItems = ref<FormItem[]>([{ producto_id: null, cantidad: 1, precio: 0 }])
const tipoOptions = [
  { label: 'Total (cancela la venta completa)', value: 'total' },
  { label: 'Parcial (requiere al menos un ítem)', value: 'parcial' },
]

function openCreateDialog() {
  formVentaId.value = null
  formTipo.value = 'total'
  formMotivo.value = ''
  formItems.value = [{ producto_id: null, cantidad: 1, precio: 0 }]
  showCreateDialog.value = true
}

function addItem() {
  formItems.value.push({ producto_id: null, cantidad: 1, precio: 0 })
}

function removeItem(idx: number) {
  if (formItems.value.length <= 1) return
  formItems.value.splice(idx, 1)
}

function extractDetail(e: unknown): string {
  const axiosDetail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (Array.isArray(axiosDetail)) {
    return axiosDetail.map((d: any) => d.msg ?? JSON.stringify(d)).join('; ')
  }
  if (typeof axiosDetail === 'string' && axiosDetail) return axiosDetail
  if (e instanceof Error && e.message) return e.message
  return 'No se pudo registrar la devolución'
}

// --- Delete devolucion (P1-8: solo draft) ---
const showDeleteDialog = ref(false)
const devolucionAEliminar = ref<{ id: number; codigo: string } | null>(null)
const deleting = ref(false)

function solicitarEliminarDevolucion(d: { id: number; codigo: string }) {
  devolucionAEliminar.value = d
  showDeleteDialog.value = true
}

async function confirmarEliminarDevolucion() {
  if (!devolucionAEliminar.value) return
  const target = devolucionAEliminar.value
  deleting.value = true
  try {
    if (isMock.value) {
      devoluciones.value = devoluciones.value.filter((d) => d.id !== target.id)
      showToast('info', 'Devolución eliminada', `Garantía ${target.codigo} eliminada en modo MOCK.`)
    } else {
      await devolucionesApi.remove(target.id)
      showToast('success', 'Devolución eliminada', `Devolución #${target.id} eliminada.`)
      await cargarDevolucionesReales()
    }
    devolucionAEliminar.value = null
    showDeleteDialog.value = false
  } catch (e: unknown) {
    showToast('error', 'No se pudo eliminar', extractDetail(e))
  } finally {
    deleting.value = false
  }
}

async function submitCreate() {
  if (!formVentaId.value || formVentaId.value <= 0) {
    showToast('warn', 'Campo requerido', 'Indicá el ID de la venta a devolver.')
    return
  }
  if (formTipo.value === 'parcial') {
    const valid = formItems.value.filter((it) => it.producto_id != null && Number(it.producto_id) > 0 && Number(it.cantidad) > 0)
    if (!valid.length) {
      showToast('warn', 'Campo requerido', 'La devolución parcial requiere al menos un ítem válido (ID de producto y cantidad > 0).')
      return
    }
  }
  saving.value = true
  try {
    const payload: DevolucionCreatePayload = {
      venta_id: Number(formVentaId.value),
      tipo: formTipo.value,
      motivo: formMotivo.value.trim() || null,
      items: formTipo.value === 'parcial'
        ? formItems.value
            .filter((it) => it.producto_id != null && Number(it.producto_id) > 0)
            .map((it) => ({
              producto_id: Number(it.producto_id),
              cantidad: Number(it.cantidad),
              precio_unitario: Number(it.precio),
            }))
        : null,
    }
    if (isMock.value) {
      const nextId = devoluciones.value.length
        ? Math.max(...devoluciones.value.map((d) => d.id)) + 1
        : 1
      devoluciones.value.unshift({
        id: nextId,
        codigo: `GAR-${String(nextId).padStart(3, '0')}`,
        prenda: `Venta #${payload.venta_id}`,
        cliente: `Cliente ${payload.venta_id}`,
        motivo: payload.motivo || 'Ajuste Atelier',
        tipo: payload.tipo === 'total' ? 'Devolución total' : 'Devolución parcial',
        estado: 'Registrada',
        fecha: new Date().toISOString().split('T')[0],
      })
      showToast('success', 'Devolución registrada', `Garantía GAR-${String(nextId).padStart(3, '0')} creada en modo MOCK.`)
    } else {
      const created = await devolucionesApi.create(payload) as { id: number }
      showToast('success', 'Devolución registrada', `Devolución #${created.id} creada para la venta #${payload.venta_id}.`)
      await cargarDevolucionesReales()
    }
    showCreateDialog.value = false
  } catch (e: unknown) {
    showToast('error', 'Error al registrar', extractDetail(e))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
          Garantías & Ajustes de Taller
        </h1>
        <p class="text-xs text-stone-400 mt-1 font-mono">
          Control de calce, adaptaciones post-entrega y garantías de corsetería de autor.
        </p>
      </div>
      <Button
        label="Registrar devolución"
        icon="pi pi-plus"
        size="small"
        class="p-button-warning text-xs font-semibold"
        @click="openCreateDialog"
      />
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
            <th class="py-2.5 px-3 text-center">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!devolucionesDisplay.length">
                <td colspan="6" class="py-8 text-center text-stone-500">
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
                {{ ({ draft: 'Borrador', confirmed: 'Confirmada', cancelled: 'Anulada', reversed: 'Revertida' } as Record<string, string>)[d.estado] ?? d.estado }}
              </span>
            </td>
            <td class="py-3 px-3 text-center">
              <Button
                v-if="d.estado === 'draft'"
                icon="pi pi-trash"
                size="small"
                text
                rounded
                class="p-button-danger text-rose-400 hover:bg-rose-950/40"
                title="Eliminar borrador"
                @click="solicitarEliminarDevolucion(d)"
              />
              <span v-else class="text-stone-600 text-[10px]" title="Solo los borradores se pueden eliminar; el resto se anula por transición de estado">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Dialog
      v-model:visible="showCreateDialog"
      modal
      header="Registrar devolución"
      :style="{ width: '90vw', maxWidth: '480px' }"
    >
      <div class="space-y-3 pt-2 text-xs">
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">ID de venta *</label>
          <InputText v-model.number="formVentaId" type="number" min="1" placeholder="Ej. 12" class="text-xs" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">Tipo *</label>
          <Dropdown
            v-model="formTipo"
            :options="tipoOptions"
            option-label="label"
            option-value="value"
            class="text-xs w-full"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">Motivo</label>
          <InputText v-model="formMotivo" placeholder="Motivo de la devolución" class="text-xs" />
        </div>
        <div v-if="formTipo === 'parcial'" class="space-y-2 border-t border-stone-800 pt-3">
          <div v-for="(it, idx) in formItems" :key="idx" class="grid grid-cols-[1fr_1fr_1fr_auto] gap-2 items-end">
            <div class="flex flex-col gap-1">
              <label class="font-semibold text-stone-300">Producto ID *</label>
              <InputText v-model.number="it.producto_id" type="number" min="1" placeholder="Ej. 5" class="text-xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="font-semibold text-stone-300">Cantidad *</label>
              <InputText v-model.number="it.cantidad" type="number" :min="1" class="text-xs" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="font-semibold text-stone-300">Precio unit.</label>
              <InputText v-model.number="it.precio" type="number" :min="0" class="text-xs" />
            </div>
            <Button
              icon="pi pi-trash"
              size="small"
              text
              rounded
              class="p-button-danger text-rose-400"
              title="Quitar ítem"
              :disabled="formItems.length <= 1"
              @click="removeItem(idx)"
            />
          </div>
          <Button label="Agregar ítem" icon="pi pi-plus" size="small" text class="text-xs text-amber-300" @click="addItem" />
          <p class="text-[11px] text-stone-500 font-mono">
            El precio final se recalcula desde la venta original en el backend.
          </p>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
          <Button
            label="Cancelar"
            icon="pi pi-times"
            size="small"
            class="p-button-text p-button-secondary text-xs"
            :disabled="saving"
            @click="showCreateDialog = false"
          />
          <Button
            label="Guardar devolución"
            icon="pi pi-check"
            size="small"
            class="p-button-warning text-xs font-semibold"
            :loading="saving"
            @click="submitCreate"
          />
        </div>
      </template>
    </Dialog>

    <Dialog
      v-model:visible="showDeleteDialog"
      modal
      header="Eliminar devolución"
      :style="{ width: '90vw', maxWidth: '420px' }"
    >
      <p class="text-xs text-stone-300 pt-2">
        ¿Eliminar el borrador <strong class="text-amber-300">{{ devolucionAEliminar?.codigo }}</strong>?
        Solo los borradores se eliminan; las devoluciones confirmadas se anulan por transición de estado.
      </p>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
          <Button
            label="Cancelar"
            icon="pi pi-times"
            size="small"
            class="p-button-text p-button-secondary text-xs"
            :disabled="deleting"
            @click="showDeleteDialog = false"
          />
          <Button
            label="Eliminar"
            icon="pi pi-trash"
            size="small"
            severity="danger"
            class="text-xs font-semibold"
            :loading="deleting"
            @click="confirmarEliminarDevolucion"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>
