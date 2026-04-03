<script setup lang="ts">
import { computed } from 'vue'
import type { ActiveCategory, FamilyMember, Product, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'
import { useTabbedFilter } from '@/composables/useTabbedFilter'

const props = defineProps<{
  recipes: Recipe[]
  products: Product[]
  familyMembers: FamilyMember[]
  recipeCategories: ActiveCategory[]
  productCategories: ActiveCategory[]
  blockedRecipeIds?: Set<number>
  blockedProductIds?: Set<number>
}>()

const {
  tab, search, recipeCF, productCF, switchTab, filteredRecipes, filteredProducts,
} = useTabbedFilter<Recipe, Product>(
  () => props.recipes,
  () => props.products,
)

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

function onDragStart(e: DragEvent, type: 'recipe' | 'product', id: number) {
  e.dataTransfer?.setData('application/json', JSON.stringify({ type, id }))
}
</script>

<template>
  <div class="flex flex-col h-full gap-2">
    <!-- Family info -->
    <div class="bg-gray-50 rounded-lg p-3">
      <h4 class="font-medium text-xs text-gray-700 mb-1">Семья</h4>
      <ul v-if="familyMembers.length" class="text-xs text-gray-600 space-y-0.5">
        <li v-for="m in familyMembers" :key="m.id">
          &bull; {{ m.name }} (&times;{{ m.portion_multiplier }})
        </li>
      </ul>
      <p v-else class="text-xs text-gray-400">Не добавлены</p>
    </div>

    <!-- Tabs -->
    <div class="flex border-b">
      <button
        :class="tab === 'recipes' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'"
        class="flex-1 py-2 text-sm font-medium"
        @click="switchTab('recipes')"
      >
        Блюда
      </button>
      <button
        :class="tab === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'"
        class="flex-1 py-2 text-sm font-medium"
        @click="switchTab('products')"
      >
        Ингредиенты
      </button>
    </div>

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

    <!-- Recipe list -->
    <div v-if="tab === 'recipes'" class="flex-1 relative overflow-hidden border rounded-lg">
      <ul class="absolute inset-0 overflow-y-auto text-sm divide-y pb-4">
        <li
          v-for="r in sortedRecipes"
          :key="r.id"
          draggable="true"
          class="px-2 py-1.5 cursor-grab flex items-center gap-1.5"
          :class="blockedRecipeIds?.has(r.id)
            ? 'opacity-40 hover:opacity-60'
            : 'hover:bg-gray-100'"
          :title="blockedRecipeIds?.has(r.id) ? 'Не подходит по предпочтениям' : undefined"
          @dragstart="onDragStart($event, 'recipe', r.id)"
        >
          <span
            v-if="blockedRecipeIds?.has(r.id)"
            class="shrink-0 text-amber-500"
            aria-label="Несовместимо с предпочтениями"
          >⚠</span>
          <span>{{ r.name }}</span>
        </li>
      </ul>
      <div class="absolute bottom-0 inset-x-0 h-6 bg-gradient-to-t from-white to-transparent pointer-events-none" />
    </div>

    <!-- Product list -->
    <div v-else class="flex-1 relative overflow-hidden border rounded-lg">
      <ul class="absolute inset-0 overflow-y-auto text-sm divide-y pb-4">
        <li
          v-for="p in sortedProducts"
          :key="p.id"
          draggable="true"
          class="px-2 py-1.5 cursor-grab flex items-center gap-1.5"
          :class="blockedProductIds?.has(p.id)
            ? 'opacity-40 hover:opacity-60'
            : 'hover:bg-gray-100'"
          :title="blockedProductIds?.has(p.id) ? 'Не подходит по предпочтениям' : undefined"
          @dragstart="onDragStart($event, 'product', p.id)"
        >
          <span
            v-if="blockedProductIds?.has(p.id)"
            class="shrink-0 text-amber-500"
            aria-label="Несовместимо с предпочтениями"
          >⚠</span>
          <span>{{ p.name }}</span>
        </li>
      </ul>
      <div class="absolute bottom-0 inset-x-0 h-6 bg-gradient-to-t from-white to-transparent pointer-events-none" />
    </div>
  </div>
</template>
