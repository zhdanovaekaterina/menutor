<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ActiveCategory, FamilyMember, MenuSlot, Product, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'
import { useTabbedFilter } from '@/composables/useTabbedFilter'
import IconCheck from '@/components/ui/icons/IconCheck.vue'

const props = defineProps<{
  open: boolean
  day: number
  mealType: string
  dayLabel: string
  recipes: Recipe[]
  products: Product[]
  existingSlots: MenuSlot[]
  recipeCategories: ActiveCategory[]
  productCategories: ActiveCategory[]
  familyMembers?: FamilyMember[]
  activeMemberIds?: Set<number>
  blockedRecipeIds?: Set<number>
  blockedProductIds?: Set<number>
}>()

const emit = defineEmits<{
  close: []
  select: [data: { type: 'recipe' | 'product'; id: number }]
  remove: [data: { type: 'recipe' | 'product'; id: number }]
}>()

const {
  tab, search, recipeCF, productCF, switchTab, filteredRecipes, filteredProducts,
} = useTabbedFilter<Recipe, Product>(
  () => props.recipes,
  () => props.products,
)

// Track which items are already in this cell
const existingRecipeIds = computed(() =>
  new Set(props.existingSlots.filter(s => s.recipe_id != null).map(s => s.recipe_id!))
)
const existingProductIds = computed(() =>
  new Set(props.existingSlots.filter(s => s.product_id != null).map(s => s.product_id!))
)

// Sort blocked items to the bottom
const sortedRecipes = computed(() => {
  const blocked = props.blockedRecipeIds
  if (!blocked?.size) return filteredRecipes.value
  return [...filteredRecipes.value].sort((a, b) => {
    const aB = blocked.has(a.id) ? 1 : 0
    const bB = blocked.has(b.id) ? 1 : 0
    return aB - bB
  })
})

const sortedProducts = computed(() => {
  const blocked = props.blockedProductIds
  if (!blocked?.size) return filteredProducts.value
  return [...filteredProducts.value].sort((a, b) => {
    const aB = blocked.has(a.id) ? 1 : 0
    const bB = blocked.has(b.id) ? 1 : 0
    return aB - bB
  })
})

// Recently added IDs for flash feedback (cleared on close)
const justAdded = ref<Set<string>>(new Set())

function onSelectItem(type: 'recipe' | 'product', id: number) {
  const key = `${type}-${id}`
  const alreadySelected =
    type === 'recipe' ? existingRecipeIds.value.has(id) : existingProductIds.value.has(id)
  if (alreadySelected) {
    emit('remove', { type, id })
    return
  }
  if (justAdded.value.has(key)) return // debounce
  justAdded.value = new Set([...justAdded.value, key])
  emit('select', { type, id })
  setTimeout(() => {
    justAdded.value = new Set([...justAdded.value].filter(k => k !== key))
  }, 300)
}

// Reset state when sheet opens/closes
watch(() => props.open, (v) => {
  if (v) {
    search.value = ''
    tab.value = 'recipes'
    recipeCF.reset()
    productCF.reset()
    justAdded.value = new Set()
    // Push history entry so Android back dismisses the sheet
    history.pushState({ mobilePicker: true }, '')
    const handler = () => {
      emit('close')
      window.removeEventListener('popstate', handler)
    }
    window.addEventListener('popstate', handler)
  }
})

const activeMemberNames = computed(() => {
  if (!props.familyMembers?.length || !props.activeMemberIds?.size) return ''
  return props.familyMembers
    .filter(m => props.activeMemberIds!.has(m.id))
    .map(m => m.name)
    .join(', ')
})

const activePortions = computed(() => {
  if (!props.familyMembers?.length || !props.activeMemberIds?.size) return 0
  return props.familyMembers
    .filter(m => props.activeMemberIds!.has(m.id))
    .reduce((sum, m) => sum + m.portion_multiplier, 0)
})

// Sheet drag-to-dismiss logic
const sheetRef = ref<HTMLElement | null>(null)
const dragY = ref(0)
const dragging = ref(false)
let startY = 0

function onTouchStart(e: TouchEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('[data-sheet-handle]')) return
  if (!e.touches[0]) return
  startY = e.touches[0].clientY
  dragging.value = true
  dragY.value = 0
}

function onTouchMove(e: TouchEvent) {
  if (!dragging.value) return
  if (!e.touches[0]) return
  const delta = e.touches[0].clientY - startY
  if (delta > 0) {
    dragY.value = delta
    e.preventDefault()
  }
}

function onTouchEnd() {
  if (!dragging.value) return
  dragging.value = false
  if (dragY.value > 120) {
    emit('close')
  }
  dragY.value = 0
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="fade">
      <div
        v-if="open"
        class="lg:hidden fixed inset-0 bg-black/30 z-40"
        @click="emit('close')"
      />
    </Transition>

    <!-- Bottom Sheet -->
    <Transition name="sheet">
      <div
        v-if="open"
        ref="sheetRef"
        class="lg:hidden fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl flex flex-col"
        style="max-height: 85vh; height: 60vh;"
        :style="dragging ? { transform: `translateY(${dragY}px)` } : {}"
        role="dialog"
        aria-modal="true"
        aria-label="Выбор блюда"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
      >
        <!-- Handle -->
        <div data-sheet-handle class="flex justify-center py-3 cursor-grab shrink-0">
          <div class="w-9 h-1 rounded-full bg-gray-300" />
        </div>

        <!-- Header -->
        <div class="flex items-center justify-between px-4 pb-2 shrink-0">
          <h3 class="font-semibold text-base">
            {{ mealType }}, {{ dayLabel }} — добавить
          </h3>
          <button
            class="p-2 -mr-2 rounded-lg hover:bg-gray-100 text-gray-500"
            aria-label="Закрыть"
            @click="emit('close')"
          >
            <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex border-b px-4 shrink-0" role="tablist">
          <button
            role="tab"
            :aria-selected="tab === 'recipes'"
            :class="tab === 'recipes' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'"
            class="flex-1 py-2.5 text-sm font-medium"
            @click="switchTab('recipes')"
          >
            Блюда
          </button>
          <button
            role="tab"
            :aria-selected="tab === 'products'"
            :class="tab === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'"
            class="flex-1 py-2.5 text-sm font-medium"
            @click="switchTab('products')"
          >
            Ингредиенты
          </button>
        </div>

        <!-- Active member info (recipes tab only) -->
        <div v-if="familyMembers?.length && tab === 'recipes' && activeMemberIds?.size" class="text-xs text-gray-500 px-4 py-1 shrink-0">
          Для: {{ activeMemberNames }} ({{ activePortions.toFixed(1) }} п.)
        </div>

        <!-- Search + Category filter -->
        <div class="px-4 pt-2 pb-1 shrink-0 flex flex-col gap-2">
          <SearchInput v-model="search" />
          <select
            :model-value="tab === 'recipes' ? recipeCF.categoryFilter.value : productCF.categoryFilter.value"
            class="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            @change="(e: Event) => {
              const v = (e.target as HTMLSelectElement).value
              const val = v === '' ? null : Number(v)
              if (tab === 'recipes') recipeCF.categoryFilter.value = val
              else productCF.categoryFilter.value = val
            }"
          >
            <option :value="null">Все категории</option>
            <option
              v-for="c in tab === 'recipes' ? recipeCategories : productCategories"
              :key="c.id"
              :value="c.id"
            >{{ c.name }}</option>
          </select>
        </div>

        <!-- Item List -->
        <div class="flex-1 overflow-y-auto overscroll-contain" role="listbox">
          <!-- Recipes tab -->
          <template v-if="tab === 'recipes'">
            <div v-if="sortedRecipes.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-400 text-sm">
              <span v-if="recipes.length === 0">Нет блюд</span>
              <span v-else>Ничего не найдено</span>
            </div>
            <button
              v-for="r in sortedRecipes"
              :key="r.id"
              role="option"
              class="w-full flex items-center gap-3 px-4 py-3 text-left text-base transition-colors border-b border-gray-100"
              :class="[
                justAdded.has(`recipe-${r.id}`) ? 'bg-green-50' : 'active:bg-gray-100',
                blockedRecipeIds?.has(r.id) ? 'opacity-40' : '',
              ]"
              :title="blockedRecipeIds?.has(r.id) ? 'Не подходит по предпочтениям' : undefined"
              @click="onSelectItem('recipe', r.id)"
            >
              <span
                v-if="blockedRecipeIds?.has(r.id)"
                class="text-amber-500 shrink-0 text-sm leading-none"
                aria-label="Несовместимо с предпочтениями"
              >⚠</span>
              <span v-else class="w-2 h-2 rounded-full bg-blue-400 shrink-0" />
              <span class="flex-1 truncate">{{ r.name }}</span>
              <IconCheck v-if="existingRecipeIds.has(r.id)" class="w-4 h-4 text-green-500 shrink-0" />
            </button>
          </template>

          <!-- Products tab -->
          <template v-else>
            <div v-if="sortedProducts.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-400 text-sm">
              <span v-if="products.length === 0">Нет ингредиентов</span>
              <span v-else>Ничего не найдено</span>
            </div>
            <button
              v-for="p in sortedProducts"
              :key="p.id"
              role="option"
              class="w-full flex items-center gap-3 px-4 py-3 text-left text-base transition-colors border-b border-gray-100"
              :class="[
                justAdded.has(`product-${p.id}`) ? 'bg-green-50' : 'active:bg-gray-100',
                blockedProductIds?.has(p.id) ? 'opacity-40' : '',
              ]"
              :title="blockedProductIds?.has(p.id) ? 'Не подходит по предпочтениям' : undefined"
              @click="onSelectItem('product', p.id)"
            >
              <span
                v-if="blockedProductIds?.has(p.id)"
                class="text-amber-500 shrink-0 text-sm leading-none"
                aria-label="Несовместимо с предпочтениями"
              >⚠</span>
              <span v-else class="w-2 h-2 rounded-full bg-orange-400 shrink-0" />
              <span class="flex-1 truncate">{{ p.name }}</span>
              <IconCheck v-if="existingProductIds.has(p.id)" class="w-4 h-4 text-green-500 shrink-0" />
            </button>
          </template>
        </div>

        <!-- Safe area spacer for bottom notch -->
        <div class="shrink-0" style="height: env(safe-area-inset-bottom, 0px)" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-enter-active { transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1); }
.sheet-leave-active { transition: transform 0.2s ease-out; }
.sheet-enter-from, .sheet-leave-to { transform: translateY(100%); }

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active, .fade-leave-active,
  .sheet-enter-active, .sheet-leave-active {
    transition-duration: 0.01ms;
  }
}
</style>
