<script setup lang="ts">
/**
 * Omisiones view (PR3, spec MIG-3/MIG-4 + FE-1/FE-2/FE-3).
 *
 * Read surface for the migration omission log (populated by the CLI hook in
 * commit mode): server-side pagination against {items, total} via the
 * PrimeVue Paginator, toolbar
 * filters (q, fase, nivel, hoja, resuelta) that reset to page 1 (FE-2),
 * and an admin-only "Marcar resuelta"/"Reabrir" action (D9 — the PATCH
 * endpoint is require_admin server-side).
 *
 * The presentational pattern is intact: the view owns page/filtros state,
 * calls the API, and passes rows down to OmisionesTable.
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { omisionesApi } from '@/api/endpoints'
import OmisionesTable from '@/components/omisiones/OmisionesTable.vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import { useAuthStore } from '@/stores/auth'
import { buildListParams } from '@/utils/pagination'
import type { OmisionRead } from '@/types/api.d'

const auth = useAuthStore()

/** D9: only an admin may mark omissions resolved (mirrors require_admin). */
const canResolve = computed(() => auth.role === 'admin')

const loading = ref(false)
const error = ref<string | null>(null)

const omisiones = ref<OmisionRead[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const searchQ = ref('')
const filterFase = ref('')
const filterNivel = ref<'WARN' | 'ERROR' | null>(null)
const filterHoja = ref('')
const filterResuelta = ref<boolean | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const result = await omisionesApi.listOmisiones(
      buildListParams({
        page: page.value,
        pageSize,
        filtros: {
          fase: filterFase.value,
          nivel: filterNivel.value,
          hoja: filterHoja.value,
          resuelta: filterResuelta.value,
        },
        q: searchQ.value,
      }),
    )
    omisiones.value = result.items
    total.value = result.total
  } catch {
    error.value = 'No se pudieron cargar las omisiones. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** FE-2: filtros/búsqueda vuelven a página 1 y refetchean. */
function onSearch(): void {
  page.value = 1
  load()
}

function onFilterChange(): void {
  page.value = 1
  load()
}

/** MIG-4: marca/desmarca resuelta (admin-only, D9). */
async function onToggleResuelta(row: OmisionRead): Promise<void> {
  try {
    const updated = await omisionesApi.updateOmision(
      { omision_id: row.id },
      { resuelta: !row.resuelta },
    )
    ElMessage.success(updated.resuelta ? 'Omisión marcada como resuelta' : 'Omisión reabierta')
    await load()
  } catch {
    ElMessage.error('No se pudo actualizar la omisión.')
  }
}

onMounted(load)
</script>

<template>
  <section class="omisiones">
    <header class="omisiones-header">
      <h2>Omisiones de migración</h2>
      <Button :loading="loading" data-test="refresh-omisiones" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="omisiones-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <div class="omisiones-toolbar">
      <el-input
        v-model="searchQ"
        clearable
        placeholder="Buscar en mensaje…"
        data-test="omision-search"
        class="omision-search"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-input
        v-model="filterFase"
        clearable
        placeholder="Fase (F1…F7)"
        data-test="omision-fase-filter"
        class="omision-fase"
        @keyup.enter="onFilterChange"
        @clear="onFilterChange"
      />
      <el-select
        v-model="filterNivel"
        clearable
        placeholder="Nivel"
        data-test="omision-nivel-filter"
        class="omision-nivel"
        @change="onFilterChange"
      >
        <el-option label="WARN" value="WARN" />
        <el-option label="ERROR" value="ERROR" />
      </el-select>
      <el-input
        v-model="filterHoja"
        clearable
        placeholder="Hoja"
        data-test="omision-hoja-filter"
        class="omision-hoja"
        @keyup.enter="onFilterChange"
        @clear="onFilterChange"
      />
      <el-select
        v-model="filterResuelta"
        clearable
        placeholder="Resuelta"
        data-test="omision-resuelta-filter"
        class="omision-resuelta"
        @change="onFilterChange"
      >
        <el-option label="Sí" :value="true" />
        <el-option label="No" :value="false" />
      </el-select>
    </div>

    <OmisionesTable :rows="omisiones" :loading="loading" :can-resolve="canResolve" @toggle="onToggleResuelta" />
    <Paginator
      class="tabla-paginacion"
      :total-records="total"
      :rows="pageSize"
      :first="(page - 1) * pageSize"
      template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
      @page="(e: { first: number; rows: number }) => { page = Math.floor(e.first / e.rows) + 1; load() }"
    />
  </section>
</template>

<style scoped>
.omisiones-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.omisiones-header h2 {
  margin: 0;
}

.omisiones-error {
  margin-bottom: 1rem;
}

.omisiones-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.omision-search {
  width: 16rem;
}

.omision-fase {
  width: 8rem;
}

.omision-nivel {
  width: 8rem;
}

.omision-hoja {
  width: 10rem;
}

.omision-resuelta {
  width: 9rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}
</style>
