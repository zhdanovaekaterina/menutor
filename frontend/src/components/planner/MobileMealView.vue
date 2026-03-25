<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MenuSlot } from '@/api/types'
import { useSwipeGesture } from '@/composables/useSwipeGesture'
import GridCell from './GridCell.vue'
import ModeBackButton from './ModeBackButton.vue'
import IconChevronUp from '@/components/ui/icons/IconChevronUp.vue'
import IconChevronDown from '@/components/ui/icons/IconChevronDown.vue'

const props = defineProps<{
  currentDay: number
  currentMealType: string
  slots: MenuSlot[]
  mealTypes: string[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  pickerDay?: number | null
  pickerMealType?: string | null
}>()

const emit = defineEmits<{
  'navigate-to-day': []
  'navigate-day': [delta: number]
  'navigate-meal-type': [delta: number]
  'bounce': [direction: 'left' | 'right' | 'up' | 'down']
  'add-item': [day: number, mealType: string, data: { type: 'recipe' | 'product'; id: number }]
  'remove-item': [day: number, mealType: string, data: { recipe_id?: number | null; product_id?: number | null }]
  'edit-item': [slot: MenuSlot]
  'move-item': [slot: MenuSlot, toDay: number, toMealType: string, toIndex: number]
  'reorder-items': [day: number, mealType: string, orderedSlots: MenuSlot[]]
  'open-picker': [day: number, mealType: string]
}>()

const dayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const isFirstMealType = computed(() => props.mealTypes.indexOf(props.currentMealType) === 0)
const isLastMealType = computed(() => props.mealTypes.indexOf(props.currentMealType) === props.mealTypes.length - 1)

const bounceClass = ref('')

function triggerBounce(direction: string) {
  bounceClass.value = `bounce-${direction}`
  setTimeout(() => { bounceClass.value = '' }, 300)
}

const { swipeHandlers } = useSwipeGesture({
  axis: 'both',
  threshold: 50,
  edgeGuard: 20,
  onSwipe(direction) {
    if (direction === 'left') emit('navigate-day', +1)
    else if (direction === 'right') emit('navigate-day', -1)
    else if (direction === 'up') emit('navigate-meal-type', +1)
    else if (direction === 'down') emit('navigate-meal-type', -1)
  },
  onBounce(direction) {
    triggerBounce(direction)
    emit('bounce', direction)
  },
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Nav bar -->
    <div class="flex items-center justify-between px-3 py-2 bg-white border-b border-gray-100 shrink-0">
      <ModeBackButton label="День" @click="emit('navigate-to-day')" />
      <div class="flex flex-col items-center">
        <span class="text-sm font-semibold text-gray-900">{{ dayLabels[currentDay] }}</span>
        <span class="text-xs text-gray-500">{{ currentMealType }}</span>
      </div>
      <div class="flex flex-col items-center gap-0.5">
        <button
          class="p-1.5 rounded text-gray-400 active:bg-gray-100 disabled:opacity-30"
          :disabled="isFirstMealType"
          aria-label="Предыдущий тип приема пищи"
          @click="emit('navigate-meal-type', -1)"
        >
          <IconChevronUp class="w-3.5 h-3.5" />
        </button>
        <button
          class="p-1.5 rounded text-gray-400 active:bg-gray-100 disabled:opacity-30"
          :disabled="isLastMealType"
          aria-label="Следующий тип приема пищи"
          @click="emit('navigate-meal-type', +1)"
        >
          <IconChevronDown class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Full-screen cell -->
    <div class="flex-1 p-3" :class="bounceClass" v-bind="swipeHandlers" style="touch-action: none;">
      <GridCell
        size="full"
        :day="currentDay"
        :meal-type="currentMealType"
        :slots="slots"
        :recipe-names="recipeNames"
        :product-names="productNames"
        :picker-active="pickerDay === currentDay && pickerMealType === currentMealType"
        @add-item="(data) => emit('add-item', currentDay, currentMealType, data)"
        @remove-item="(data) => emit('remove-item', currentDay, currentMealType, data)"
        @edit-item="(slot) => emit('edit-item', slot)"
        @move-item="(slot, d, m, idx) => emit('move-item', slot, d, m, idx)"
        @reorder-items="(d, m, ordered) => emit('reorder-items', d, m, ordered)"
        @open-picker="emit('open-picker', currentDay, currentMealType)"
      />
    </div>

    <!-- Day indicator -->
    <div class="flex justify-center items-center gap-2 py-1.5 shrink-0">
      <span
        v-for="(day, i) in dayLabels"
        :key="i"
        class="text-xs px-1.5 py-0.5 rounded transition-colors duration-200"
        :class="i === currentDay ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-400'"
      >
        {{ day }}
      </span>
    </div>

    <!-- Meal type indicator -->
    <div class="flex justify-center items-center gap-3 py-1 pb-2 shrink-0">
      <span
        v-for="meal in mealTypes"
        :key="meal"
        class="text-xs transition-colors duration-200"
        :class="meal === currentMealType ? 'text-blue-700 font-semibold' : 'text-gray-400'"
      >
        {{ meal }}
      </span>
    </div>
  </div>
</template>
