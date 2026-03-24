<script setup lang="ts">
import { ref } from 'vue'
import type { MealIngredient } from '@/api/types'
import { formatUnit } from '@/utils/units'

export interface NestedRecipeSummary {
  sub_recipe_id: number
  sub_recipe_name: string
  total_quantity_amount: number
  quantity_unit: string
  ingredients: MealIngredient[]
}

const props = defineProps<{
  nested: NestedRecipeSummary
  isSelected: boolean
}>()

const emit = defineEmits<{ toggle: [] }>()

const expanded = ref(true)

function formatQuantity(n: number): string {
  return String(Math.round(n * 100) / 100)
}
</script>

<template>
  <div
    :class="[
      'rounded-xl border transition-all',
      isSelected
        ? 'bg-white border-amber-200'
        : 'bg-amber-50/30 border-amber-100 opacity-60',
    ]"
  >
    <!-- Card header row -->
    <div class="flex items-center gap-3 px-3 sm:px-4 py-3">
      <!-- Checkbox -->
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
              ? 'bg-amber-500 border-amber-500 text-white'
              : 'border-gray-300 hover:border-gray-400'
          "
        >
          <svg v-if="isSelected" class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </div>
      </button>

      <!-- Sub-recipe name + total -->
      <div class="flex-1 min-w-0">
        <h3
          :class="[
            'text-sm font-semibold truncate',
            isSelected ? 'text-amber-900' : 'text-gray-400',
          ]"
        >
          {{ nested.sub_recipe_name }}
        </h3>
        <p
          :class="[
            'text-xs mt-0.5',
            isSelected ? 'text-amber-600' : 'text-gray-400 line-through',
          ]"
        >
          {{ formatQuantity(nested.total_quantity_amount) }} {{ formatUnit(nested.quantity_unit) }} итого
        </p>
      </div>

      <!-- Expand/collapse -->
      <button
        class="shrink-0 p-1.5 rounded-lg hover:bg-amber-50 text-amber-400 hover:text-amber-600 transition-colors"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        <svg
          class="w-4 h-4 transition-transform duration-200"
          :class="{ 'rotate-180': expanded }"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Expandable ingredients -->
    <Transition name="expand">
      <div v-if="expanded" class="border-t border-amber-100 px-3 sm:px-4 py-2.5">
        <p class="text-xs font-medium text-amber-400 uppercase tracking-wide mb-2">Ингредиенты</p>
        <template v-if="nested.ingredients.length === 0">
          <p class="text-xs text-gray-300 italic">Нет ингредиентов</p>
        </template>
        <ul v-else class="space-y-0.5">
          <li
            v-for="(ing, i) in nested.ingredients"
            :key="ing.sub_recipe_id != null ? `sr-${ing.sub_recipe_id}` : `p-${ing.product_id ?? i}`"
            class="flex items-baseline justify-between gap-2 text-sm py-0.5"
          >
            <span class="flex items-center gap-1.5 min-w-0 text-gray-700">
              <span class="shrink-0 w-1 h-1 rounded-full bg-amber-400 mt-0.5" />
              <span class="truncate">{{ ing.product_name || ing.sub_recipe_name }}</span>
            </span>
            <span class="text-gray-400 whitespace-nowrap shrink-0 text-xs">
              {{ formatQuantity(ing.quantity_amount) }} {{ formatUnit(ing.quantity_unit) }}
            </span>
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
.expand-enter-to,
.expand-leave-from {
  max-height: 800px;
  opacity: 1;
}
</style>
