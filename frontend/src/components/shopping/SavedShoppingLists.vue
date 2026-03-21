<script setup lang="ts">
import { ref } from 'vue'
import type { SavedShoppingListMeta } from '@/api/types'
import SavedShoppingListItem from './SavedShoppingListItem.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'

const props = defineProps<{
  lists: SavedShoppingListMeta[]
  selectedId: number | null
}>()

const emit = defineEmits<{
  select: [id: number]
  create: []
}>()

// Import store directly for rename/copy/delete actions
import { useShoppingListStore } from '@/stores/shoppingList'
const store = useShoppingListStore()

// ---- Delete confirmation ----
const confirmDeleteOpen = ref(false)
const deleteTargetId = ref<number | null>(null)

function requestDelete(id: number) {
  deleteTargetId.value = id
  confirmDeleteOpen.value = true
}

async function confirmDelete() {
  confirmDeleteOpen.value = false
  if (deleteTargetId.value !== null) {
    await store.remove(deleteTargetId.value)
    deleteTargetId.value = null
  }
}

function cancelDelete() {
  confirmDeleteOpen.value = false
  deleteTargetId.value = null
}

async function onRename(id: number, newTitle: string) {
  await store.rename(id, newTitle)
}

async function onCopy(id: number) {
  await store.copy(id)
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between px-3 py-2.5 border-b shrink-0">
      <h3 class="font-semibold text-sm text-gray-700">Списки покупок</h3>
      <button
        class="p-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        title="Новый список"
        @click="emit('create')"
      >
        <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="lists.length === 0"
      class="flex-1 flex flex-col items-center justify-center px-4 text-center"
    >
      <svg class="w-10 h-10 text-gray-300 mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />
      </svg>
      <p class="text-sm text-gray-400 mb-3">Нет сохранённых списков</p>
      <button
        class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors"
        @click="emit('create')"
      >
        Создать список
      </button>
      <p class="text-xs text-gray-400 mt-2">
        или сформируйте в планировщике меню
      </p>
    </div>

    <!-- List -->
    <ul v-else class="flex-1 overflow-y-auto divide-y min-h-0">
      <SavedShoppingListItem
        v-for="list in lists"
        :key="list.id"
        :list="list"
        :is-active="list.id === selectedId"
        @select="emit('select', list.id)"
        @rename="(newTitle) => onRename(list.id, newTitle)"
        @copy="onCopy(list.id)"
        @delete="requestDelete(list.id)"
      />
    </ul>

    <ConfirmDialog
      :open="confirmDeleteOpen"
      message="Удалить список покупок?"
      danger
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>
