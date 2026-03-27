<script setup lang="ts">
import { ref } from 'vue'
import { useDropdown } from '@/composables/useDropdown'
import IconDotsVertical from '@/components/ui/icons/IconDotsVertical.vue'

defineProps<{
  showDeleteAll?: boolean
}>()

const emit = defineEmits<{
  import: []
  export: []
  deleteAll: []
  selectMode: []
}>()

const containerRef = ref<HTMLElement | null>(null)
const { open, toggle, close } = useDropdown(containerRef)
</script>

<template>
  <div ref="containerRef" class="relative">
    <button
      class="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
      title="Дополнительные действия"
      @click="toggle()"
    >
      <IconDotsVertical class="w-5 h-5" />
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
