<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Menu } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const props = defineProps<{
  menus: Menu[]
  selectedId: number | null
}>()

const emit = defineEmits<{ select: [id: number]; create: []; remove: [] }>()

const search = ref('')

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return q ? props.menus.filter((m) => m.name.toLowerCase().includes(q)) : props.menus
})
</script>

<template>
  <div class="flex flex-col gap-2 h-full p-4">
    <!-- Header: title + create button -->
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-sm">Сохранённые меню</h3>
      <button
        class="p-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        @click="emit('create')"
        title="Новое меню"
      >
        <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
    </div>

    <!-- Search -->
    <SearchInput v-model="search" />

    <!-- Menu list -->
    <ul class="flex-1 overflow-y-auto divide-y border rounded-lg min-h-0">
      <li
        v-for="m in filtered"
        :key="m.id"
        :class="m.id === selectedId ? 'bg-blue-100 font-medium' : 'hover:bg-gray-50'"
        class="px-3 py-2 cursor-pointer text-sm"
        @click="emit('select', m.id)"
      >
        {{ m.name }}
      </li>
      <li v-if="!filtered.length" class="px-3 py-4 text-sm text-gray-400 text-center">
        Нет меню
      </li>
    </ul>

    <!-- Delete button at bottom (destructive, less frequent) -->
    <button
      class="w-full px-3 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      :disabled="!selectedId"
      @click="emit('remove')"
    >
      Удалить выбранное
    </button>
  </div>
</template>
