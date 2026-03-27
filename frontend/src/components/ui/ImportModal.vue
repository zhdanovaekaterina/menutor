<script setup lang="ts">
import { ref } from 'vue'
import { importEntities } from '@/api/client'
import type { ImportResult } from '@/api/types'

const props = defineProps<{
  open: boolean
  entityType: string
  allowedExtensions: string[]
}>()

const emit = defineEmits<{ close: []; imported: [result: ImportResult] }>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const error = ref('')
const result = ref<ImportResult | null>(null)

const acceptAttr = props.allowedExtensions.map((e) => `.${e}`).join(',')

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  error.value = ''
  result.value = null

  if (!file) { selectedFile.value = null; return }

  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!props.allowedExtensions.includes(ext)) {
    error.value = `Недопустимый формат. Допустимые: ${props.allowedExtensions.join(', ').toUpperCase()}`
    selectedFile.value = null
    return
  }
  selectedFile.value = file
}

async function onImport() {
  if (!selectedFile.value) return
  const ext = selectedFile.value.name.split('.').pop()?.toLowerCase() ?? ''
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const res = await importEntities(props.entityType, ext, selectedFile.value)
    result.value = res
    emit('imported', res)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Ошибка импорта'
  } finally {
    loading.value = false
  }
}

function onClose() {
  selectedFile.value = null
  error.value = ''
  result.value = null
  if (fileInput.value) fileInput.value.value = ''
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50" @mousedown.self="onClose" @touchstart.self.passive="onClose">
      <div class="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-w-md w-full sm:mx-4 p-6">
        <h3 class="text-lg font-semibold mb-4">Импорт</h3>

        <div class="space-y-4">
          <p class="text-sm text-gray-500">
            Допустимые форматы: {{ allowedExtensions.map((e) => e.toUpperCase()).join(', ') }}
          </p>

          <input
            ref="fileInput"
            type="file"
            :accept="acceptAttr"
            class="w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            @change="onFileChange"
          />

          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

          <div v-if="result" class="text-sm text-green-700 bg-green-50 rounded-lg p-3">
            <p>Создано: {{ result.created }}, Обновлено: {{ result.updated }}</p>
            <ul v-if="result.errors.length" class="mt-1 list-disc list-inside text-red-600">
              <li v-for="(e, i) in result.errors" :key="i">{{ e }}</li>
            </ul>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-6">
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="loading"
            @click="onClose"
          >
            Закрыть
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!selectedFile || loading"
            @click="onImport"
          >
            {{ loading ? 'Импорт...' : 'Импорт' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
