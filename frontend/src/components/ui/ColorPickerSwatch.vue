<script setup lang="ts">
import { isLightColor } from '@/utils/color'

const props = defineProps<{
  hex: string
  selected: boolean
  label?: string
}>()

defineEmits<{ select: [hex: string] }>()
</script>

<template>
  <button
    class="w-7 h-7 rounded-md border-2 transition-all duration-100
           focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-1"
    :class="selected
      ? 'border-gray-800 shadow-sm'
      : 'border-transparent hover:scale-110 hover:border-gray-300'"
    :style="{ backgroundColor: hex }"
    :title="label ?? hex"
    :aria-label="label ?? hex"
    :aria-checked="selected"
    role="radio"
    @click="$emit('select', hex)"
  >
    <svg
      v-if="selected"
      class="w-4 h-4 mx-auto"
      :class="isLightColor(hex) ? 'text-gray-800' : 'text-white'"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      stroke-width="3"
    >
      <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  </button>
</template>
