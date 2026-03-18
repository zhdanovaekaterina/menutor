<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ActiveCategory, Product, Recipe, RecipeCreate, ProductCreate } from '@/api/types'
import { useToastStore } from '@/stores/toast'
import { useProductStore } from '@/stores/products'
import { fetchRecipeDependents } from '@/api/client'
import IngredientListEditor from './IngredientListEditor.vue'
import StepListEditor from './StepListEditor.vue'
import FlattenedProductList from './FlattenedProductList.vue'
import ProductForm from '@/components/products/ProductForm.vue'

const toast = useToastStore()
const productStore = useProductStore()

const props = defineProps<{
  recipe: Recipe | null
  categories: ActiveCategory[]
  products: Product[]
  recipes: Recipe[]
  ancestorIds?: Set<number>
  parentRecipeName?: string
}>()

const emit = defineEmits<{
  save: [data: RecipeCreate, id: number | null]
  remove: [id: number]
  clear: []
  'navigate-to-recipe': [recipeId: number]
  'navigate-back': []
}>()

type IngredientRow = {
  product_id: number | null
  sub_recipe_id: number | null
  quantity_amount: number
  quantity_unit: string
}

const name = ref('')
const categoryId = ref<number | null>(null)
const servings = ref(4)
const weight = ref(0)
const ingredients = ref<IngredientRow[]>([])
const steps = ref<{ order: number; description: string }[]>([])

const productFormOpen = ref(false)
const pendingIngredientIndex = ref<number | null>(null)

const dependentNames = ref<string[]>([])

watch(
  () => props.recipe,
  (r) => {
    if (r) {
      name.value = r.name
      categoryId.value = r.category_id
      servings.value = r.servings
      weight.value = r.weight
      ingredients.value = [...r.ingredients].sort((a, b) => a.order - b.order).map((i) => ({
        product_id: i.product_id,
        sub_recipe_id: i.sub_recipe_id,
        quantity_amount: i.quantity_amount,
        quantity_unit: i.quantity_unit,
      }))
      steps.value = r.steps.map((s) => ({ ...s }))
    }
  },
  { immediate: true },
)

watch(
  () => props.recipe?.id,
  async (id) => {
    if (!id) { dependentNames.value = []; return }
    try {
      const deps = await fetchRecipeDependents(id)
      dependentNames.value = deps.map((d) => d.name)
    } catch {
      dependentNames.value = []
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
  if (!name.value.trim()) { toast.show('Введите название рецепта', 'error'); return }
  if (categoryId.value == null) { toast.show('Выберите категорию', 'error'); return }
  const data: RecipeCreate = {
    name: name.value.trim(),
    category_id: categoryId.value,
    servings: servings.value,
    weight: weight.value,
    ingredients: ingredients.value
      .filter((i) => i.product_id != null || i.sub_recipe_id != null)
      .map((i, idx) => ({
        product_id: i.product_id,
        sub_recipe_id: i.sub_recipe_id,
        quantity_amount: i.quantity_amount,
        quantity_unit: i.quantity_unit,
        order: idx,
      })),
    steps: steps.value,
  }
  emit('save', data, props.recipe?.id ?? null)
}

function onCreateProduct(index: number) {
  pendingIngredientIndex.value = index
  productFormOpen.value = true
}

async function onProductSave(data: ProductCreate) {
  try {
    const created = await productStore.create(data)
    if (pendingIngredientIndex.value != null && pendingIngredientIndex.value < ingredients.value.length) {
      const ing = ingredients.value[pendingIngredientIndex.value]!
      ing.product_id = created.id
      ing.quantity_unit = created.recipe_unit
      ing.quantity_amount = created.recipe_unit === 'g' ? 100 : 1
    }
    productFormOpen.value = false
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка создания продукта', 'error')
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Breadcrumb: back to parent recipe -->
    <button
      v-if="parentRecipeName"
      type="button"
      class="mb-3 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
      @click="emit('navigate-back')"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
      </svg>
      <span>Назад к: {{ parentRecipeName }}</span>
    </button>

    <!-- Used as sub-recipe banner -->
    <div
      v-if="dependentNames.length > 0"
      class="mb-3 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-700"
    >
      Этот рецепт используется в: {{ dependentNames.join(', ') }}
    </div>

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

    <IngredientListEditor
      v-model="ingredients"
      :products="products"
      :recipes="recipes"
      :current-recipe-id="recipe?.id ?? null"
      :ancestor-ids="ancestorIds"
      @create-product="onCreateProduct"
      @navigate-to-recipe="(id) => emit('navigate-to-recipe', id)"
    />

    <!-- Flattened products (shown when recipe has sub-recipe ingredients and is already saved) -->
    <FlattenedProductList
      v-if="recipe && ingredients.some((i) => i.sub_recipe_id != null)"
      :recipe-id="recipe.id"
    />

    <StepListEditor v-model="steps" />

    <div class="flex gap-2 pt-4 border-t">
      <button
        class="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        @click="onSave"
      >
        {{ recipe ? 'Сохранить' : 'Создать' }}
      </button>
      <button
        v-if="recipe"
        class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
        @click="clearForm"
      >
        Новый
      </button>
      <button
        v-if="recipe"
        class="px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50 transition-colors"
        @click="emit('remove', recipe.id)"
      >
        Удалить
      </button>
    </div>

    <Teleport to="body">
      <div v-if="productFormOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold">Новый продукт</h3>
            <button
              class="p-1 rounded hover:bg-gray-100 text-gray-500"
              @click="productFormOpen = false"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
          <ProductForm
            :product="null"
            :categories="productStore.categories"
            @save="onProductSave"
            @clear="productFormOpen = false"
          />
        </div>
      </div>
    </Teleport>
  </div>
</template>
