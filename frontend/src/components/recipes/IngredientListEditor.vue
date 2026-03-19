<script setup lang="ts">
import { ref } from 'vue'
import type { ActiveCategory, Product, Recipe } from '@/api/types'
import IngredientTypeIcon from './IngredientTypeIcon.vue'
import IngredientPickerModal from './IngredientPickerModal.vue'

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', tsp: 'ч.л.', tbsp: 'ст.л.', pcs: 'шт', box: 'кор', pack: 'уп', serv: 'порц.',
}

const props = defineProps<{
  products: Product[]
  recipes: Recipe[]
  currentRecipeId: number | null
  ancestorIds?: Set<number>
  productCategories: ActiveCategory[]
  recipeCategories: ActiveCategory[]
}>()

const emit = defineEmits<{
  'navigate-to-recipe': [recipeId: number]
}>()

type IngredientRow = {
  product_id: number | null
  sub_recipe_id: number | null
  quantity_amount: number
  quantity_unit: string
}

const ingredients = defineModel<IngredientRow[]>({
  required: true,
})

const expanded = ref(true)
const pickerOpen = ref(false)

function isSubRecipeRow(ing: IngredientRow): boolean {
  return ing.sub_recipe_id != null
}

function subRecipeWeight(recipeId: number | null): number {
  if (recipeId == null) return 0
  return props.recipes.find((r) => r.id === recipeId)?.weight ?? 0
}

function toggleSubRecipeUnit(ing: IngredientRow, unit: 'serv' | 'g') {
  ing.quantity_unit = unit
  ing.quantity_amount = unit === 'g' ? 100 : 1
}

function productUnit(productId: number | null) {
  if (productId == null) return ''
  const p = props.products.find((pr) => pr.id === productId)
  return p ? (UNIT_MAP[p.recipe_unit] ?? p.recipe_unit) : ''
}

function remove(index: number) {
  ingredients.value.splice(index, 1)
}

type PickerDelta = {
  added: IngredientRow[]
  removedProductIds: Set<number>
  removedRecipeIds: Set<number>
}

function onPickerConfirm(delta: PickerDelta) {
  // Remove deselected ingredients
  if (delta.removedProductIds.size > 0 || delta.removedRecipeIds.size > 0) {
    ingredients.value = ingredients.value.filter((ing) => {
      if (ing.product_id != null && delta.removedProductIds.has(ing.product_id)) return false
      if (ing.sub_recipe_id != null && delta.removedRecipeIds.has(ing.sub_recipe_id)) return false
      return true
    })
  }
  // Append newly added ingredients
  for (const row of delta.added) {
    ingredients.value.push(row)
  }
}
</script>

<template>
  <div>
    <button
      type="button"
      class="flex items-center justify-between w-full bg-slate-100 px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-200 transition-colors"
      @click="expanded = !expanded"
    >
      <span>Ингредиенты</span>
      <svg
        :class="expanded ? 'rotate-180' : ''"
        class="w-4 h-4 transition-transform duration-200"
        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
      </svg>
    </button>
    <div v-show="expanded" class="pt-2 space-y-2">
      <!-- Existing ingredient rows with quantity editing and delete -->
      <div v-for="(ing, i) in ingredients" :key="i" class="flex flex-col gap-0.5">
        <div class="flex items-center gap-2">
          <!-- Sub-recipe row -->
          <template v-if="isSubRecipeRow(ing)">
            <IngredientTypeIcon type="recipe" />
            <span class="flex-1 min-w-0 truncate text-xs text-amber-800 font-medium">
              {{ recipes.find((r) => r.id === ing.sub_recipe_id)?.name ?? 'Рецепт' }}
            </span>
            <input
              v-model.number="ing.quantity_amount"
              type="number"
              min="0.01"
              step="0.01"
              class="w-16 shrink-0 border border-gray-300 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <!-- Unit toggle: порц. / г -->
            <span class="flex shrink-0 rounded overflow-hidden border border-amber-300 text-xs">
              <button
                type="button"
                class="w-8 py-1.5 transition-colors"
                :class="ing.quantity_unit === 'serv' ? 'bg-amber-400 text-white font-semibold' : 'bg-white text-amber-600 hover:bg-amber-50'"
                @click="toggleSubRecipeUnit(ing, 'serv')"
              >порц.</button>
              <button
                type="button"
                class="w-8 py-1.5 border-l border-amber-300 transition-colors"
                :class="ing.quantity_unit === 'g' ? 'bg-amber-400 text-white font-semibold' : 'bg-white text-amber-600 hover:bg-amber-50'"
                @click="toggleSubRecipeUnit(ing, 'g')"
              >г</button>
            </span>
            <button
              type="button"
              class="rounded p-1 text-amber-600 hover:text-amber-800 disabled:opacity-30 disabled:cursor-not-allowed"
              :disabled="!ing.sub_recipe_id"
              title="Перейти к рецепту"
              @click="ing.sub_recipe_id && emit('navigate-to-recipe', ing.sub_recipe_id)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </template>

          <!-- Product row -->
          <template v-else>
            <span class="flex-1 min-w-0 truncate text-xs text-gray-800">
              {{ products.find((p) => p.id === ing.product_id)?.name ?? 'Продукт' }}
            </span>
            <input
              v-model.number="ing.quantity_amount"
              type="number"
              min="0.01"
              step="0.01"
              class="w-16 shrink-0 border border-gray-300 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <span class="text-xs text-gray-500 shrink-0 w-10">{{ productUnit(ing.product_id) }}</span>
          </template>

          <button
            type="button"
            class="p-1 text-gray-400 hover:text-red-600 shrink-0 transition-colors"
            title="Удалить ингредиент"
            @click="remove(i)"
          >&times;</button>
        </div>
        <!-- Weight error: shown when unit is г but sub-recipe has no weight set -->
        <p
          v-if="isSubRecipeRow(ing) && ing.quantity_unit === 'g' && ing.sub_recipe_id != null && subRecipeWeight(ing.sub_recipe_id) === 0"
          class="text-xs text-red-500 pl-7"
        >Укажите вес рецепта или используйте порции</p>
      </div>

      <!-- Choose button -->
      <div>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-blue-600 text-blue-600 text-sm font-medium hover:bg-blue-50 transition-colors"
          @click="pickerOpen = true"
        >
          <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Выбрать
        </button>
      </div>
    </div>

    <IngredientPickerModal
      :open="pickerOpen"
      :products="products"
      :recipes="recipes"
      :current-recipe-id="currentRecipeId"
      :ancestor-ids="ancestorIds"
      :product-categories="productCategories"
      :recipe-categories="recipeCategories"
      :existing-ingredients="ingredients"
      @close="pickerOpen = false"
      @confirm="onPickerConfirm"
    />
  </div>
</template>
