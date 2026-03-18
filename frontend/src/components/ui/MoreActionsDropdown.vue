<script setup lang="ts">
import { useDropdown } from '@/composables/useDropdown'

defineProps<{
  showDeleteAll?: boolean
}>()

const emit = defineEmits<{
  import: []
  export: []
  deleteAll: []
  selectMode: []
}>()

const { open, toggle, close } = useDropdown()
</script>

<template>
  <div class="relative" @click.stop>
    <button
      class="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
      title="Дополнительные действия"
      @click="toggle()"
    >
      <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
      </svg>
    </button>
    <div
      v-if="open"
      class="absolute right-0 top-full mt-1 w-48 bg-white border rounded-lg shadow-lg z-30 py-1"
    >
      <button
        class="sm:hidden w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50"
        @click="emit('selectMode'); close()"
      >
        Выбрать
      </button>
      <button
        class="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50"
        @click="emit('import'); close()"
      >
        Импорт
      </button>
      <button
        class="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50"
        @click="emit('export'); close()"
      >
        Экспорт
      </button>
      <template v-if="showDeleteAll">
        <div class="border-t my-1" />
        <button
          class="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50"
          @click="emit('deleteAll'); close()"
        >
          Удалить все
        </button>
      </template>
    </div>
  </div>
</template>
