<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  recipeName: string
  portions: string
  calculatedPieces: number
  pieces: string
  showDelete?: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
  delete: []
  'update:pieces': [value: string]
}>()

const inputRef = ref<HTMLInputElement | null>(null)

const piecesError = computed(() => {
  const val = parseInt(props.pieces)
  if (isNaN(val) || val < 1) return 'Минимум 1 шт'
  return ''
})

const isValid = computed(() => !piecesError.value)

watch(
  () => props.open,
  async (v) => {
    if (v) {
      await nextTick()
      inputRef.value?.focus()
      inputRef.value?.select()
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)

function onBlur() {
  // Округление до целого
  const val = parseFloat(props.pieces)
  if (!isNaN(val)) {
    const rounded = Math.max(1, Math.round(val))
    emit('update:pieces', String(rounded))
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50" @keydown.escape="emit('cancel')" @mousedown.self="emit('cancel')" @touchstart.self.passive="emit('cancel')">
      <div class="bg-white rounded-t-2xl sm:rounded-xl shadow-xl max-w-md w-full sm:mx-4 p-6">
        <!-- Drag indicator (mobile) -->
        <div class="w-10 h-1 bg-gray-300 rounded-full mx-auto mb-4 sm:hidden" />

        <h3 class="text-lg font-semibold mb-4">Количество: {{ recipeName }}</h3>

        <!-- Порции (read-only) -->
        <label class="block text-sm font-medium text-gray-500 mb-1">Порции (авто)</label>
        <input
          :value="portions"
          type="text"
          readonly
          aria-readonly="true"
          aria-label="Порции (рассчитано автоматически)"
          class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-gray-100 text-gray-600 cursor-not-allowed mb-4"
        />

        <!-- Количество (шт) -->
        <label class="block text-sm font-medium text-gray-700 mb-1">Количество (шт)</label>
        <input
          ref="inputRef"
          :value="pieces"
          type="number"
          min="1"
          step="1"
          aria-label="Количество штук"
          :class="[
            'w-full border rounded-lg px-3 py-2 text-sm outline-none',
            piecesError
              ? 'border-red-400 focus:ring-2 focus:ring-red-400'
              : 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
          ]"
          @input="emit('update:pieces', ($event.target as HTMLInputElement).value)"
          @blur="onBlur"
          @keydown.enter="isValid && emit('confirm')"
        />
        <p v-if="piecesError" class="text-xs text-red-500 mt-1" role="alert">{{ piecesError }}</p>
        <p class="text-xs text-gray-400 mt-1">Рассчитано: {{ calculatedPieces }} шт</p>

        <div class="flex justify-between items-center mt-6">
          <button
            v-if="showDelete"
            class="lg:hidden px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm hover:bg-red-100 transition-colors"
            @click="emit('delete')"
          >
            Удалить
          </button>
          <div class="flex gap-2 ml-auto">
            <button
              class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
              @click="emit('cancel')"
            >
              Отмена
            </button>
            <button
              class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!isValid"
              @click="emit('confirm')"
            >
              ОК
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
