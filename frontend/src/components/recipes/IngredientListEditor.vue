<script setup lang="ts">
import { ref } from 'vue'
import type { Product, Recipe } from '@/api/types'
import IngredientTypeIcon from './IngredientTypeIcon.vue'
import SplitButton from '@/components/ui/SplitButton.vue'

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', tsp: 'ч.л.', tbsp: 'ст.л.', pcs: 'шт', box: 'кор', pack: 'уп', serv: 'порц.',
}

const NEW_PRODUCT = -1

const props = defineProps<{
  products: Product[]
  recipes: Recipe[]
  currentRecipeId: number | null
  ancestorIds?: Set<number>
}>()

const emit = defineEmits<{
  'create-product': [index: number]
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

function isSubRecipeRow(ing: IngredientRow): boolean {
  return ing.sub_recipe_id != null || ing.quantity_unit === 'serv'
}

function productUnit(productId: number | null) {
  if (productId == null) return ''
  const p = props.products.find((pr) => pr.id === productId)
  return p ? (UNIT_MAP[p.recipe_unit] ?? p.recipe_unit) : ''
}

function defaultQuantity(unit: string) {
  return unit === 'g' ? 100 : 1
}

function onProductChange(ing: IngredientRow, index: number) {
  if (ing.product_id === NEW_PRODUCT) {
    ing.product_id = null
    emit('create-product', index)
    return
  }
  const unit = props.products.find((p) => p.id === ing.product_id)?.recipe_unit ?? 'g'
  ing.quantity_unit = unit
  ing.quantity_amount = defaultQuantity(unit)
}

function filteredRecipes(): Recipe[] {
  return props.recipes.filter((r) => {
    if (props.currentRecipeId != null && r.id === props.currentRecipeId) return false
    if (props.ancestorIds?.has(r.id)) return false
    return true
  })
}

function addProduct() {
  ingredients.value.push({ product_id: null, sub_recipe_id: null, quantity_amount: 100, quantity_unit: 'g' })
}

function addSubRecipe() {
  ingredients.value.push({ product_id: null, sub_recipe_id: null, quantity_amount: 1, quantity_unit: 'serv' })
}

function onSplitButtonClick() {
  addProduct()
}

function onSplitButtonSelect(key: string) {
  if (key === 'product') addProduct()
  else if (key === 'sub-recipe') addSubRecipe()
}

function remove(index: number) {
  ingredients.value.splice(index, 1)
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
      <div v-for="(ing, i) in ingredients" :key="i" class="flex items-center gap-2">
        <!-- Sub-recipe row -->
        <template v-if="isSubRecipeRow(ing)">
          <IngredientTypeIcon type="recipe" />
          <select
            v-model="ing.sub_recipe_id"
            class="flex-1 min-w-0 border border-amber-300 rounded px-2 py-1.5 text-xs"
          >
            <option :value="null">Рецепт...</option>
            <option v-for="r in filteredRecipes()" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
          <input
            v-model.number="ing.quantity_amount"
            type="number"
            min="0.01"
            step="0.01"
            class="w-16 shrink-0 border border-gray-300 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
          />
          <span class="text-xs text-amber-600 font-medium shrink-0 w-10">порц.</span>
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
          <select
            v-model="ing.product_id"
            class="flex-1 min-w-0 border border-gray-300 rounded px-2 py-1.5 text-xs"
            @change="onProductChange(ing, i)"
          >
            <option :value="null">Продукт...</option>
            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
            <option disabled>---</option>
            <option :value="NEW_PRODUCT">+ Создать новый...</option>
          </select>
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
      <div>
        <SplitButton
          label="+ Добавить"
          :items="[
            { key: 'product', label: 'Продукт' },
            { key: 'sub-recipe', label: 'Рецепт-ингредиент' },
          ]"
          @click="onSplitButtonClick"
          @select="onSplitButtonSelect"
        />
      </div>
    </div>
  </div>
</template>
