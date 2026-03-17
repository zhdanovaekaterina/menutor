<script setup lang="ts">
import { computed, ref } from 'vue'
import { exportEntities, exportExample } from '@/api/client'
import { downloadBlob } from '@/composables/useFileDownload'

const props = defineProps<{
  open: boolean
  entityType: string
  formats: { value: string; label: string }[]
  selectedIds?: number[]
}>()

const emit = defineEmits<{ close: [] }>()

const selectedFormat = ref(props.formats[0]?.value ?? '')
const compact = ref(false)
const loading = ref(false)
const error = ref('')

const effectiveFormat = computed(() => {
  if (props.entityType === 'recipes' && selectedFormat.value === 'json' && compact.value) {
    return 'json_compact'
  }
  return selectedFormat.value
})

async function onDownload() {
  loading.value = true
  error.value = ''
  try {
    const blob = await exportEntities(props.entityType, effectiveFormat.value, props.selectedIds)
    const ext = effectiveFormat.value.replace('_compact', '')
    downloadBlob(blob, `${props.entityType}.${ext}`)
    emit('close')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Ошибка экспорта'
  } finally {
    loading.value = false
  }
}

async function onDownloadExample() {
  loading.value = true
  error.value = ''
  try {
    const blob = await exportExample(props.entityType, effectiveFormat.value)
    const ext = effectiveFormat.value.replace('_compact', '')
    downloadBlob(blob, `example_${props.entityType}.${ext}`)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Ошибка загрузки примера'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50">
      <div class="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-w-md w-full sm:mx-4 p-6">
        <h3 class="text-lg font-semibold mb-4">Экспорт</h3>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Формат</label>
            <select
              v-model="selectedFormat"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="f in formats" :key="f.value" :value="f.value">{{ f.label }}</option>
            </select>
          </div>

          <label
            v-if="entityType === 'recipes' && selectedFormat === 'json'"
            class="flex items-center gap-2 text-sm text-gray-700"
          >
            <input v-model="compact" type="checkbox" class="rounded" />
            Компактный формат (без шагов и категорий)
          </label>

          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        </div>

        <div class="flex justify-end gap-2 mt-6">
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="loading"
            @click="emit('close')"
          >
            Отмена
          </button>
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="loading"
            @click="onDownloadExample"
          >
            Скачать пример
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="loading"
            @click="onDownload"
          >
            {{ loading ? 'Загрузка...' : 'Скачать' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
