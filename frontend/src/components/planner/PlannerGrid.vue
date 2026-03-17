<script setup lang="ts">
import type { MenuSlot } from '@/api/types'
import GridCell from './GridCell.vue'

defineProps<{
  slots: MenuSlot[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
}>()

const emit = defineEmits<{
  addItem: [day: number, mealType: string, data: { type: 'recipe' | 'product'; id: number }]
  removeItem: [day: number, mealType: string, data: { recipe_id?: number | null; product_id?: number | null }]
  editItem: [slot: MenuSlot]
  moveItem: [slot: MenuSlot, toDay: number, toMealType: string, toIndex: number]
  reorderItems: [day: number, mealType: string, orderedSlots: MenuSlot[]]
}>()

const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const meals = ['Завтрак', 'Обед', 'Ужин']
</script>

<template>
  <!-- Mobile: snap-scroll one-day-at-a-time layout (hidden on lg+) -->
  <div class="lg:hidden h-full flex gap-px bg-gray-200 rounded-lg overflow-hidden text-sm">
    <!-- Fixed left column: meal-type labels -->
    <div class="w-[60px] shrink-0 flex flex-col bg-gray-100 gap-px">
      <!-- Spacer matching day-header height -->
      <div class="h-9 shrink-0 bg-gray-100" />
      <div
        v-for="meal in meals"
        :key="'label-' + meal"
        class="flex-1 bg-gray-100 font-semibold text-xs px-2 py-2 flex items-center"
      >
        {{ meal }}
      </div>
    </div>

    <!-- Swipeable day columns -->
    <div class="flex-1 flex overflow-x-auto snap-x snap-mandatory scroll-smooth">
      <div
        v-for="(day, i) in days"
        :key="'day-' + day"
        class="min-w-full h-full flex flex-col gap-px snap-start"
      >
        <!-- Day header (stays at top, does not scroll) -->
        <div class="h-9 shrink-0 bg-gray-100 font-semibold text-center flex items-center justify-center">
          {{ day }}
        </div>
        <!-- Meal cells — flex-1 so they share height equally -->
        <GridCell
          v-for="meal in meals"
          :key="'cell-' + i + '-' + meal"
          class="flex-1"
          :day="i"
          :meal-type="meal"
          :slots="slots"
          :recipe-names="recipeNames"
          :product-names="productNames"
          @add-item="(data) => emit('addItem', i, meal, data)"
          @remove-item="(data) => emit('removeItem', i, meal, data)"
          @edit-item="(slot) => emit('editItem', slot)"
          @move-item="(slot, toDay, toMeal, toIdx) => emit('moveItem', slot, toDay, toMeal, toIdx)"
          @reorder-items="(d, m, ordered) => emit('reorderItems', d, m, ordered)"
        />
      </div>
    </div>
  </div>

  <!-- Desktop: original CSS grid layout (hidden below lg) -->
  <div class="hidden lg:grid h-full min-w-[700px] grid-cols-[60px_repeat(7,1fr)] grid-rows-[auto_repeat(3,1fr)] gap-px bg-gray-200 rounded-lg overflow-hidden text-sm">
    <!-- Header row -->
    <div class="bg-gray-100" />
    <div
      v-for="d in days"
      :key="'hd-' + d"
      class="bg-gray-100 font-semibold text-center py-2"
    >
      {{ d }}
    </div>

    <!-- Meal rows -->
    <template v-for="(meal, mi) in meals" :key="'row-' + meal">
      <div class="bg-gray-100 font-semibold px-3 py-2 flex items-start">{{ meal }}</div>
      <GridCell
        v-for="day in 7"
        :key="'gc-' + day + '-' + meal"
        :day="day - 1"
        :meal-type="meal"
        :slots="slots"
        :recipe-names="recipeNames"
        :product-names="productNames"
        @add-item="(data) => emit('addItem', day - 1, meal, data)"
        @remove-item="(data) => emit('removeItem', day - 1, meal, data)"
        @edit-item="(slot) => emit('editItem', slot)"
        @move-item="(slot, toDay, toMeal, toIdx) => emit('moveItem', slot, toDay, toMeal, toIdx)"
        @reorder-items="(d, m, ordered) => emit('reorderItems', d, m, ordered)"
      />
    </template>
  </div>
</template>
