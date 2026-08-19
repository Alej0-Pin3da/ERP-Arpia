<script setup lang="ts">
/**
 * Nested variantes table (PR10, spec MOD-5).
 *
 * Lists the variantes of ONE selected product (lazily fetched by the view:
 * GET /productos/{id}/variantes). The backend VarianteProductoRead has NO
 * costo_adicional — only nombre_variante + precio_venta, so those are the
 * two columns; a null precio renders as an em dash. Editar/Eliminar are
 * admin-only via `canEdit`.
 *
 * Presentational: emits `edit` / `delete` with the clicked row.
 *
 * Migrated to PrimeVue DataTable (lazy) in slice 1c. Button cells were
 * migrated in slice 2b.
 */
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import type { components } from '@/types/api.d'
import { formatMoney } from '@/utils/format'

type VarianteProductoRead = components['schemas']['VarianteProductoRead']

defineProps<{
  variantes: VarianteProductoRead[]
  loading: boolean
  canEdit: boolean
}>()

defineEmits<{
  edit: [variante: VarianteProductoRead]
  delete: [variante: VarianteProductoRead]
}>()
</script>

<template>
  <DataTable :value="variantes" lazy :loading="loading">
    <Column field="nombre_variante" header="Variante" style="min-width: 160px" />
    <Column field="precio_venta" header="Precio de venta" style="min-width: 140px" align="right">
      <template #body="{ data }">
        {{ data.precio_venta == null || data.precio_venta === '' ? '—' : formatMoney(data.precio_venta) }}
      </template>
    </Column>
    <Column v-if="canEdit" header="Acciones" style="width: 180px">
      <template #body="{ data: row }">
        <Button size="small" severity="secondary" data-test="edit-variante" @click="$emit('edit', row)">Editar</Button>
        <Button size="small" severity="danger" data-test="delete-variante" @click="$emit('delete', row)">
          Eliminar
        </Button>
      </template>
    </Column>

    <template #empty>
      <div class="variante-empty">Sin variantes registradas</div>
    </template>
  </DataTable>
</template>

<style scoped>
.variante-empty {
  color: var(--arpia-text-muted);
  padding: 2rem 0;
  text-align: center;
}
</style>
