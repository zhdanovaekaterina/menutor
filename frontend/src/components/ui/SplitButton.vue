<template>
  <div class="relative inline-flex">
    <button
      type="button"
      class="rounded-l-md border border-r-0 border-blue-600 bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      @click="emit('click')"
    >
      {{ label }}
    </button>
    <button
      type="button"
      class="rounded-r-md border border-blue-600 bg-blue-600 px-1.5 py-1.5 text-sm text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-label="Ещё варианты"
      @click="toggleOpen"
      @keydown.escape="close"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
      </svg>
    </button>
    <div
      v-if="open"
      class="absolute right-0 top-full z-50 mt-1 min-w-[10rem] rounded-md border border-gray-200 bg-white shadow-lg"
      role="menu"
    >
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        class="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
        role="menuitem"
        @click="selectItem(item.key)"
      >
        {{ item.label }}
      </button>
    </div>
    <!-- backdrop to close on outside click -->
    <div v-if="open" class="fixed inset-0 z-40" @click="close" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  label: string
  items: { key: string; label: string }[]
}>()

const emit = defineEmits<{
  click: []
  select: [key: string]
}>()

const open = ref(false)

function toggleOpen() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function selectItem(key: string) {
  emit('select', key)
  close()
}
</script>
