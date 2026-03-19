<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ActiveCategory, Product, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'
import { useCategoryFilter } from '@/composables/useCategoryFilter'

type IngredientRow = {
  product_id: number | null
  sub_recipe_id: number | null
  quantity_amount: number
  quantity_unit: string
}

const props = defineProps<{
  open: boolean
  products: Product[]
  recipes: Recipe[]
  currentRecipeId: number | null
  ancestorIds?: Set<number>
  productCategories: ActiveCategory[]
  recipeCategories: ActiveCategory[]
  // Currently committed ingredients so we can pre-mark selected items
  existingIngredients: IngredientRow[]
}>()

type PickerDelta = {
  added: IngredientRow[]
  removedProductIds: Set<number>
  removedRecipeIds: Set<number>
}

const emit = defineEmits<{
  close: []
  confirm: [delta: PickerDelta]
}>()

// ------- tab state -------
const tab = ref<'products' | 'recipes'>('products')
const search = ref('')
const productCF = useCategoryFilter<Product>()
const recipeCF = useCategoryFilter<Recipe>()

function switchTab(next: 'products' | 'recipes') {
  tab.value = next
  search.value = ''
  productCF.reset()
  recipeCF.reset()
}

// ------- filtered lists -------
const filteredProducts = computed(() => productCF.applyFilter(props.products, search.value))
const filteredRecipes = computed(() =>
  recipeCF.applyFilter(
    props.recipes.filter((r) => {
      if (props.currentRecipeId != null && r.id === props.currentRecipeId) return false
      if (props.ancestorIds?.has(r.id)) return false
      return true
    }),
    search.value,
  ),
)

// ------- selection state (local, while modal is open) -------
// We track the full set: existing + newly toggled.
// On open we seed it from existingIngredients.
const selectedProductIds = ref<Set<number>>(new Set())
const selectedRecipeIds = ref<Set<number>>(new Set())

// The ingredient rows that were already present when the modal opened.
// We track them so we can detect newly-added vs. already-existing.
const originalProductIds = ref<Set<number>>(new Set())
const originalRecipeIds = ref<Set<number>>(new Set())

function seedFromExisting() {
  const pIds = new Set<number>()
  const rIds = new Set<number>()
  for (const ing of props.existingIngredients) {
    if (ing.product_id != null) pIds.add(ing.product_id)
    if (ing.sub_recipe_id != null) rIds.add(ing.sub_recipe_id)
  }
  selectedProductIds.value = new Set(pIds)
  selectedRecipeIds.value = new Set(rIds)
  originalProductIds.value = new Set(pIds)
  originalRecipeIds.value = new Set(rIds)
}

watch(
  () => props.open,
  (v) => {
    if (v) {
      seedFromExisting()
      search.value = ''
      tab.value = 'products'
      productCF.reset()
      recipeCF.reset()
    }
  },
)

function toggleProduct(id: number) {
  const s = new Set(selectedProductIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedProductIds.value = s
}

function toggleRecipe(id: number) {
  const s = new Set(selectedRecipeIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedRecipeIds.value = s
}

// ------- summary -------
const addedCount = computed(() => {
  let n = 0
  for (const id of selectedProductIds.value) {
    if (!originalProductIds.value.has(id)) n++
  }
  for (const id of selectedRecipeIds.value) {
    if (!originalRecipeIds.value.has(id)) n++
  }
  return n
})

const removedCount = computed(() => {
  let n = 0
  for (const id of originalProductIds.value) {
    if (!selectedProductIds.value.has(id)) n++
  }
  for (const id of originalRecipeIds.value) {
    if (!selectedRecipeIds.value.has(id)) n++
  }
  return n
})

const totalSelected = computed(
  () => selectedProductIds.value.size + selectedRecipeIds.value.size,
)

// ------- confirm -------
function onConfirm() {
  const added: IngredientRow[] = []

  for (const id of selectedProductIds.value) {
    if (originalProductIds.value.has(id)) continue
    const product = props.products.find((p) => p.id === id)
    const unit = product?.recipe_unit ?? 'g'
    added.push({
      product_id: id,
      sub_recipe_id: null,
      quantity_unit: unit,
      quantity_amount: unit === 'g' ? 100 : 1,
    })
  }

  for (const id of selectedRecipeIds.value) {
    if (originalRecipeIds.value.has(id)) continue
    added.push({
      product_id: null,
      sub_recipe_id: id,
      quantity_unit: 'serv',
      quantity_amount: 1,
    })
  }

  const removedProductIds = new Set<number>()
  for (const id of originalProductIds.value) {
    if (!selectedProductIds.value.has(id)) removedProductIds.add(id)
  }
  const removedRecipeIds = new Set<number>()
  for (const id of originalRecipeIds.value) {
    if (!selectedRecipeIds.value.has(id)) removedRecipeIds.add(id)
  }

  emit('confirm', { added, removedProductIds, removedRecipeIds })
  emit('close')
}

// ESC key support
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-label="Выбор ингредиентов"
        @click.self="emit('close')"
        @keydown="onKeydown"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col" style="max-height: min(85vh, 640px);">

          <!-- Header -->
          <div class="flex items-center justify-between px-5 pt-5 pb-3 shrink-0">
            <h3 class="text-base font-semibold text-gray-900">Выбрать ингредиенты</h3>
            <button
              type="button"
              class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
              aria-label="Закрыть"
              @click="emit('close')"
            >
              <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Tabs -->
          <div class="flex border-b px-5 shrink-0" role="tablist">
            <button
              role="tab"
              :aria-selected="tab === 'products'"
              :class="tab === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'"
              class="flex-1 py-2.5 text-sm font-medium transition-colors"
              type="button"
              @click="switchTab('products')"
            >
              Продукты
            </button>
            <button
              role="tab"
              :aria-selected="tab === 'recipes'"
              :class="tab === 'recipes' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'"
              class="flex-1 py-2.5 text-sm font-medium transition-colors"
              type="button"
              @click="switchTab('recipes')"
            >
              Рецепты
            </button>
          </div>

          <!-- Search + Category filter -->
          <div class="px-4 pt-3 pb-2 shrink-0 flex flex-col gap-2">
            <SearchInput v-model="search" />
            <select
              :model-value="tab === 'products' ? productCF.categoryFilter.value : recipeCF.categoryFilter.value"
              class="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              @change="(e: Event) => {
                const v = (e.target as HTMLSelectElement).value
                const val = v === '' ? null : Number(v)
                if (tab === 'products') productCF.categoryFilter.value = val
                else recipeCF.categoryFilter.value = val
              }"
            >
              <option :value="null">Все категории</option>
              <option
                v-for="c in tab === 'products' ? productCategories : recipeCategories"
                :key="c.id"
                :value="c.id"
              >{{ c.name }}</option>
            </select>
          </div>

          <!-- Item list -->
          <div class="flex-1 overflow-y-auto" role="listbox" aria-multiselectable="true">
            <!-- Products tab -->
            <template v-if="tab === 'products'">
              <div
                v-if="filteredProducts.length === 0"
                class="flex items-center justify-center py-10 text-gray-400 text-sm"
              >
                <span v-if="products.length === 0">Нет продуктов</span>
                <span v-else>Ничего не найдено</span>
              </div>
              <button
                v-for="p in filteredProducts"
                :key="p.id"
                type="button"
                role="option"
                :aria-selected="selectedProductIds.has(p.id)"
                class="w-full flex items-center gap-3 px-4 py-3 text-left text-sm hover:bg-gray-50 transition-colors border-b border-gray-100"
                :class="selectedProductIds.has(p.id) ? 'bg-blue-50' : ''"
                @click="toggleProduct(p.id)"
              >
                <span class="w-2 h-2 rounded-full bg-orange-400 shrink-0" />
                <span class="flex-1 truncate">{{ p.name }}</span>
                <!-- Checkmark when selected -->
                <span
                  v-if="selectedProductIds.has(p.id)"
                  class="shrink-0"
                >
                  <svg class="w-4 h-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                </span>
              </button>
            </template>

            <!-- Recipes tab -->
            <template v-else>
              <div
                v-if="filteredRecipes.length === 0"
                class="flex items-center justify-center py-10 text-gray-400 text-sm"
              >
                <span v-if="recipes.length === 0">Нет рецептов</span>
                <span v-else>Ничего не найдено</span>
              </div>
              <button
                v-for="r in filteredRecipes"
                :key="r.id"
                type="button"
                role="option"
                :aria-selected="selectedRecipeIds.has(r.id)"
                class="w-full flex items-center gap-3 px-4 py-3 text-left text-sm hover:bg-gray-50 transition-colors border-b border-gray-100"
                :class="selectedRecipeIds.has(r.id) ? 'bg-amber-50' : ''"
                @click="toggleRecipe(r.id)"
              >
                <span class="w-2 h-2 rounded-full bg-blue-400 shrink-0" />
                <span class="flex-1 truncate">{{ r.name }}</span>
                <!-- Checkmark when selected -->
                <span
                  v-if="selectedRecipeIds.has(r.id)"
                  class="shrink-0"
                >
                  <svg class="w-4 h-4 text-amber-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                </span>
              </button>
            </template>
          </div>

          <!-- Status bar + actions -->
          <div class="shrink-0 border-t border-gray-200 px-4 py-3 flex items-center gap-3">
            <div class="flex-1 text-xs text-gray-500 min-w-0">
              <span v-if="totalSelected === 0">Ничего не выбрано</span>
              <span v-else>
                Выбрано: <strong class="text-gray-800">{{ totalSelected }}</strong>
                <template v-if="addedCount > 0"> &middot; добавится: <strong class="text-blue-700">{{ addedCount }}</strong></template>
                <template v-if="removedCount > 0"> &middot; удалится: <strong class="text-red-600">{{ removedCount }}</strong></template>
              </span>
            </div>
            <button
              type="button"
              class="px-3 py-1.5 rounded-lg border border-gray-300 text-sm text-gray-600 hover:bg-gray-50 transition-colors shrink-0"
              @click="emit('close')"
            >
              Отмена
            </button>
            <button
              type="button"
              class="px-4 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors shrink-0"
              @click="onConfirm"
            >
              Готово
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active, .fade-leave-active { transition-duration: 0.01ms; }
}
</style>
