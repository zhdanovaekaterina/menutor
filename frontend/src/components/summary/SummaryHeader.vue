<script setup lang="ts">
defineProps<{
  menuName: string
  selectedCount: number
  totalCount: number
}>()

const emit = defineEmits<{
  back: []
  selectAll: []
  deselectAll: []
}>()
</script>

<template>
  <div class="flex items-center justify-between flex-wrap gap-2">
    <div class="flex items-center gap-2">
      <button
        class="p-2 -ml-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
        title="Вернуться в планировщик"
        @click="emit('back')"
      >
        <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
        </svg>
      </button>
      <div>
        <h1 class="text-lg sm:text-xl font-bold">Сводка блюд</h1>
        <p class="text-sm text-gray-500">{{ menuName }}</p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <span class="text-sm text-gray-400 hidden sm:inline">
        Выбрано: {{ selectedCount }} из {{ totalCount }}
      </span>
      <button
        class="px-3 py-1.5 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
        @click="emit('selectAll')"
      >
        Выбрать все
      </button>
      <button
        class="px-3 py-1.5 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
        @click="emit('deselectAll')"
      >
        Снять все
      </button>
    </div>
  </div>
</template>
