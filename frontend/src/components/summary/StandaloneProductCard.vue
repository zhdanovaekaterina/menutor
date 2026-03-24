<script setup lang="ts">
import { formatUnit } from '@/utils/units'

defineProps<{
  slotKey: string
  productName: string
  dayLabel: string
  mealTypeLabel: string
  quantity: number
  unit: string
  isSelected: boolean
}>()

const emit = defineEmits<{ toggle: [] }>()
</script>

<template>
  <div
    :class="[
      'rounded-lg border p-3 transition-all',
      isSelected
        ? 'bg-orange-50/50 border-orange-200'
        : 'bg-gray-50 border-gray-100 opacity-60',
    ]"
  >
    <div class="flex items-center gap-3">
      <!-- Checkbox with accessible touch target -->
      <button
        class="shrink-0 p-2.5 sm:p-0 -m-2.5 sm:m-0"
        :aria-checked="isSelected"
        role="checkbox"
        @click="emit('toggle')"
      >
        <div
          class="w-5 h-5 rounded border-2 flex items-center justify-center transition-colors"
          :class="
            isSelected
              ? 'bg-blue-600 border-blue-600 text-white'
              : 'border-gray-300 hover:border-gray-400'
          "
        >
          <svg v-if="isSelected" class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </div>
      </button>

      <div class="flex-1 flex items-baseline justify-between gap-2 min-w-0">
        <div class="min-w-0">
          <span class="text-xs text-gray-400">{{ dayLabel }}, {{ mealTypeLabel }}</span>
          <h3
            :class="[
              'text-sm font-medium truncate',
              isSelected ? 'text-gray-900' : 'text-gray-400 line-through',
            ]"
          >
            {{ productName }}
          </h3>
        </div>
        <span class="text-xs text-gray-500 whitespace-nowrap shrink-0">
          {{ quantity }} {{ formatUnit(unit) }}
        </span>
      </div>
    </div>
  </div>
</template>
