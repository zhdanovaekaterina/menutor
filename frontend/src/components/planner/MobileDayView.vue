<script setup lang="ts">
import type { FamilyMember, MenuSlot } from '@/api/types'
import { useSwipeGesture } from '@/composables/useSwipeGesture'
import GridCell from './GridCell.vue'
import ModeBackButton from './ModeBackButton.vue'
import IconChevronLeft from '@/components/ui/icons/IconChevronLeft.vue'
import IconChevronRight from '@/components/ui/icons/IconChevronRight.vue'

const props = defineProps<{
  currentDay: number
  slots: MenuSlot[]
  mealTypes: { id: number; name: string }[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  pickerDay?: number | null
  pickerMealTypeId?: number | null
  activeMemberIds?: Set<number>
  allActive?: boolean
  familyMembers?: FamilyMember[]
}>()

const emit = defineEmits<{
  'navigate-to-week': []
  'navigate-to-meal': [mealTypeId: number]
  'navigate-day': [delta: number]
  'add-item': [day: number, mealTypeId: number, data: { type: 'recipe' | 'product'; id: number }]
  'remove-item': [day: number, mealTypeId: number, data: { recipe_id?: number | null; product_id?: number | null }]
  'edit-item': [slot: MenuSlot]
  'move-item': [slot: MenuSlot, toDay: number, toMealTypeId: number, toIndex: number]
  'reorder-items': [day: number, mealTypeId: number, orderedSlots: MenuSlot[]]
  'open-picker': [day: number, mealTypeId: number]
}>()

const dayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const { swipeHandlers } = useSwipeGesture({
  axis: 'horizontal',
  threshold: 50,
  edgeGuard: 20,
  onSwipe(direction) {
    if (direction === 'left') emit('navigate-day', +1)
    else if (direction === 'right') emit('navigate-day', -1)
  },
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Nav bar -->
    <div class="flex items-center justify-between px-3 py-2 bg-white border-b border-gray-100 shrink-0">
      <ModeBackButton label="Неделя" @click="emit('navigate-to-week')" />
      <span class="text-sm font-semibold text-gray-900">{{ dayLabels[currentDay] }}</span>
      <div class="flex items-center gap-1">
        <button
          class="p-2 rounded-lg text-gray-400 active:bg-gray-100 disabled:opacity-30"
          :disabled="currentDay === 0"
          aria-label="Предыдущий день"
          @click="emit('navigate-day', -1)"
        >
          <IconChevronLeft class="w-4 h-4" />
        </button>
        <button
          class="p-2 rounded-lg text-gray-400 active:bg-gray-100 disabled:opacity-30"
          :disabled="currentDay === 6"
          aria-label="Следующий день"
          @click="emit('navigate-day', +1)"
        >
          <IconChevronRight class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Swipe area -->
    <div class="flex-1 flex flex-col min-h-0" v-bind="swipeHandlers" style="touch-action: pan-y;">
      <div v-for="mt in mealTypes" :key="mt.id" class="flex-1 flex flex-col min-h-0 border-b border-gray-100 last:border-b-0">
        <!-- Meal type header — tap to drill in -->
        <button
          class="w-full flex items-center justify-between px-3 py-2.5 bg-gray-50 active:bg-gray-100 transition-colors shrink-0"
          @click="emit('navigate-to-meal', mt.id)"
        >
          <span class="text-sm font-semibold text-gray-700">{{ mt.name }}</span>
          <IconChevronRight class="w-4 h-4 text-gray-400" />
        </button>
        <!-- Cell with items -->
        <GridCell
          class="flex-1"
          :day="currentDay"
          :meal-type-id="mt.id"
          :slots="slots"
          :recipe-names="recipeNames"
          :product-names="productNames"
          :picker-active="pickerDay === currentDay && pickerMealTypeId === mt.id"
          :active-member-ids="activeMemberIds"
          :all-active="allActive"
          :family-members="familyMembers"
          @add-item="(data) => emit('add-item', currentDay, mt.id, data)"
          @remove-item="(data) => emit('remove-item', currentDay, mt.id, data)"
          @edit-item="(slot) => emit('edit-item', slot)"
          @move-item="(slot, d, m, idx) => emit('move-item', slot, d, m, idx)"
          @reorder-items="(d, m, ordered) => emit('reorder-items', d, m, ordered)"
          @open-picker="emit('open-picker', currentDay, mt.id)"
        />
      </div>
    </div>

    <!-- Day indicator dots -->
    <div class="flex justify-center gap-1.5 py-2 shrink-0">
      <span
        v-for="i in 7"
        :key="i"
        class="w-1.5 h-1.5 rounded-full transition-colors duration-200"
        :class="i - 1 === currentDay ? 'bg-blue-500' : 'bg-gray-300'"
      />
    </div>
  </div>
</template>
