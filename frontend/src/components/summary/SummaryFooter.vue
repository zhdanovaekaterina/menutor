<script setup lang="ts">
defineProps<{
  selectedCount: number
  totalCount: number
  generating: boolean
}>()

const emit = defineEmits<{ generate: [] }>()
</script>

<template>
  <!-- Desktop: inline at bottom of view -->
  <div class="hidden lg:flex items-center justify-between pt-3 border-t">
    <div class="flex items-center gap-4 text-sm text-gray-500">
      <span>
        Выбрано: <strong class="text-gray-900">{{ selectedCount }}</strong> из {{ totalCount }}
      </span>
    </div>
    <div class="flex flex-col items-end gap-1">
      <button
        class="px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        :disabled="selectedCount === 0 || generating"
        @click="emit('generate')"
      >
        <svg v-if="generating" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <svg v-else class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
        </svg>
        Сформировать список покупок
      </button>
      <p v-if="selectedCount === 0" class="text-xs text-amber-600">
        Выберите хотя бы одно блюдо
      </p>
    </div>
  </div>

  <!-- Mobile: sticky bottom bar above bottom nav -->
  <div class="lg:hidden fixed bottom-16 inset-x-0 bg-white border-t shadow-lg px-3 py-2.5 z-30">
    <div class="flex items-center justify-between">
      <div class="text-sm text-gray-500">
        <span class="font-medium text-gray-900">{{ selectedCount }}</span>/{{ totalCount }}
        <p v-if="selectedCount === 0" class="text-xs text-amber-600">
          Выберите хотя бы одно блюдо
        </p>
      </div>
      <button
        class="px-3 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
        :disabled="selectedCount === 0 || generating"
        @click="emit('generate')"
      >
        <svg v-if="generating" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <svg v-else class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
        </svg>
        <span>Список</span>
      </button>
    </div>
  </div>
</template>
