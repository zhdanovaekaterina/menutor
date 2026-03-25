<script setup lang="ts">
import { computed } from 'vue'
import type { MenuSlot } from '@/api/types'

const props = defineProps<{
  dayIndex: number
  dayLabel: string
  slots: MenuSlot[]
  mealTypes: string[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
}>()

const emit = defineEmits<{ 'select-day': [dayIndex: number] }>()

const daySlots = computed(() => props.slots.filter(s => s.day === props.dayIndex))
const hasItems = computed(() => daySlots.value.length > 0)
const totalItems = computed(() => daySlots.value.length)

const summaryText = computed(() => {
  if (!hasItems.value) return 'Нет блюд'
  const parts: string[] = []
  for (const meal of props.mealTypes) {
    const mealSlots = daySlots.value.filter(s => s.meal_type === meal)
    if (mealSlots.length === 0) continue
    const first = mealSlots[0]
    const name = first.recipe_id != null
      ? (props.recipeNames[first.recipe_id] ?? '?')
      : (props.productNames[first.product_id!] ?? '?')
    const extra = mealSlots.length > 1 ? `, +${mealSlots.length - 1}` : ''
    parts.push(`${meal}: ${name}${extra}`)
  }
  return parts.join(' · ')
})
</script>

<template>
  <button
    class="flex-1 min-h-14 w-full flex flex-col justify-center px-4 py-2 rounded-lg border transition-all duration-150 active:scale-[0.98] active:bg-gray-50"
    :class="hasItems ? 'bg-white border-gray-200 shadow-sm' : 'bg-gray-50 border-gray-100'"
    :aria-label="`${dayLabel}, ${totalItems} блюд`"
    @click="emit('select-day', dayIndex)"
  >
    <div class="flex items-center justify-between w-full">
      <span class="text-sm font-semibold" :class="hasItems ? 'text-gray-900' : 'text-gray-400'">
        {{ dayLabel }}
      </span>
      <span class="text-xs text-gray-400">{{ totalItems }}</span>
    </div>
    <p class="text-xs mt-0.5 truncate w-full text-left" :class="hasItems ? 'text-gray-500' : 'text-gray-400'">
      {{ summaryText }}
    </p>
  </button>
</template>
