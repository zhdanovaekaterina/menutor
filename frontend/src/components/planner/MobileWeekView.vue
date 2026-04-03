<script setup lang="ts">
import type { FamilyMember, MenuSlot } from '@/api/types'
import { isSlotVisible } from '@/utils/slotVisibility'
import WeekDayCard from './WeekDayCard.vue'

const props = defineProps<{
  slots: MenuSlot[]
  mealTypes: { id: number; name: string }[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  activeMemberIds?: Set<number>
  allActive?: boolean
  familyMembers?: FamilyMember[]
}>()

const emit = defineEmits<{ 'select-day': [dayIndex: number] }>()

const dayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

function visibleSlots(slots: MenuSlot[]): MenuSlot[] {
  const activeIds = props.activeMemberIds
  if (!activeIds || activeIds.size === 0) return slots
  return slots.filter(s => isSlotVisible(s, activeIds))
}
</script>

<template>
  <nav aria-label="Дни недели" class="h-full flex flex-col gap-1.5 p-2">
    <WeekDayCard
      v-for="(day, i) in dayLabels"
      :key="i"
      :day-index="i"
      :day-label="day"
      :slots="visibleSlots(slots)"
      :meal-types="mealTypes"
      :recipe-names="recipeNames"
      :product-names="productNames"
      @select-day="(idx) => emit('select-day', idx)"
    />
  </nav>
</template>
