<script setup lang="ts">
defineProps<{
  label: string
  active: boolean
  special?: boolean
}>()

defineEmits<{
  toggle: []
}>()
</script>

<template>
  <button
    type="button"
    :aria-pressed="active"
    :aria-label="`${label}: ${active ? 'включен' : 'выключен'}`"
    class="shrink-0 rounded-full text-sm font-medium border select-none cursor-pointer
      transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1
      h-8 px-3 lg:h-8 lg:px-3
      touch-manipulation min-w-[44px]"
    :class="special
      ? (active
        ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700 active:scale-95'
        : 'bg-gray-100 text-gray-500 border-gray-200 hover:bg-gray-200 active:scale-95')
      : (active
        ? 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-200 hover:text-blue-900 hover:border-blue-400 active:bg-blue-200'
        : 'bg-gray-100 text-gray-500 border-gray-200 hover:bg-gray-200 hover:text-gray-600 hover:border-gray-300')"
    @click="$emit('toggle')"
  >
    {{ label }}
  </button>
</template>
