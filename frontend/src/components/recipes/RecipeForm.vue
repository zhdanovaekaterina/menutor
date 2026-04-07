<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { ActiveCategory, Product, Recipe, RecipeCreate } from '@/api/types'
import { useToastStore } from '@/stores/toast'
import { useProductStore } from '@/stores/products'
import { fetchRecipeDependents } from '@/api/client'
import IngredientListEditor from './IngredientListEditor.vue'
import StepListEditor from './StepListEditor.vue'
import FlattenedProductList from './FlattenedProductList.vue'
import CostSummaryBlock from './CostSummaryBlock.vue'
import PreferenceBadges from './PreferenceBadges.vue'
import { useRecipeSettingsStore } from '@/stores/recipeSettings'

const recipeSettings = useRecipeSettingsStore()

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
const isPiecesMode = ref(false)
const totalPieces = ref<number | null>(null)
const piecesPerPortion = ref<number | null>(null)
const link = ref<string | null>(null)
const comment = ref<string | null>(null)

const autoServings = computed(() => {
  if (!isPiecesMode.value || !totalPieces.value || !piecesPerPortion.value) return null
  return Math.floor(totalPieces.value / piecesPerPortion.value)
})

const ingredients = ref<IngredientRow[]>([])
const steps = ref<{ order: number; description: string }[]>([])

const dependentNames = ref<string[]>([])

type IngredientSnapshot = { product_id: number | null; sub_recipe_id: number | null; quantity_amount: number; quantity_unit: string }
const ingredientsSnapshotAtLastFetch = ref<IngredientSnapshot[] | null>(null)

const flattenedProductsDirty = computed<boolean>(() => {
  const snap = ingredientsSnapshotAtLastFetch.value
  if (snap === null) return false
  const current = ingredients.value
  if (current.length !== snap.length) return true
  return current.some((ing, i) => {
    const s = snap[i]!
    return (
      ing.product_id !== s.product_id ||
      ing.sub_recipe_id !== s.sub_recipe_id ||
      ing.quantity_amount !== s.quantity_amount ||
      ing.quantity_unit !== s.quantity_unit
    )
  })
})

function takeIngredientsSnapshot() {
  ingredientsSnapshotAtLastFetch.value = ingredients.value.map((ing) => ({ ...ing }))
}

watch(
  () => props.recipe,
  (r) => {
    ingredientsSnapshotAtLastFetch.value = null
    if (r) {
      name.value = r.name
      categoryId.value = r.category_id
      servings.value = r.servings
      weight.value = r.weight
      isPiecesMode.value = r.total_pieces != null && r.pieces_per_portion != null
      totalPieces.value = r.total_pieces ?? null
      piecesPerPortion.value = r.pieces_per_portion ?? null
      link.value = r.link ?? null
      comment.value = r.comment ?? null
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
  isPiecesMode.value = false
  totalPieces.value = null
  piecesPerPortion.value = null
  link.value = null
  comment.value = null
  ingredients.value = []
  steps.value = []
  emit('clear')
}

function onSave() {
  if (!name.value.trim()) { toast.show('Введите название рецепта', 'error'); return }
  if (categoryId.value == null) { toast.show('Выберите категорию', 'error'); return }

  if (isPiecesMode.value) {
    if (!totalPieces.value || totalPieces.value < 1) {
      toast.show('Укажите количество штук (мин. 1)', 'error'); return
    }
    if (!piecesPerPortion.value || piecesPerPortion.value < 1) {
      toast.show('Укажите штук на порцию (мин. 1)', 'error'); return
    }
    if (piecesPerPortion.value > totalPieces.value) {
      toast.show('Штук на порцию не может быть больше общего количества', 'error'); return
    }
  }

  const data: RecipeCreate = {
    name: name.value.trim(),
    category_id: categoryId.value,
    servings: isPiecesMode.value ? (autoServings.value ?? 1) : servings.value,
    weight: weight.value,
    total_pieces: isPiecesMode.value ? totalPieces.value : null,
    pieces_per_portion: isPiecesMode.value ? piecesPerPortion.value : null,
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
    link: link.value || null,
    comment: comment.value || null,
  }
  emit('save', data, props.recipe?.id ?? null)
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

    <!-- Preference tags for existing recipe -->
    <PreferenceBadges v-if="recipe && recipe.ingredients.length > 0" :recipe-id="recipe.id" />

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

    <!-- Toggle: Считать в штуках -->
    <div class="flex items-center gap-3 py-2">
      <button
        type="button"
        role="switch"
        :aria-checked="isPiecesMode"
        aria-label="Считать в штуках"
        class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200"
        :class="isPiecesMode ? 'bg-blue-600' : 'bg-gray-300'"
        @click="isPiecesMode = !isPiecesMode"
      >
        <span
          class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200"
          :class="isPiecesMode ? 'translate-x-4' : 'translate-x-0.5'"
        />
      </button>
      <span class="text-sm text-gray-700">Считать в штуках</span>
    </div>

    <!-- Обычный режим: Порции + Вес -->
    <div v-if="!isPiecesMode" class="grid grid-cols-2 gap-4">
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

    <!-- Штучный режим: Кол-во + Шт на порцию + Вес -->
    <div v-else>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Кол-во (шт)</label>
          <input v-model.number="totalPieces" type="number" min="1" max="9999"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Шт на порцию</label>
          <input v-model.number="piecesPerPortion" type="number" min="1" :max="totalPieces ?? 9999"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Вес готового блюда (г)</label>
          <input v-model.number="weight" type="number" min="0"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>
      </div>
      <p v-if="autoServings != null" class="text-xs text-gray-500 mt-2 ml-0.5">
        Порций: {{ autoServings }} (авто)
      </p>
    </div>

    <!-- Cost per portion -->
    <CostSummaryBlock
      v-if="recipeSettings.showCostColumn"
      :ingredients="ingredients"
      :servings="servings"
      :total-pieces="totalPieces"
      :pieces-per-portion="piecesPerPortion"
      :is-pieces-mode="isPiecesMode"
    />

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Ссылка <span class="text-gray-400 font-normal">(необязательно)</span></label>
      <input
        v-model="link"
        type="url"
        placeholder="https://..."
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Комментарий <span class="text-gray-400 font-normal">(необязательно)</span></label>
      <textarea
        v-model="comment"
        rows="3"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y"
      />
    </div>

    <IngredientListEditor
      v-model="ingredients"
      :products="products"
      :recipes="recipes"
      :current-recipe-id="recipe?.id ?? null"
      :ancestor-ids="ancestorIds"
      :product-categories="productStore.categories"
      :recipe-categories="categories"
      @navigate-to-recipe="(id) => emit('navigate-to-recipe', id)"
    />

    <!-- Flattened products (shown when recipe has sub-recipe ingredients and is already saved) -->
    <FlattenedProductList
      v-if="recipe && ingredients.some((i) => i.sub_recipe_id != null)"
      :recipe-id="recipe.id"
      :ingredients="ingredients"
      :is-dirty="flattenedProductsDirty"
      @refreshed="takeIngredientsSnapshot"
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
  </div>
</template>
