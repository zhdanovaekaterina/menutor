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
  <div class="flex flex-col gap-2 h-full">
    <h3 class="font-semibold text-sm">Сохранённые меню</h3>
    <SearchInput v-model="search" />
    <ul class="flex-1 overflow-y-auto divide-y border rounded-lg">
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
    <div class="flex flex-col gap-2 pt-2 border-t">
      <button
        class="w-full px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
        @click="emit('create')"
      >
        + Новое меню
      </button>
      <button
        class="w-full px-3 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50"
        :disabled="!selectedId"
        @click="emit('remove')"
      >
        Удалить
      </button>
    </div>
  </div>
</template>
