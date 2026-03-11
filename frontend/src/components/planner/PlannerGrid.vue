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
}>()

const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const meals = ['Завтрак', 'Обед', 'Ужин']
</script>

<template>
  <div class="grid grid-cols-[auto_repeat(7,1fr)] gap-px bg-gray-200 rounded-lg overflow-hidden text-sm">
    <!-- Header row -->
    <div class="bg-gray-100" />
    <div
      v-for="d in days"
      :key="d"
      class="bg-gray-100 font-semibold text-center py-2"
    >
      {{ d }}
    </div>

    <!-- Meal rows -->
    <template v-for="(meal, mi) in meals" :key="meal">
      <div class="bg-gray-100 font-semibold px-3 py-2 flex items-start">{{ meal }}</div>
      <GridCell
        v-for="day in 7"
        :key="day"
        :day="day - 1"
        :meal-type="meal"
        :slots="slots"
        :recipe-names="recipeNames"
        :product-names="productNames"
        @add-item="(data) => emit('addItem', day - 1, meal, data)"
        @remove-item="(data) => emit('removeItem', day - 1, meal, data)"
        @edit-item="(slot) => emit('editItem', slot)"
      />
    </template>
  </div>
</template>
