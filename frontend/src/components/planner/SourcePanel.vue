<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FamilyMember, Product, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const props = defineProps<{
  recipes: Recipe[]
  products: Product[]
  familyMembers: FamilyMember[]
}>()

const tab = ref<'recipes' | 'products'>('recipes')
const search = ref('')

const filteredRecipes = computed(() => {
  const q = search.value.toLowerCase()
  return q ? props.recipes.filter((r) => r.name.toLowerCase().includes(q)) : props.recipes
})

const filteredProducts = computed(() => {
  const q = search.value.toLowerCase()
  return q ? props.products.filter((p) => p.name.toLowerCase().includes(q)) : props.products
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
        @click="tab = 'recipes'; search = ''"
      >
        Блюда
      </button>
      <button
        :class="tab === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'"
        class="flex-1 py-2 text-sm font-medium"
        @click="tab = 'products'; search = ''"
      >
        Ингредиенты
      </button>
    </div>

    <SearchInput v-model="search" />

    <!-- Recipe list -->
    <ul v-if="tab === 'recipes'" class="flex-1 overflow-y-auto text-sm divide-y">
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

    <!-- Product list -->
    <ul v-else class="flex-1 overflow-y-auto text-sm divide-y">
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
  </div>
</template>
