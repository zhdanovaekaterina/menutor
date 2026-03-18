<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { MenuSlot, Product, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const props = defineProps<{
  open: boolean
  day: number
  mealType: string
  dayLabel: string
  recipes: Recipe[]
  products: Product[]
  existingSlots: MenuSlot[]
}>()

const emit = defineEmits<{
  close: []
  select: [data: { type: 'recipe' | 'product'; id: number }]
}>()

const tab = ref<'recipes' | 'products'>('recipes')
const search = ref('')

// Filter items by search query
const filteredRecipes = computed(() => {
  const q = search.value.toLowerCase()
  return q ? props.recipes.filter(r => r.name.toLowerCase().includes(q)) : props.recipes
})

const filteredProducts = computed(() => {
  const q = search.value.toLowerCase()
  return q ? props.products.filter(p => p.name.toLowerCase().includes(q)) : props.products
})

// Track which items are already in this cell
const existingRecipeIds = computed(() =>
  new Set(props.existingSlots.filter(s => s.recipe_id != null).map(s => s.recipe_id!))
)
const existingProductIds = computed(() =>
  new Set(props.existingSlots.filter(s => s.product_id != null).map(s => s.product_id!))
)

// Recently added IDs for flash feedback (cleared on close)
const justAdded = ref<Set<string>>(new Set())

function onSelectItem(type: 'recipe' | 'product', id: number) {
  const key = `${type}-${id}`
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
            @click="tab = 'recipes'; search = ''"
          >
            Блюда
          </button>
          <button
            role="tab"
            :aria-selected="tab === 'products'"
            :class="tab === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'"
            class="flex-1 py-2.5 text-sm font-medium"
            @click="tab = 'products'; search = ''"
          >
            Ингредиенты
          </button>
        </div>

        <!-- Search -->
        <div class="px-4 py-2 shrink-0">
          <SearchInput v-model="search" />
        </div>

        <!-- Item List -->
        <div class="flex-1 overflow-y-auto overscroll-contain" role="listbox">
          <!-- Recipes tab -->
          <template v-if="tab === 'recipes'">
            <div v-if="filteredRecipes.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-400 text-sm">
              <span v-if="recipes.length === 0">Нет блюд</span>
              <span v-else>Ничего не найдено</span>
            </div>
            <button
              v-for="r in filteredRecipes"
              :key="r.id"
              role="option"
              class="w-full flex items-center gap-3 px-4 py-3 text-left text-base active:bg-gray-100 transition-colors border-b border-gray-100"
              :class="justAdded.has(`recipe-${r.id}`) ? 'bg-green-50' : ''"
              @click="onSelectItem('recipe', r.id)"
            >
              <span class="w-2 h-2 rounded-full bg-blue-400 shrink-0" />
              <span class="flex-1 truncate">{{ r.name }}</span>
              <svg
                v-if="existingRecipeIds.has(r.id)"
                class="w-4 h-4 text-green-500 shrink-0"
                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            </button>
          </template>

          <!-- Products tab -->
          <template v-else>
            <div v-if="filteredProducts.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-400 text-sm">
              <span v-if="products.length === 0">Нет ингредиентов</span>
              <span v-else>Ничего не найдено</span>
            </div>
            <button
              v-for="p in filteredProducts"
              :key="p.id"
              role="option"
              class="w-full flex items-center gap-3 px-4 py-3 text-left text-base active:bg-gray-100 transition-colors border-b border-gray-100"
              :class="justAdded.has(`product-${p.id}`) ? 'bg-green-50' : ''"
              @click="onSelectItem('product', p.id)"
            >
              <span class="w-2 h-2 rounded-full bg-orange-400 shrink-0" />
              <span class="flex-1 truncate">{{ p.name }}</span>
              <svg
                v-if="existingProductIds.has(p.id)"
                class="w-4 h-4 text-green-500 shrink-0"
                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
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
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

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
