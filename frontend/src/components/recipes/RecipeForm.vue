<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ActiveCategory, Product, Recipe, RecipeCreate, ProductCreate } from '@/api/types'
import { useToastStore } from '@/stores/toast'
import { useProductStore } from '@/stores/products'
import IngredientListEditor from './IngredientListEditor.vue'
import StepListEditor from './StepListEditor.vue'
import ProductForm from '@/components/products/ProductForm.vue'

const toast = useToastStore()
const productStore = useProductStore()

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

const productFormOpen = ref(false)
const pendingIngredientIndex = ref<number | null>(null)

watch(
  () => props.recipe,
  (r) => {
    if (r) {
      name.value = r.name
      categoryId.value = r.category_id
      servings.value = r.servings
      weight.value = r.weight
      ingredients.value = [...r.ingredients].sort((a, b) => a.order - b.order).map((i) => ({ ...i }))
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
  if (!name.value.trim()) { toast.show('Введите название рецепта', 'error'); return }
  if (categoryId.value == null) { toast.show('Выберите категорию', 'error'); return }
  const data: RecipeCreate = {
    name: name.value.trim(),
    category_id: categoryId.value,
    servings: servings.value,
    weight: weight.value,
    ingredients: ingredients.value
      .filter((i) => i.product_id != null)
      .map((i, idx) => ({
        product_id: i.product_id!,
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

    <IngredientListEditor v-model="ingredients" :products="products" @create-product="onCreateProduct" />

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
