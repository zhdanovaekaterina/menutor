<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MealIngredient, MealOccurrence, MealSummaryRecipe } from '@/api/types'
import { formatUnit } from '@/utils/units'

const DAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const props = defineProps<{
  recipe: MealSummaryRecipe
  selectedSlots: Set<number>
  scaledIngredients: MealIngredient[]
}>()

const emit = defineEmits<{
  toggleRecipe: []
  toggleSlot: [slotIndex: number]
}>()

const expanded = ref(true)

// Checkbox state: checked = all selected, indeterminate = some selected, unchecked = none
const checkState = computed<'all' | 'some' | 'none'>(() => {
  const total = props.recipe.occurrences.length
  const selected = props.recipe.occurrences.filter(o => props.selectedSlots.has(o.slot_index)).length
  if (selected === 0) return 'none'
  if (selected === total) return 'all'
  return 'some'
})

const totalSelectedServings = computed(() => {
  return props.recipe.occurrences
    .filter(o => props.selectedSlots.has(o.slot_index))
    .reduce((sum, o) => sum + o.servings, 0)
})

function occurrenceLabel(occ: MealOccurrence): string {
  return `${DAY_LABELS[occ.day] ?? ''}, ${occ.meal_type}`
}

function formatQuantity(n: number): string {
  return String(Math.round(n * 100) / 100)
}
</script>

<template>
  <div
    :class="[
      'rounded-xl border transition-all',
      checkState !== 'none'
        ? 'bg-white border-gray-200'
        : 'bg-gray-50 border-gray-100 opacity-60',
    ]"
  >
    <!-- Card header row -->
    <div class="flex items-center gap-3 px-3 sm:px-4 py-3">
      <!-- Checkbox (three-state) -->
      <button
        class="shrink-0 p-2.5 sm:p-0 -m-2.5 sm:m-0"
        :aria-checked="checkState === 'all' ? 'true' : checkState === 'some' ? 'mixed' : 'false'"
        role="checkbox"
        @click="emit('toggleRecipe')"
      >
        <div
          class="w-5 h-5 rounded border-2 flex items-center justify-center transition-colors"
          :class="
            checkState === 'all'
              ? 'bg-blue-600 border-blue-600 text-white'
              : checkState === 'some'
                ? 'bg-blue-100 border-blue-400 text-blue-600'
                : 'border-gray-300 hover:border-gray-400'
          "
        >
          <!-- Checked -->
          <svg v-if="checkState === 'all'" class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
          <!-- Indeterminate -->
          <svg v-else-if="checkState === 'some'" class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
      </button>

      <!-- Recipe name + servings summary -->
      <div class="flex-1 min-w-0">
        <h3
          :class="[
            'text-sm font-semibold truncate',
            checkState !== 'none' ? 'text-gray-900' : 'text-gray-400',
          ]"
        >
          {{ recipe.recipe_name }}
        </h3>
        <p class="text-xs text-gray-400 mt-0.5">
          <template v-if="checkState !== 'none'">
            {{ totalSelectedServings }} порц. · {{ recipe.occurrences.length }}
            {{ recipe.occurrences.length === 1 ? 'приём пищи' : recipe.occurrences.length < 5 ? 'приёма пищи' : 'приёмов пищи' }}
          </template>
          <template v-else>
            <span class="text-amber-500">Не выбрано</span>
          </template>
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

    <!-- Expandable body -->
    <Transition name="expand">
      <div v-if="expanded" class="border-t border-gray-100">
        <!-- Block 1: Meal slots -->
        <div class="px-3 sm:px-4 py-2.5">
          <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Приёмы пищи</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="occ in recipe.occurrences"
              :key="occ.slot_index"
              class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs transition-colors"
              :class="
                selectedSlots.has(occ.slot_index)
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-gray-50 border-gray-200 text-gray-400'
              "
              @click="emit('toggleSlot', occ.slot_index)"
            >
              <!-- Mini checkbox dot -->
              <span
                class="w-3 h-3 rounded border flex items-center justify-center shrink-0 transition-colors"
                :class="
                  selectedSlots.has(occ.slot_index)
                    ? 'bg-blue-500 border-blue-500'
                    : 'border-gray-300'
                "
              >
                <svg v-if="selectedSlots.has(occ.slot_index)" class="w-2 h-2 text-white" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </span>
              {{ occurrenceLabel(occ) }}
              <span class="text-gray-400">{{ occ.servings }} порц.</span>
            </button>
          </div>
        </div>

        <!-- Block 2: Ingredients for selected slots -->
        <div class="border-t border-gray-100 px-3 sm:px-4 py-2.5">
          <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
            Ингредиенты
            <span v-if="checkState !== 'all'" class="normal-case font-normal">(для выбранных приёмов)</span>
          </p>

          <template v-if="scaledIngredients.length === 0 || checkState === 'none'">
            <p class="text-xs text-gray-300 italic">Нет ингредиентов</p>
          </template>
          <ul v-else class="space-y-0.5">
            <li
              v-for="(ing, i) in scaledIngredients"
              :key="ing.sub_recipe_id != null ? `sr-${ing.sub_recipe_id}` : `p-${ing.product_id ?? i}`"
              class="flex items-baseline justify-between gap-2 text-sm py-0.5"
            >
              <!-- Sub-recipe ingredient -->
              <template v-if="ing.sub_recipe_id != null">
                <span class="flex items-center gap-1.5 min-w-0 text-amber-700">
                  <span class="shrink-0 w-3.5 h-3.5 rounded-sm bg-amber-100 border border-amber-300 flex items-center justify-center">
                    <svg class="w-2 h-2 text-amber-600" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                  </span>
                  <span class="truncate">{{ ing.sub_recipe_name ?? 'Вложенный рецепт' }}</span>
                </span>
                <span class="text-amber-500 whitespace-nowrap shrink-0 text-xs">
                  {{ formatQuantity(ing.quantity_amount) }} {{ formatUnit(ing.quantity_unit) }}
                </span>
              </template>

              <!-- Regular ingredient -->
              <template v-else>
                <span class="flex items-center gap-1.5 min-w-0 text-gray-700">
                  <span class="shrink-0 w-1 h-1 rounded-full bg-gray-400 mt-0.5" />
                  <span class="truncate">{{ ing.product_name }}</span>
                </span>
                <span class="text-gray-400 whitespace-nowrap shrink-0 text-xs">
                  {{ formatQuantity(ing.quantity_amount) }} {{ formatUnit(ing.quantity_unit) }}
                </span>
              </template>
            </li>
          </ul>
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
  max-height: 1200px;
  opacity: 1;
}
</style>
