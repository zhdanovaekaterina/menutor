<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MealIngredient } from '@/api/types'
import { formatUnit } from '@/utils/units'
import SubRecipeNode from './SubRecipeNode.vue'

const props = withDefaults(
  defineProps<{
    ingredients: MealIngredient[]
    initiallyExpanded?: boolean
  }>(),
  { initiallyExpanded: false },
)

const expanded = ref(props.initiallyExpanded)

const regularIngredients = computed(() =>
  props.ingredients.filter((i) => !i.sub_recipe_id),
)

const subRecipes = computed(() =>
  props.ingredients.filter((i) => !!i.sub_recipe_id),
)

const ingredientCount = computed(() => regularIngredients.value.length)
const subRecipeCount = computed(() => subRecipes.value.length)

function formatQuantity(n: number): string {
  return String(Math.round(n * 100) / 100)
}

function ingredientKey(ing: MealIngredient): string {
  if (ing.sub_recipe_id) return `sr-${ing.sub_recipe_id}`
  return `p-${ing.product_id}`
}
</script>

<template>
  <div>
    <!-- Toggle -->
    <button
      class="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
      @click="expanded = !expanded"
    >
      <svg
        class="w-3 h-3 transition-transform"
        :class="{ '-rotate-90': !expanded }"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
      <span>
        Ингредиенты ({{ ingredientCount
        }}<template v-if="subRecipeCount">
          + {{ subRecipeCount }}
          {{ subRecipeCount === 1 ? 'подрецепт' : 'подрецептов' }}</template
        >)
      </span>
    </button>

    <!-- Ingredient list -->
    <Transition name="collapse">
      <div v-if="expanded" class="mt-1.5 space-y-0.5">
        <template v-for="ing in ingredients" :key="ingredientKey(ing)">
          <!-- Sub-recipe node -->
          <SubRecipeNode
            v-if="ing.sub_recipe_id"
            :name="ing.sub_recipe_name ?? 'Подрецепт'"
            :quantity-amount="ing.quantity_amount"
            :quantity-unit="ing.quantity_unit"
            :sub-ingredients="ing.sub_ingredients ?? []"
          />
          <!-- Regular ingredient -->
          <div
            v-else
            class="flex justify-between text-sm text-gray-700 py-0.5 px-2"
          >
            <span class="truncate">{{ ing.product_name }}</span>
            <span class="text-gray-400 whitespace-nowrap ml-2">
              {{ formatQuantity(ing.quantity_amount) }} {{ formatUnit(ing.quantity_unit) }}
            </span>
          </div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
}
.collapse-enter-to,
.collapse-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>
