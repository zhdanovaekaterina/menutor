<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchMealSummary, generateFilteredShoppingList } from '@/api/client'
import type { MealIngredient, MealSummaryResponse, PiecesInfo } from '@/api/types'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useToastStore } from '@/stores/toast'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SummaryHeader from '@/components/summary/SummaryHeader.vue'
import MealCard from '@/components/summary/MealCard.vue'
import StandaloneProductCard from '@/components/summary/StandaloneProductCard.vue'
import SummaryFooter from '@/components/summary/SummaryFooter.vue'

const DAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const route = useRoute()
const router = useRouter()
const shoppingStore = useShoppingListStore()
const toast = useToastStore()

const menuId = computed(() => Number(route.params['id']))

const summary = ref<MealSummaryResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const generating = ref(false)
const confirmGenerateOpen = ref(false)

// Selected slot keys: "r-{recipe_id}-{slot_index}" or "p-{product_id}-{slot_index}"
const selectedKeys = ref<Set<string>>(new Set())

function recipeSlotKey(recipeId: number, slotIndex: number): string {
  return `r-${recipeId}-${slotIndex}`
}

function productSlotKey(productId: number, slotIndex: number): string {
  return `p-${productId}-${slotIndex}`
}

// All possible slot keys derived from summary data
const allKeys = computed<string[]>(() => {
  if (!summary.value) return []
  const keys: string[] = []
  for (const recipe of summary.value.recipes) {
    for (const occ of recipe.occurrences) {
      keys.push(recipeSlotKey(recipe.recipe_id, occ.slot_index))
    }
  }
  for (const product of summary.value.products) {
    for (const occ of product.occurrences) {
      keys.push(productSlotKey(product.product_id, occ.slot_index))
    }
  }
  return keys
})

const totalCount = computed(() => allKeys.value.length)
const selectedCount = computed(() => selectedKeys.value.size)
const isEmpty = computed(
  () =>
    summary.value !== null &&
    summary.value.recipes.length === 0 &&
    summary.value.products.length === 0,
)

interface DisplayItem {
  key: string
  type: 'recipe' | 'product'
  day: number
  mealType: string
  mealTypeLabel: string
  // Recipe-specific
  recipeName?: string
  servings?: number
  piecesInfo?: PiecesInfo | null
  scaledIngredients?: MealIngredient[]
  // Product-specific
  productName?: string
  quantity?: number
  unit?: string
}

// Scale ingredients by factor (per-occurrence)
function scaleIngredients(
  ingredients: MealIngredient[],
  factor: number,
): MealIngredient[] {
  return ingredients.map((ing) => ({
    ...ing,
    quantity_amount: Math.round(ing.quantity_amount * factor * 100) / 100,
    sub_ingredients: ing.sub_ingredients
      ? scaleIngredients(ing.sub_ingredients, factor)
      : undefined,
  }))
}

// Group display items by day, sorted day 0-6
const itemsByDay = computed<Map<number, DisplayItem[]>>(() => {
  if (!summary.value) return new Map()

  const dayMap = new Map<number, DisplayItem[]>()

  for (const recipe of summary.value.recipes) {
    for (const occ of recipe.occurrences) {
      const key = recipeSlotKey(recipe.recipe_id, occ.slot_index)
      const scaleFactor =
        recipe.total_servings > 0 ? occ.servings / recipe.total_servings : 1

      const item: DisplayItem = {
        key,
        type: 'recipe',
        day: occ.day,
        mealType: occ.meal_type,
        mealTypeLabel: occ.meal_type,
        recipeName: recipe.recipe_name,
        servings: occ.servings,
        piecesInfo: occ.pieces_override != null && recipe.pieces_info
          ? {
              total_pieces: occ.pieces_override,
              pieces_per_portion: recipe.pieces_info.pieces_per_portion,
            }
          : null,
        scaledIngredients: scaleIngredients(recipe.ingredients, scaleFactor),
      }

      const list = dayMap.get(occ.day) ?? []
      list.push(item)
      dayMap.set(occ.day, list)
    }
  }

  // Sort days 0-6
  return new Map([...dayMap.entries()].sort((a, b) => a[0] - b[0]))
})

// Standalone products (not grouped by day in a separate map, shown in separate section)
const standaloneProducts = computed<DisplayItem[]>(() => {
  if (!summary.value) return []
  const items: DisplayItem[] = []
  for (const product of summary.value.products) {
    for (const occ of product.occurrences) {
      items.push({
        key: productSlotKey(product.product_id, occ.slot_index),
        type: 'product',
        day: occ.day,
        mealType: occ.meal_type,
        mealTypeLabel: occ.meal_type,
        productName: product.product_name,
        quantity: occ.quantity,
        unit: occ.unit,
      })
    }
  }
  return items
})

async function loadSummary() {
  loading.value = true
  error.value = null
  try {
    summary.value = await fetchMealSummary(menuId.value)
    // Select all by default
    selectedKeys.value = new Set(allKeys.value)
  } catch {
    error.value = 'Не удалось загрузить сводку меню'
  } finally {
    loading.value = false
  }
}

onMounted(loadSummary)

function selectAll() {
  selectedKeys.value = new Set(allKeys.value)
}

function deselectAll() {
  selectedKeys.value = new Set()
}

function toggleKey(key: string) {
  const next = new Set(selectedKeys.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  selectedKeys.value = next
}

function collectSelectedSlotIndices(): number[] {
  const indices: number[] = []
  for (const key of selectedKeys.value) {
    // Key format: "r-{recipeId}-{slotIndex}" or "p-{productId}-{slotIndex}"
    const parts = key.split('-')
    const idx = Number(parts[parts.length - 1])
    if (!isNaN(idx)) {
      indices.push(idx)
    }
  }
  return indices
}

function onGenerate() {
  if (selectedCount.value === 0) return
  if (selectedCount.value < totalCount.value) {
    // Partial selection — show confirmation
    confirmGenerateOpen.value = true
  } else {
    doGenerate()
  }
}

async function doGenerate() {
  confirmGenerateOpen.value = false
  generating.value = true
  try {
    const slotIndices = collectSelectedSlotIndices()
    const list = await generateFilteredShoppingList(menuId.value, slotIndices)
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
    <template v-else>
      <SummaryHeader
        :menu-name="summary?.menu_name ?? ''"
        :selected-count="selectedCount"
        :total-count="totalCount"
        @back="router.back()"
        @select-all="selectAll"
        @deselect-all="deselectAll"
      />

      <div class="flex-1 overflow-y-auto min-h-0">
        <div class="max-w-3xl mx-auto pb-24 lg:pb-4">

          <!-- Day groups (recipe occurrences) -->
          <div
            v-for="[day, items] in itemsByDay"
            :key="day"
            class="mt-6 first:mt-0"
          >
            <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-1">
              {{ DAY_LABELS[day] }}
            </h2>
            <div class="space-y-2">
              <MealCard
                v-for="item in items"
                :key="item.key"
                :slot-key="item.key"
                :recipe-name="item.recipeName ?? ''"
                :day-label="DAY_LABELS[item.day] ?? ''"
                :meal-type-label="item.mealTypeLabel"
                :servings="item.servings ?? 0"
                :pieces-info="item.piecesInfo"
                :ingredients="item.scaledIngredients ?? []"
                :is-selected="selectedKeys.has(item.key)"
                @toggle="toggleKey(item.key)"
              />
            </div>
          </div>

          <!-- Standalone products section -->
          <div v-if="standaloneProducts.length > 0" class="mt-8">
            <div class="flex items-center gap-3 mb-3">
              <div class="h-px flex-1 bg-gray-200" />
              <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Отдельные продукты
              </span>
              <div class="h-px flex-1 bg-gray-200" />
            </div>
            <div class="space-y-2">
              <StandaloneProductCard
                v-for="item in standaloneProducts"
                :key="item.key"
                :slot-key="item.key"
                :product-name="item.productName ?? ''"
                :day-label="DAY_LABELS[item.day] ?? ''"
                :meal-type-label="item.mealTypeLabel"
                :quantity="item.quantity ?? 0"
                :unit="item.unit ?? ''"
                :is-selected="selectedKeys.has(item.key)"
                @toggle="toggleKey(item.key)"
              />
            </div>
          </div>

        </div>
      </div>

      <SummaryFooter
        :selected-count="selectedCount"
        :total-count="totalCount"
        :generating="generating"
        @generate="onGenerate"
      />
    </template>

    <ConfirmDialog
      :open="confirmGenerateOpen"
      title="Частичный выбор"
      :message="`Вы выбрали ${selectedCount} из ${totalCount} блюд. Сформировать список покупок только для выбранных?`"
      confirm-label="Сформировать"
      @confirm="doGenerate"
      @cancel="confirmGenerateOpen = false"
    />
  </div>
</template>
