<script setup lang="ts">
import type { MenuSlot } from '@/api/types'
import GridCell from './GridCell.vue'
import MobileGridNavigator from './MobileGridNavigator.vue'

defineProps<{
  slots: MenuSlot[]
  recipeNames: Record<number, string>
  productNames: Record<number, string>
  pickerDay?: number | null
  pickerMealType?: string | null
  menuId?: number | null
}>()

const emit = defineEmits<{
  addItem: [day: number, mealType: string, data: { type: 'recipe' | 'product'; id: number }]
  removeItem: [day: number, mealType: string, data: { recipe_id?: number | null; product_id?: number | null }]
  editItem: [slot: MenuSlot]
  moveItem: [slot: MenuSlot, toDay: number, toMealType: string, toIndex: number]
  reorderItems: [day: number, mealType: string, orderedSlots: MenuSlot[]]
  openPicker: [day: number, mealType: string]
  dayScrolled: []
}>()

const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const meals = ['Завтрак', 'Обед', 'Ужин']
</script>

<template>
  <!-- Mobile: three-mode navigation (hidden on lg+) -->
  <MobileGridNavigator
    class="lg:hidden h-full"
    :slots="slots"
    :recipe-names="recipeNames"
    :product-names="productNames"
    :picker-day="pickerDay"
    :picker-meal-type="pickerMealType"
    :menu-id="menuId"
    @add-item="(d, m, data) => emit('addItem', d, m, data)"
    @remove-item="(d, m, data) => emit('removeItem', d, m, data)"
    @edit-item="(slot) => emit('editItem', slot)"
    @move-item="(slot, d, m, idx) => emit('moveItem', slot, d, m, idx)"
    @reorder-items="(d, m, ordered) => emit('reorderItems', d, m, ordered)"
    @open-picker="(d, m) => emit('openPicker', d, m)"
    @day-scrolled="emit('dayScrolled')"
  />

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
