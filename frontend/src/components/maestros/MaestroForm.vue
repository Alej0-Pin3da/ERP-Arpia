<script setup lang="ts">
/**
 * Generic maestros form (PR11, spec MOD-5).
 *
 * One form renders every master-data entity from its field config
 * (`fields` from `MAESTRO_ENTITIES`): one input per field, an email input
 * when `inputType === 'email'`. Dual mode:
 *  - create: emits the RAW values record on submit
 *  - edit: prefills every field from the row being edited and emits the
 *    current values
 * Required fields block submission with an es-CO warning. The VIEW builds
 * the typed Create/Update payload via the per-entity builders in
 * utils/maestros (the generic form cannot know the entity's API schema).
 */
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

import { showToast } from '@/utils/toast'
import type { MaestroField, MaestroRow } from '@/utils/maestros'

const props = defineProps<{
  mode: 'create' | 'edit'
  /** Field config from the entity config (drives inputs + gates). */
  fields: MaestroField[]
  /** Singular es-CO name for the submit label ("Crear Cliente"). */
  singular: string
  /** The row being edited — prefills every field in edit mode. */
  initial?: MaestroRow | null
  /** True while the parent is POSTing/PUTting — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [values: Record<string, string>] }>()

const values = ref<Record<string, string>>({})

/** (Re)initialize the field registry when the config changes. */
watch(
  () => props.fields,
  (fields) => {
    const next: Record<string, string> = {}
    for (const field of fields) next[field.key] = ''
    values.value = next
  },
  { immediate: true },
)

/** Edit mode prefills every field from the row being edited. */
watch(
  () => props.initial,
  (row) => {
    if (row) {
      const next = { ...values.value }
      for (const field of props.fields) {
        const raw = row[field.key]
        next[field.key] = typeof raw === 'string' ? raw : ''
      }
      values.value = next
    }
  },
  { immediate: true },
)

/** MOD-5: every required field must be filled (nombre on all entities). */
function submit(): void {
  for (const field of props.fields) {
    if (field.required && (values.value[field.key] ?? '').trim() === '') {
      showToast('warn', `${field.label} es obligatorio.`)
      return
    }
  }
  emit('submit', { ...values.value })
}
</script>

<template>
  <form class="maestro-form" @submit.prevent="submit">
    <div class="form-grid">
      <div v-for="field in fields" :key="field.key" class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">{{ field.label }}</label>
          <InputText
            v-model="values[field.key]"
            :type="field.inputType ?? 'text'"
            :placeholder="field.placeholder"
            :data-test="`maestro-${field.key}-input`"
          />
        </div>
      </div>
    </div>
    <div class="submit-row">
      <Button type="submit" :loading="saving" data-test="submit-maestro">
        {{ mode === 'edit' ? 'Guardar cambios' : `Crear ${singular}` }}
      </Button>
    </div>
  </form>
</template>

<style scoped>
.maestro-form {
  max-width: 48rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(24, 1fr);
  gap: 0.5rem 1rem;
}

.form-col {
  grid-column: span 24;
}

@media (min-width: 768px) {
  .form-col {
    grid-column: span var(--md, 24);
  }
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-label {
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: var(--arpia-text-primary);
}

.submit-row {
  margin-top: 0.5rem;
}
</style>