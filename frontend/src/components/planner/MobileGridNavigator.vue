<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { MenuSlot } from '@/api/types'
import MobileWeekView from './MobileWeekView.vue'
import MobileDayView from './MobileDayView.vue'
import MobileMealView from './MobileMealView.vue'

const props = defineProps<{
  slots: MenuSlot[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  pickerDay?: number | null
  pickerMealType?: string | null
  menuId?: number | null
}>()

const emit = defineEmits<{
  'add-item': [day: number, mealType: string, data: { type: 'recipe' | 'product'; id: number }]
  'remove-item': [day: number, mealType: string, data: { recipe_id?: number | null; product_id?: number | null }]
  'edit-item': [slot: MenuSlot]
  'move-item': [slot: MenuSlot, toDay: number, toMealType: string, toIndex: number]
  'reorder-items': [day: number, mealType: string, orderedSlots: MenuSlot[]]
  'open-picker': [day: number, mealType: string]
  'day-scrolled': []
}>()

type Mode = 'week' | 'day' | 'meal'

const mode = ref<Mode>('week')
const currentDay = ref(0)
const currentMealType = ref('')
const transitionName = ref('mode-zoom')
const meals = ['Завтрак', 'Обед', 'Ужин']

// Reset to week view when menu changes
watch(() => props.menuId, () => {
  mode.value = 'week'
  currentDay.value = 0
  currentMealType.value = ''
})

function goToDay(dayIndex: number) {
  currentDay.value = dayIndex
  transitionName.value = 'mode-zoom'
  mode.value = 'day'
}

function goToWeek() {
  transitionName.value = 'mode-zoom'
  mode.value = 'week'
}

function goToMeal(mealType: string) {
  currentMealType.value = mealType
  transitionName.value = 'mode-drill'
  mode.value = 'meal'
}

function goBackToDay() {
  transitionName.value = 'mode-drill'
  mode.value = 'day'
}

function onNavigateDay(delta: number) {
  const next = currentDay.value + delta
  if (next < 0 || next > 6) return
  currentDay.value = next
  emit('day-scrolled')
}

function onNavigateMealType(delta: number) {
  const idx = meals.indexOf(currentMealType.value)
  const next = idx + delta
  if (next < 0 || next >= meals.length) return
  currentMealType.value = meals[next]
}

const dayLabelsFull = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

const liveAnnouncement = computed(() => {
  if (mode.value === 'week') return 'Обзор недели'
  if (mode.value === 'day') {
    const daySlots = props.slots.filter(s => s.day === currentDay.value)
    return `${dayLabelsFull[currentDay.value]}, ${daySlots.length} блюд`
  }
  const mealSlots = props.slots.filter(s => s.day === currentDay.value && s.meal_type === currentMealType.value)
  return `${dayLabelsFull[currentDay.value]}, ${currentMealType.value}, ${mealSlots.length} блюд`
})
</script>

<template>
  <div class="h-full" role="region">
    <div class="sr-only" aria-live="polite" aria-atomic="true">{{ liveAnnouncement }}</div>

    <Transition :name="transitionName" mode="out-in">
      <MobileWeekView
        v-if="mode === 'week'"
        key="week"
        :slots="slots"
        :meal-types="meals"
        :recipe-names="recipeNames"
        :product-names="productNames"
        @select-day="goToDay"
      />

      <MobileDayView
        v-else-if="mode === 'day'"
        key="day"
        :current-day="currentDay"
        :slots="slots"
        :meal-types="meals"
        :recipe-names="recipeNames"
        :product-names="productNames"
        :picker-day="pickerDay"
        :picker-meal-type="pickerMealType"
        @navigate-to-week="goToWeek"
        @navigate-to-meal="goToMeal"
        @navigate-day="onNavigateDay"
        @add-item="(d, m, data) => emit('add-item', d, m, data)"
        @remove-item="(d, m, data) => emit('remove-item', d, m, data)"
        @edit-item="(slot) => emit('edit-item', slot)"
        @move-item="(slot, d, m, idx) => emit('move-item', slot, d, m, idx)"
        @reorder-items="(d, m, ordered) => emit('reorder-items', d, m, ordered)"
        @open-picker="(d, m) => emit('open-picker', d, m)"
      />

      <MobileMealView
        v-else
        key="meal"
        :current-day="currentDay"
        :current-meal-type="currentMealType"
        :slots="slots"
        :meal-types="meals"
        :recipe-names="recipeNames"
        :product-names="productNames"
        :picker-day="pickerDay"
        :picker-meal-type="pickerMealType"
        @navigate-to-day="goBackToDay"
        @navigate-day="onNavigateDay"
        @navigate-meal-type="onNavigateMealType"
        @add-item="(d, m, data) => emit('add-item', d, m, data)"
        @remove-item="(d, m, data) => emit('remove-item', d, m, data)"
        @edit-item="(slot) => emit('edit-item', slot)"
        @move-item="(slot, d, m, idx) => emit('move-item', slot, d, m, idx)"
        @reorder-items="(d, m, ordered) => emit('reorder-items', d, m, ordered)"
        @open-picker="(d, m) => emit('open-picker', d, m)"
      />
    </Transition>
  </div>
</template>
