<script setup lang="ts">
import type { ContextMenuItem } from '@/composables/useContextMenu'
import { useContextMenu } from '@/composables/useContextMenu'

defineProps<{
  items: ContextMenuItem[]
  x: number
  y: number
}>()

const { close } = useContextMenu()
</script>

<template>
  <!-- Invisible full-screen backdrop to catch outside clicks -->
  <div
    class="fixed inset-0 z-40"
    @click="close"
    @contextmenu.prevent="close"
  />

  <!-- Menu panel, positioned at cursor -->
  <div
    class="fixed z-50 min-w-[140px] bg-white border border-gray-200 rounded-lg shadow-lg py-1 text-sm"
    :style="{ left: `${x}px`, top: `${y}px` }"
    @click.stop
  >
    <button
      v-for="item in items"
      :key="item.label"
      :disabled="item.disabled"
      :class="[
        'w-full text-left px-4 py-2 transition-colors',
        item.disabled
          ? 'text-gray-300 cursor-not-allowed'
          : 'text-gray-700 hover:bg-gray-50 active:bg-gray-100',
      ]"
      @click="!item.disabled && (item.action(), close())"
    >
      {{ item.label }}
    </button>
  </div>
</template>
