<script setup lang="ts">
import type { MenuSlot } from '@/api/types'
import WeekDayCard from './WeekDayCard.vue'

defineProps<{
  slots: MenuSlot[]
  mealTypes: string[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
}>()

const emit = defineEmits<{ 'select-day': [dayIndex: number] }>()

const dayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
</script>

<template>
  <nav aria-label="Дни недели" class="h-full flex flex-col gap-1.5 p-2">
    <WeekDayCard
      v-for="(day, i) in dayLabels"
      :key="i"
      :day-index="i"
      :day-label="day"
      :slots="slots"
      :meal-types="mealTypes"
      :recipe-names="recipeNames"
      :product-names="productNames"
      @select-day="(idx) => emit('select-day', idx)"
    />
  </nav>
</template>
