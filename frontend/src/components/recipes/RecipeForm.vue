<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ActiveCategory, Product, Recipe, RecipeCreate } from '@/api/types'

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', pcs: 'шт', box: 'кор', pack: 'уп',
}

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
const newStep = ref('')

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

function productUnit(productId: number | null) {
  if (productId == null) return ''
  const p = props.products.find((pr) => pr.id === productId)
  return p ? (UNIT_MAP[p.recipe_unit] ?? p.recipe_unit) : ''
}

function addIngredient() {
  ingredients.value.push({ product_id: null, quantity_amount: 100, quantity_unit: 'g' })
}

function removeIngredient() {
  ingredients.value.pop()
}

function addStep() {
  if (!newStep.value.trim()) return
  steps.value.push({ order: steps.value.length + 1, description: newStep.value.trim() })
  newStep.value = ''
}

function removeStep() {
  steps.value.pop()
}

function clearForm() {
  name.value = ''
  categoryId.value = null
  servings.value = 4
  weight.value = 0
  ingredients.value = []
  steps.value = []
  newStep.value = ''
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
        <label class="block text-sm font-medium text-gray-700 mb-1">Вес (г)</label>
        <input v-model.number="weight" type="number" min="0"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      </div>
    </div>

    <!-- Ingredients -->
    <details open>
      <summary class="bg-slate-200 px-3 py-2 rounded font-medium text-sm cursor-pointer select-none hover:bg-slate-300">
        Ингредиенты
      </summary>
      <div class="pt-2 space-y-2">
        <div v-for="(ing, i) in ingredients" :key="i" class="flex gap-2 items-center">
          <select v-model="ing.product_id"
            class="flex-1 border border-gray-300 rounded px-2 py-1 text-xs"
            @change="ing.quantity_unit = products.find(p => p.id === ing.product_id)?.recipe_unit ?? 'g'">
            <option :value="null">Продукт...</option>
            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
          <input v-model.number="ing.quantity_amount" type="number" min="0.01" step="0.01"
            class="w-20 border border-gray-300 rounded px-2 py-1 text-xs" />
          <span class="text-xs text-gray-500 w-8">{{ productUnit(ing.product_id) }}</span>
        </div>
        <div class="flex gap-2">
          <button class="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50" @click="addIngredient">+ Добавить</button>
          <button class="px-3 py-1 text-xs rounded border border-gray-300 text-red-600 hover:bg-red-50" @click="removeIngredient">− Удалить</button>
        </div>
      </div>
    </details>

    <!-- Steps -->
    <details open>
      <summary class="bg-slate-200 px-3 py-2 rounded font-medium text-sm cursor-pointer select-none hover:bg-slate-300">
        Шаги приготовления
      </summary>
      <div class="pt-2 space-y-2">
        <ol class="list-decimal list-inside text-sm space-y-1">
          <li v-for="s in steps" :key="s.order" class="px-2 py-1 rounded hover:bg-gray-100">
            {{ s.description }}
          </li>
        </ol>
        <div class="flex gap-2">
          <input v-model="newStep" placeholder="Описание шага..."
            class="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm"
            @keydown.enter="addStep" />
          <button class="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50" @click="addStep">+</button>
          <button class="px-3 py-1 text-xs rounded border border-gray-300 text-red-600 hover:bg-red-50" @click="removeStep">&minus;</button>
        </div>
      </div>
    </details>

    <!-- Actions -->
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
