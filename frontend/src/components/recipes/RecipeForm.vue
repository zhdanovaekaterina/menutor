<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ActiveCategory, Product, Recipe, RecipeCreate } from '@/api/types'
import IngredientListEditor from './IngredientListEditor.vue'
import StepListEditor from './StepListEditor.vue'

const props = defineProps<{
  recipe: Recipe | null
  categories: ActiveCategory[]
  products: Product[]
}>()

const emit = defineEmits<{
  save: [data: RecipeCreate, id: number | null]
  remove: [id: number]
  clear: []
}>()

const name = ref('')
const categoryId = ref<number | null>(null)
const servings = ref(4)
const weight = ref(0)
const ingredients = ref<{ product_id: number | null; quantity_amount: number; quantity_unit: string }[]>([])
const steps = ref<{ order: number; description: string }[]>([])

watch(
  () => props.recipe,
  (r) => {
    if (r) {
      name.value = r.name
      categoryId.value = r.category_id
      servings.value = r.servings
      weight.value = r.weight
      ingredients.value = r.ingredients.map((i) => ({ ...i }))
      steps.value = r.steps.map((s) => ({ ...s }))
    }
  },
  { immediate: true },
)

function clearForm() {
  name.value = ''
  categoryId.value = null
  servings.value = 4
  weight.value = 0
  ingredients.value = []
  steps.value = []
  emit('clear')
}

function onSave() {
  if (!name.value.trim() || categoryId.value == null) return
  const data: RecipeCreate = {
    name: name.value.trim(),
    category_id: categoryId.value,
    servings: servings.value,
    weight: weight.value,
    ingredients: ingredients.value
      .filter((i) => i.product_id != null)
      .map((i) => ({
        product_id: i.product_id!,
        quantity_amount: i.quantity_amount,
        quantity_unit: i.quantity_unit,
      })),
    steps: steps.value,
  }
  emit('save', data, props.recipe?.id ?? null)
}
</script>

<template>
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
      <input v-model="name"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Категория *</label>
      <select v-model="categoryId"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
        <option :value="null" disabled>Выберите...</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Порций</label>
        <input v-model.number="servings" type="number" min="1" max="100"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Вес готового блюда (г)</label>
        <input v-model.number="weight" type="number" min="0"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
    </div>

    <IngredientListEditor v-model="ingredients" :products="products" />

    <StepListEditor v-model="steps" />

    <div class="flex gap-2 pt-4 border-t">
      <button class="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700" @click="onSave">
        Сохранить
      </button>
      <button v-if="recipe" class="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700"
        @click="emit('remove', recipe.id)">
        Удалить
      </button>
    </div>
  </div>
</template>
