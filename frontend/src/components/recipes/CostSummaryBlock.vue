<script setup lang="ts">
import { ref, watch } from 'vue'
import type { CostPreviewResponse } from '@/api/types'
import { previewRecipeCost } from '@/api/client'

const props = defineProps<{
  ingredients: { product_id: number | null; sub_recipe_id: number | null; quantity_amount: number; quantity_unit: string }[]
  servings: number
  totalPieces: number | null
  piecesPerPortion: number | null
  isPiecesMode: boolean
}>()

const costData = ref<CostPreviewResponse | null>(null)
const costLoading = ref(false)
const breakdownExpanded = ref(false)

let debounceTimer: ReturnType<typeof setTimeout>

async function fetchCost() {
  const validIngredients = props.ingredients.filter(
    (i) => i.product_id != null || i.sub_recipe_id != null
  )
  if (validIngredients.length === 0) {
    costData.value = null
    return
  }
  costLoading.value = true
  try {
    costData.value = await previewRecipeCost({
      ingredients: validIngredients.map((i) => ({
        product_id: i.product_id,
        sub_recipe_id: i.sub_recipe_id,
        quantity_amount: i.quantity_amount,
        quantity_unit: i.quantity_unit,
      })),
      servings: props.isPiecesMode
        ? (props.totalPieces && props.piecesPerPortion
            ? Math.floor(props.totalPieces / props.piecesPerPortion)
            : 1)
        : props.servings,
      total_pieces: props.isPiecesMode ? props.totalPieces : null,
      pieces_per_portion: props.isPiecesMode ? props.piecesPerPortion : null,
    })
  } catch {
    costData.value = null
  } finally {
    costLoading.value = false
  }
}

watch(
  [
    () => props.ingredients,
    () => props.servings,
    () => props.totalPieces,
    () => props.piecesPerPortion,
    () => props.isPiecesMode,
  ],
  () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(fetchCost, 300)
  },
  { deep: true, immediate: true },
)
</script>

<template>
  <div
    v-if="ingredients.some((i) => i.product_id != null || i.sub_recipe_id != null)"
    class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
  >
    <p class="text-sm font-medium text-gray-700 mb-1">Стоимость порции</p>

    <div v-if="costData?.cost_per_portion !== null && costData?.cost_per_portion !== undefined">
      <p class="tabular-nums">
        <span
          class="text-lg font-semibold transition-opacity duration-150"
          :class="[
            costLoading ? 'opacity-50' : '',
            costData.cost_is_partial ? 'text-amber-700' : 'text-emerald-700',
          ]"
        >~{{ costData.cost_per_portion.toFixed(2) }}</span>
        <span
          class="text-sm ml-1"
          :class="costData.cost_is_partial ? 'text-amber-600' : 'text-emerald-600'"
        >руб./порц.</span>
        <span
          v-if="isPiecesMode && piecesPerPortion"
          class="text-sm text-gray-500 ml-1"
        >({{ piecesPerPortion }} шт.)</span>
      </p>

      <p v-if="costData.total_cost !== null" class="text-xs text-gray-500 mt-0.5">
        Стоимость рецепта: ~{{ costData.total_cost.toFixed(2) }} руб.
        ({{ costData.computed_servings }} порц.)
      </p>

      <!-- Partial warning -->
      <div
        v-if="costData.cost_is_partial"
        class="mt-2 flex items-start gap-2 rounded-md bg-amber-50 border border-amber-200 px-3 py-2"
      >
        <svg class="w-4 h-4 text-amber-500 mt-0.5 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
        <p class="text-xs text-amber-800">
          Стоимость рассчитана не полностью: не у всех ингредиентов указана цена.
        </p>
      </div>

      <!-- Breakdown toggle -->
      <button
        v-if="costData.ingredient_costs.length > 0"
        type="button"
        class="mt-2 text-sm text-gray-600 underline hover:text-gray-800"
        @click="breakdownExpanded = !breakdownExpanded"
      >
        {{ breakdownExpanded ? 'Скрыть разбивку стоимости' : 'Показать разбивку стоимости' }}
      </button>

      <!-- Breakdown list -->
      <div v-if="breakdownExpanded && costData.ingredient_costs.length > 0" class="mt-2 rounded-lg border border-gray-200 bg-white">
        <ul class="divide-y divide-gray-100">
          <li
            v-for="item in costData.ingredient_costs"
            :key="item.product_id"
            class="flex items-center justify-between px-3 py-1.5 text-xs"
          >
            <span class="flex-1 min-w-0 truncate text-gray-700">{{ item.product_name }}</span>
            <span class="text-gray-400 mx-2 shrink-0">{{ item.quantity_amount.toFixed(1) }} {{ item.quantity_unit }}</span>
            <span
              v-if="item.cost_amount !== null"
              class="shrink-0 tabular-nums text-gray-600"
            >~{{ item.cost_amount.toFixed(2) }} руб.</span>
            <span v-else class="shrink-0 text-amber-600 italic">нет цены</span>
          </li>
        </ul>
        <div class="flex justify-between px-3 py-2 border-t border-gray-200 text-sm font-medium">
          <span class="text-gray-700">Итого:</span>
          <span
            class="tabular-nums"
            :class="costData.cost_is_partial ? 'text-amber-700' : 'text-emerald-700'"
          >~{{ costData.total_cost?.toFixed(2) }} руб.</span>
        </div>
      </div>
    </div>

    <!-- No cost available -->
    <p v-else-if="costData !== null" class="text-sm text-gray-400">
      Стоимость не может быть рассчитана
    </p>

    <!-- Loading (no data yet) -->
    <p v-else-if="costLoading" class="text-sm text-gray-400">
      Расчёт...
    </p>
  </div>
</template>
