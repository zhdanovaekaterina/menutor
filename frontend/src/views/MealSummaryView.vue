<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchMealSummary, generateFilteredShoppingList } from '@/api/client'
import { buildSummaryText, getSummaryFilename } from '@/utils/exportSummaryTxt'
import type { MealIngredient, MealSummaryRecipe, MealSummaryResponse } from '@/api/types'
import { useMealTypeStore } from '@/stores/mealTypes'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useToastStore } from '@/stores/toast'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SummaryExportModal from '@/components/summary/SummaryExportModal.vue'
import SummaryHeader from '@/components/summary/SummaryHeader.vue'
import MealCard from '@/components/summary/MealCard.vue'
import NestedRecipeCard from '@/components/summary/NestedRecipeCard.vue'
import type { NestedRecipeSummary } from '@/components/summary/NestedRecipeCard.vue'
import StandaloneProductCard from '@/components/summary/StandaloneProductCard.vue'
import SummaryFooter from '@/components/summary/SummaryFooter.vue'


const route = useRoute()
const router = useRouter()
const shoppingStore = useShoppingListStore()
const toast = useToastStore()
const mealTypeStore = useMealTypeStore()

const menuId = computed(() => Number(route.params['id']))

const summary = ref<MealSummaryResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const generating = ref(false)
const confirmGenerateOpen = ref(false)
const exportModalOpen = ref(false)
const exportText = ref('')
const exportFilename = ref('')

// Per-recipe slot selection: recipeId -> Set of selected slotIndices
const selectedSlotsByRecipe = ref<Map<number, Set<number>>>(new Map())

// Deselected nested recipe IDs (excluded from shopping list)
const deselectedSubRecipes = ref<Set<number>>(new Set())

const isEmpty = computed(
  () =>
    summary.value !== null &&
    summary.value.recipes.length === 0 &&
    summary.value.products.length === 0,
)

// ── Scale helpers ──────────────────────────────────────────────────────────

function scaleIngredients(ingredients: MealIngredient[], factor: number): MealIngredient[] {
  return ingredients.map((ing) => ({
    ...ing,
    quantity_amount: Math.round(ing.quantity_amount * factor * 100) / 100,
    sub_ingredients: ing.sub_ingredients
      ? scaleIngredients(ing.sub_ingredients, factor)
      : undefined,
  }))
}

function getRecipeScaleFactor(recipe: MealSummaryRecipe): number {
  const selectedSlots = selectedSlotsByRecipe.value.get(recipe.recipe_id) ?? new Set<number>()
  const selectedServings = recipe.occurrences
    .filter((o) => selectedSlots.has(o.slot_index))
    .reduce((sum, o) => sum + o.servings, 0)
  return recipe.total_servings > 0 ? selectedServings / recipe.total_servings : 0
}

// Reactive map: recipeId -> scaled ingredients (tracks selectedSlotsByRecipe)
const recipeIngredients = computed(() => {
  const map = new Map<number, MealIngredient[]>()
  if (summary.value) {
    for (const recipe of summary.value.recipes) {
      map.set(recipe.recipe_id, scaleIngredients(recipe.ingredients, getRecipeScaleFactor(recipe)))
    }
  }
  return map
})

// ── Nested recipes aggregation ─────────────────────────────────────────────

function aggregateSubIngredients(existing: MealIngredient[], additional: MealIngredient[]): void {
  for (const addIng of additional) {
    const match = existing.find(
      (e) => e.product_name === addIng.product_name && e.quantity_unit === addIng.quantity_unit,
    )
    if (match) {
      match.quantity_amount = Math.round((match.quantity_amount + addIng.quantity_amount) * 100) / 100
    } else {
      existing.push({ ...addIng })
    }
  }
}

function collectSubRecipes(
  ingredients: MealIngredient[],
  map: Map<number, NestedRecipeSummary>,
): void {
  for (const ing of ingredients) {
    if (ing.sub_recipe_id != null) {
      const existing = map.get(ing.sub_recipe_id)
      if (existing) {
        existing.total_quantity_amount = Math.round(
          (existing.total_quantity_amount + ing.quantity_amount) * 100,
        ) / 100
        aggregateSubIngredients(existing.ingredients, ing.sub_ingredients ?? [])
      } else {
        map.set(ing.sub_recipe_id, {
          sub_recipe_id: ing.sub_recipe_id,
          sub_recipe_name: ing.sub_recipe_name ?? '',
          total_quantity_amount: ing.quantity_amount,
          quantity_unit: ing.quantity_unit,
          ingredients: (ing.sub_ingredients ?? []).map((i) => ({ ...i })),
        })
      }
      // Recurse into sub-sub-recipes
      collectSubRecipes(ing.sub_ingredients ?? [], map)
    }
  }
}

const nestedRecipes = computed<NestedRecipeSummary[]>(() => {
  if (!summary.value) return []
  const map = new Map<number, NestedRecipeSummary>()
  for (const recipe of summary.value.recipes) {
    const scaled = recipeIngredients.value.get(recipe.recipe_id) ?? []
    collectSubRecipes(scaled, map)
  }
  return [...map.values()]
})

// ── Selection counts ───────────────────────────────────────────────────────

const totalSlotCount = computed(() => {
  if (!summary.value) return 0
  return (
    summary.value.recipes.reduce((sum, r) => sum + r.occurrences.length, 0) +
    summary.value.products.reduce((sum, p) => sum + p.occurrences.length, 0)
  )
})

const selectedSlotCount = computed(() => {
  if (!summary.value) return 0
  let count = 0
  for (const recipe of summary.value.recipes) {
    count += (selectedSlotsByRecipe.value.get(recipe.recipe_id) ?? new Set()).size
  }
  // Products always counted (no deselection for products)
  count += summary.value.products.reduce((sum, p) => sum + p.occurrences.length, 0)
  return count
})

// ── Standalone products ────────────────────────────────────────────────────

const standaloneProducts = computed(() => summary.value?.products ?? [])

// ── Load ───────────────────────────────────────────────────────────────────

async function loadSummary() {
  loading.value = true
  error.value = null
  try {
    summary.value = await fetchMealSummary(menuId.value)
    // Select all slots by default
    const next = new Map<number, Set<number>>()
    for (const recipe of summary.value.recipes) {
      next.set(recipe.recipe_id, new Set(recipe.occurrences.map((o) => o.slot_index)))
    }
    selectedSlotsByRecipe.value = next
    deselectedSubRecipes.value = new Set()
  } catch {
    error.value = 'Не удалось загрузить сводку меню'
  } finally {
    loading.value = false
  }
}

const mealTypeNames = computed<Record<number, string>>(() =>
  Object.fromEntries(mealTypeStore.items.map((mt) => [mt.id, mt.name])),
)

onMounted(async () => {
  await mealTypeStore.load()
  await loadSummary()
})

// ── Toggle functions ───────────────────────────────────────────────────────

function toggleRecipe(recipeId: number): void {
  const recipe = summary.value?.recipes.find((r) => r.recipe_id === recipeId)
  if (!recipe) return
  const current = selectedSlotsByRecipe.value.get(recipeId) ?? new Set<number>()
  const allIndices = new Set(recipe.occurrences.map((o) => o.slot_index))
  const newSelected = current.size === allIndices.size ? new Set<number>() : new Set(allIndices)
  const next = new Map(selectedSlotsByRecipe.value)
  next.set(recipeId, newSelected)
  selectedSlotsByRecipe.value = next
}

function toggleRecipeSlot(recipeId: number, slotIndex: number): void {
  const current = new Set(selectedSlotsByRecipe.value.get(recipeId) ?? [])
  if (current.has(slotIndex)) {
    current.delete(slotIndex)
  } else {
    current.add(slotIndex)
  }
  const next = new Map(selectedSlotsByRecipe.value)
  next.set(recipeId, current)
  selectedSlotsByRecipe.value = next
}

function collectAllSubRecipeIds(ingredients: MealIngredient[], into: Set<number>): void {
  for (const ing of ingredients) {
    if (ing.sub_recipe_id != null) {
      into.add(ing.sub_recipe_id)
      collectAllSubRecipeIds(ing.sub_ingredients ?? [], into)
    }
  }
}

function toggleNestedRecipe(subRecipeId: number): void {
  const next = new Set(deselectedSubRecipes.value)
  if (next.has(subRecipeId)) {
    next.delete(subRecipeId)
  } else {
    next.add(subRecipeId)
    // Auto-deselect nested sub-recipes of this sub-recipe
    const nested = nestedRecipes.value.find((n) => n.sub_recipe_id === subRecipeId)
    if (nested) {
      collectAllSubRecipeIds(nested.ingredients, next)
    }
  }
  deselectedSubRecipes.value = next
}

function selectAll(): void {
  if (!summary.value) return
  const next = new Map<number, Set<number>>()
  for (const recipe of summary.value.recipes) {
    next.set(recipe.recipe_id, new Set(recipe.occurrences.map((o) => o.slot_index)))
  }
  selectedSlotsByRecipe.value = next
  deselectedSubRecipes.value = new Set()
}

function deselectAll(): void {
  if (!summary.value) return
  const next = new Map<number, Set<number>>()
  for (const recipe of summary.value.recipes) {
    next.set(recipe.recipe_id, new Set<number>())
  }
  selectedSlotsByRecipe.value = next
}

// ── Generate shopping list ─────────────────────────────────────────────────

function onGenerate() {
  if (selectedSlotCount.value === 0) return
  if (selectedSlotCount.value < totalSlotCount.value) {
    confirmGenerateOpen.value = true
  } else {
    doGenerate()
  }
}

async function doGenerate(): Promise<void> {
  confirmGenerateOpen.value = false
  generating.value = true
  try {
    // Collect all selected recipe slot indices
    const slotIndices: number[] = []
    for (const [, slots] of selectedSlotsByRecipe.value) {
      for (const idx of slots) slotIndices.push(idx)
    }
    // Include all standalone product slot indices (no deselection for products)
    if (summary.value) {
      for (const product of summary.value.products) {
        for (const occ of product.occurrences) slotIndices.push(occ.slot_index)
      }
    }

    const excludedSubRecipeIds = [...deselectedSubRecipes.value]

    const list = await generateFilteredShoppingList(menuId.value, slotIndices, excludedSubRecipeIds)
    shoppingStore.data = list
    shoppingStore.currentListId = list.id
    toast.show('Список покупок сформирован', 'success')
    router.push({ path: '/shopping-list' })
  } catch {
    toast.show('Ошибка формирования списка', 'error')
  } finally {
    generating.value = false
  }
}

function goToPlanner() {
  router.push('/planner')
}

function exportTxt(): void {
  if (!summary.value) return
  exportText.value = buildSummaryText(
    summary.value,
    selectedSlotsByRecipe.value,
    recipeIngredients.value,
    nestedRecipes.value,
    deselectedSubRecipes.value,
    mealTypeNames.value,
  )
  exportFilename.value = getSummaryFilename(summary.value.menu_name)
  exportModalOpen.value = true
}
</script>

<template>
  <div class="h-full flex flex-col p-3 sm:p-4 lg:p-6 gap-3 sm:gap-4">
    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center gap-2">
        <div class="w-8 h-8 border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
        <span class="text-sm text-gray-400">Загрузка сводки...</span>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex flex-col items-center justify-center gap-3 text-center px-4">
      <div class="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center">
        <svg class="w-6 h-6 text-red-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
      </div>
      <p class="text-sm text-red-600">{{ error }}</p>
      <div class="flex gap-2">
        <button
          class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
          @click="router.back()"
        >
          Назад
        </button>
        <button
          class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
          @click="loadSummary"
        >
          Повторить
        </button>
      </div>
    </div>

    <!-- Empty menu -->
    <div v-else-if="isEmpty" class="flex-1 flex flex-col items-center justify-center gap-4 text-center px-4">
      <div class="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
        <svg class="w-8 h-8 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      </div>
      <div>
        <p class="text-gray-900 font-medium">Меню пусто</p>
        <p class="text-sm text-gray-500 mt-1">Добавьте блюда в планировщике, чтобы увидеть сводку.</p>
      </div>
      <button
        class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
        @click="goToPlanner"
      >
        Перейти в планировщик
      </button>
    </div>

    <!-- Main content -->
    <template v-else-if="summary">
      <SummaryHeader
        :menu-name="summary.menu_name"
        :selected-count="selectedSlotCount"
        :total-count="totalSlotCount"
        @back="router.back()"
        @select-all="selectAll"
        @deselect-all="deselectAll"
      />

      <div class="flex-1 overflow-y-auto min-h-0">
        <div class="max-w-3xl mx-auto pb-24 lg:pb-4 space-y-3">

          <!-- Section 1: Recipe cards (one per unique recipe) -->
          <MealCard
            v-for="recipe in summary.recipes"
            :key="recipe.recipe_id"
            :recipe="recipe"
            :selected-slots="selectedSlotsByRecipe.get(recipe.recipe_id) ?? new Set()"
            :scaled-ingredients="recipeIngredients.get(recipe.recipe_id) ?? []"
            :meal-type-names="mealTypeNames"
            @toggle-recipe="toggleRecipe(recipe.recipe_id)"
            @toggle-slot="(idx) => toggleRecipeSlot(recipe.recipe_id, idx)"
          />

          <!-- Section 2: Nested recipes -->
          <div v-if="nestedRecipes.length > 0" class="mt-8">
            <div class="flex items-center gap-3 mb-3">
              <div class="h-px flex-1 bg-amber-200" />
              <span class="text-xs font-semibold text-amber-600 uppercase tracking-wider">
                Вложенные рецепты
              </span>
              <div class="h-px flex-1 bg-amber-200" />
            </div>
            <div class="space-y-3">
              <NestedRecipeCard
                v-for="nested in nestedRecipes"
                :key="nested.sub_recipe_id"
                :nested="nested"
                :is-selected="!deselectedSubRecipes.has(nested.sub_recipe_id)"
                @toggle="toggleNestedRecipe(nested.sub_recipe_id)"
              />
            </div>
          </div>

          <!-- Section 3: Standalone products -->
          <div v-if="standaloneProducts.length > 0" class="mt-8">
            <div class="flex items-center gap-3 mb-3">
              <div class="h-px flex-1 bg-gray-200" />
              <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Отдельные продукты
              </span>
              <div class="h-px flex-1 bg-gray-200" />
            </div>
            <div class="space-y-3">
              <StandaloneProductCard
                v-for="product in standaloneProducts"
                :key="product.product_id"
                :product="product"
                :meal-type-names="mealTypeNames"
              />
            </div>
          </div>

        </div>
      </div>

      <SummaryFooter
        :selected-count="selectedSlotCount"
        :total-count="totalSlotCount"
        :generating="generating"
        @generate="onGenerate"
        @export="exportTxt"
      />
    </template>

    <SummaryExportModal
      :open="exportModalOpen"
      :text="exportText"
      :filename="exportFilename"
      @close="exportModalOpen = false"
    />

    <ConfirmDialog
      :open="confirmGenerateOpen"
      title="Частичный выбор"
      :message="`Вы выбрали ${selectedSlotCount} из ${totalSlotCount} блюд. Сформировать список покупок только для выбранных?`"
      confirm-label="Сформировать"
      @confirm="doGenerate"
      @cancel="confirmGenerateOpen = false"
    />
  </div>
</template>
