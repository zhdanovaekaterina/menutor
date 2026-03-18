<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ActiveCategory, FamilyMember, Product, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const props = defineProps<{
  recipes: Recipe[]
  products: Product[]
  familyMembers: FamilyMember[]
  recipeCategories: ActiveCategory[]
  productCategories: ActiveCategory[]
}>()

const tab = ref<'recipes' | 'products'>('recipes')
const search = ref('')
const categoryFilter = ref<number | null>(null)

function switchTab(next: 'recipes' | 'products') {
  tab.value = next
  search.value = ''
  categoryFilter.value = null
}

const filteredRecipes = computed(() => {
  const q = search.value.toLowerCase()
  return props.recipes.filter((r) => {
    if (categoryFilter.value !== null && r.category_id !== categoryFilter.value) return false
    if (q && !r.name.toLowerCase().includes(q)) return false
    return true
  })
})

const filteredProducts = computed(() => {
  const q = search.value.toLowerCase()
  return props.products.filter((p) => {
    if (categoryFilter.value !== null && p.category_id !== categoryFilter.value) return false
    if (q && !p.name.toLowerCase().includes(q)) return false
    return true
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
      v-model="categoryFilter"
      class="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
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
          v-for="r in filteredRecipes"
          :key="r.id"
          draggable="true"
          class="px-2 py-1.5 cursor-grab hover:bg-gray-100"
          @dragstart="onDragStart($event, 'recipe', r.id)"
        >
          {{ r.name }}
        </li>
      </ul>
      <div class="absolute bottom-0 inset-x-0 h-6 bg-gradient-to-t from-white to-transparent pointer-events-none" />
    </div>

    <!-- Product list -->
    <div v-else class="flex-1 relative overflow-hidden border rounded-lg">
      <ul class="absolute inset-0 overflow-y-auto text-sm divide-y pb-4">
        <li
          v-for="p in filteredProducts"
          :key="p.id"
          draggable="true"
          class="px-2 py-1.5 cursor-grab hover:bg-gray-100"
          @dragstart="onDragStart($event, 'product', p.id)"
        >
          {{ p.name }}
        </li>
      </ul>
      <div class="absolute bottom-0 inset-x-0 h-6 bg-gradient-to-t from-white to-transparent pointer-events-none" />
    </div>
  </div>
</template>
