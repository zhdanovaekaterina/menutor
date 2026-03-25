<script setup lang="ts">
import IconChevronLeft from '@/components/ui/icons/IconChevronLeft.vue'

defineProps<{ label: string }>()
const emit = defineEmits<{ click: [] }>()
</script>

<template>
  <button
    class="flex items-center gap-1 px-2 py-1.5 -ml-1 rounded-lg text-sm text-blue-600 font-medium active:bg-blue-50 transition-colors"
    @click="emit('click')"
  >
    <IconChevronLeft class="w-4 h-4" />
    <span>{{ label }}</span>
  </button>
</template>
