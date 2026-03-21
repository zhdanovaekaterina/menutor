<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { SavedShoppingListMeta } from '@/api/types'
import IconDotsVertical from '@/components/ui/icons/IconDotsVertical.vue'

const props = defineProps<{
  list: SavedShoppingListMeta
  isActive: boolean
}>()

const emit = defineEmits<{
  select: []
  rename: [newTitle: string]
  copy: []
  delete: []
}>()

// ---- Context menu ----
const menuOpen = ref(false)
const menuEl = ref<HTMLDivElement | null>(null)

function openMenu(event: MouseEvent) {
  event.stopPropagation()
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

// ---- Inline rename ----
const renaming = ref(false)
const renameValue = ref('')
const renameInputEl = ref<HTMLInputElement | null>(null)

async function startRename() {
  closeMenu()
  renaming.value = true
  renameValue.value = props.list.name
  await nextTick()
  renameInputEl.value?.focus()
  renameInputEl.value?.select()
}

function confirmRename() {
  if (!renaming.value) return
  const trimmed = renameValue.value.trim()
  renaming.value = false
  if (trimmed && trimmed !== props.list.name) {
    emit('rename', trimmed)
  }
}

function cancelRename() {
  renaming.value = false
}

function onCopy() {
  closeMenu()
  emit('copy')
}

function onDelete() {
  closeMenu()
  emit('delete')
}

// ---- Date formatting ----
function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    const day = String(d.getDate()).padStart(2, '0')
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const year = d.getFullYear()
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    return `${hours}:${minutes} ${day}.${month}.${year}`
  } catch {
    return iso
  }
}
</script>

<template>
  <li
    class="group relative px-3 py-2.5 cursor-pointer text-sm transition-colors hover:bg-gray-50"
    :class="isActive ? 'bg-blue-50 border-l-2 border-blue-600' : ''"
    @click="emit('select')"
  >
    <!-- Inline rename input -->
    <input
      v-if="renaming"
      ref="renameInputEl"
      v-model="renameValue"
      class="w-full px-2 py-1 text-sm border border-blue-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-300"
      @keydown.enter.prevent="confirmRename"
      @keydown.escape.prevent="cancelRename"
      @blur="confirmRename"
      @click.stop
    />

    <!-- Normal display -->
    <template v-else>
      <p class="font-medium truncate pr-6" :title="list.name">
        {{ list.name }}
      </p>
      <div class="flex items-center gap-2 mt-0.5">
        <span class="text-xs text-gray-400">
          {{ formatDate(list.created_at) }}
        </span>
        <span
          v-if="list.source_menu_id !== null"
          class="text-[10px] px-1.5 py-0.5 rounded-full bg-green-50 text-green-700 font-medium"
        >
          из меню
        </span>
      </div>
    </template>

    <!-- 3-dot button (always visible on touch, hover-only on desktop) -->
    <button
      class="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-gray-200 transition-opacity lg:opacity-0 lg:group-hover:opacity-100"
      @click.stop="openMenu"
    >
      <IconDotsVertical class="w-4 h-4 text-gray-400" />
    </button>

    <!-- Context dropdown -->
    <div
      v-if="menuOpen"
      ref="menuEl"
      class="absolute right-8 top-1 w-44 bg-white border rounded-lg shadow-lg z-30 py-1"
    >
      <button
        class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
        @click.stop="startRename"
      >
        Переименовать
      </button>
      <button
        class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
        @click.stop="onCopy"
      >
        Копировать
      </button>
      <div class="border-t my-1" />
      <button
        class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
        @click.stop="onDelete"
      >
        Удалить
      </button>
    </div>
  </li>

  <!-- Click outside to close menu -->
  <Teleport v-if="menuOpen" to="body">
    <div class="fixed inset-0 z-20" @click="closeMenu" @keydown.escape="closeMenu" />
  </Teleport>
</template>
