<script setup lang="ts">
import { ref } from 'vue'
import type { MealSummaryProduct, MealSummaryProductOccurrence } from '@/api/types'
import { formatUnit } from '@/utils/units'

const DAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const MEAL_TYPE_ORDER = ['Завтрак', 'Обед', 'Ужин']

function mealTypeRank(mt: string): number {
  const i = MEAL_TYPE_ORDER.indexOf(mt)
  return i === -1 ? MEAL_TYPE_ORDER.length : i
}

function sortOccurrences<T extends { day: number; meal_type: string }>(occs: T[]): T[] {
  return [...occs].sort((a, b) => a.day - b.day || mealTypeRank(a.meal_type) - mealTypeRank(b.meal_type))
}

defineProps<{ product: MealSummaryProduct }>()

const expanded = ref(false)

function fmtQty(n: number): string {
  return String(Math.round(n * 100) / 100)
}

function occurrenceLabel(occ: MealSummaryProductOccurrence): string {
  return `${DAY_LABELS[occ.day] ?? ''}, ${occ.meal_type}`
}
</script>

<template>
  <div class="rounded-xl border bg-white border-gray-200 transition-all">
    <!-- Card header row -->
    <div class="flex items-center gap-3 px-3 sm:px-4 py-3">
      <!-- Product icon -->
      <div class="shrink-0 w-5 h-5 rounded border-2 bg-orange-100 border-orange-300 flex items-center justify-center">
        <svg class="w-3 h-3 text-orange-500" viewBox="0 0 20 20" fill="currentColor">
          <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
        </svg>
      </div>

      <!-- Name + totals -->
      <div class="flex-1 min-w-0">
        <h3 class="text-sm font-semibold truncate text-gray-900">{{ product.product_name }}</h3>
        <p class="text-xs text-gray-400 mt-0.5">
          {{ fmtQty(product.total_quantity) }} {{ formatUnit(product.unit) }} · {{ product.occurrences.length }}
          {{ product.occurrences.length === 1 ? 'приём пищи' : product.occurrences.length < 5 ? 'приёма пищи' : 'приёмов пищи' }}
        </p>
      </div>

      <!-- Expand/collapse toggle -->
      <button
        class="shrink-0 p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        <svg
          class="w-4 h-4 transition-transform duration-200"
          :class="{ 'rotate-180': expanded }"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Expandable: meal slots -->
    <Transition name="expand">
      <div v-if="expanded" class="border-t border-gray-100 px-3 sm:px-4 py-2.5">
        <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Приёмы пищи</p>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="occ in sortOccurrences(product.occurrences)"
            :key="occ.slot_index"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs bg-orange-50 border-orange-200 text-orange-700"
          >
            {{ occurrenceLabel(occ) }}
            <span class="text-orange-400">— {{ fmtQty(occ.quantity) }} {{ formatUnit(occ.unit) }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
.expand-enter-to,
.expand-leave-from {
  max-height: 400px;
  opacity: 1;
}
</style>
