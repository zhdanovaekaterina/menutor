<script setup lang="ts">
import { ref } from 'vue'
import type { MealIngredient } from '@/api/types'
import { formatUnit } from '@/utils/units'

const props = withDefaults(
  defineProps<{
    name: string
    quantityAmount: number
    quantityUnit: string
    subIngredients: MealIngredient[]
    depth?: number
  }>(),
  { depth: 0 },
)

const expanded = ref(false)

function formatQuantity(n: number): string {
  return String(Math.round(n * 100) / 100)
}
</script>

<template>
  <div class="mt-1 rounded border border-amber-200 bg-amber-50 overflow-hidden">
    <!-- Sub-recipe header (always visible) -->
    <button
      class="w-full flex items-center justify-between px-2 py-1.5 text-sm hover:bg-amber-100/50 transition-colors"
      @click="expanded = !expanded"
    >
      <div class="flex items-center gap-1.5 min-w-0">
        <svg
          class="w-3 h-3 text-amber-600 transition-transform shrink-0"
          :class="{ '-rotate-90': !expanded }"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
        <span class="text-amber-800 font-medium truncate">{{ name }}</span>
      </div>
      <span class="text-xs text-amber-600 whitespace-nowrap ml-2">
        {{ formatQuantity(quantityAmount) }} {{ formatUnit(quantityUnit) }}
      </span>
    </button>

    <!-- Sub-ingredients -->
    <div v-if="expanded" class="border-t border-amber-200 px-2 py-1.5 space-y-0.5">
      <template v-for="sub in subIngredients" :key="sub.product_id ?? sub.sub_recipe_id">
        <!-- Recursive: if sub also has sub_recipe_id and depth < 2, render nested SubRecipeNode -->
        <SubRecipeNode
          v-if="sub.sub_recipe_id && props.depth < 2"
          :name="sub.sub_recipe_name ?? 'Подрецепт'"
          :quantity-amount="sub.quantity_amount"
          :quantity-unit="sub.quantity_unit"
          :sub-ingredients="sub.sub_ingredients ?? []"
          :depth="props.depth + 1"
        />
        <!-- At depth >= 2, render sub-recipes inline -->
        <div
          v-else-if="sub.sub_recipe_id"
          class="flex justify-between text-sm text-amber-700 py-0.5 pl-4"
        >
          <span class="truncate">{{ sub.sub_recipe_name ?? 'Подрецепт' }} <span class="text-xs text-amber-500">(вложенный рецепт)</span></span>
          <span class="text-gray-400 whitespace-nowrap ml-2">
            {{ formatQuantity(sub.quantity_amount) }} {{ formatUnit(sub.quantity_unit) }}
          </span>
        </div>
        <!-- Regular product ingredient -->
        <div
          v-else
          class="flex justify-between text-sm text-gray-700 py-0.5 pl-4"
        >
          <span class="truncate">{{ sub.product_name }}</span>
          <span class="text-gray-400 whitespace-nowrap ml-2">
            {{ formatQuantity(sub.quantity_amount) }} {{ formatUnit(sub.quantity_unit) }}
          </span>
        </div>
      </template>
    </div>
  </div>
</template>
