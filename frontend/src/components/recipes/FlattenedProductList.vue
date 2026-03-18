<template>
  <div class="mt-3">
    <div class="flex items-center gap-2">
      <button
        type="button"
        class="text-sm text-amber-700 underline hover:text-amber-900"
        @click="toggle"
      >
        {{ expanded ? 'Скрыть продукты' : 'Показать все продукты' }}
      </button>
      <button
        v-if="isDirty && loaded"
        type="button"
        title="Пересчитать продукты"
        class="flex items-center justify-center w-6 h-6 rounded-full bg-amber-100 text-amber-700 hover:bg-amber-200 hover:text-amber-900 transition-colors"
        :class="{ 'animate-spin': loading }"
        @click="refresh"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
          <path d="M3 3v5h5" />
        </svg>
      </button>
    </div>
    <div v-if="expanded" class="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
      <div v-if="loading" class="text-sm text-gray-500">Загрузка...</div>
      <div v-else-if="products.length === 0" class="text-sm text-gray-500">
        Нет продуктов
      </div>
      <ul v-else class="space-y-1">
        <li
          v-for="p in products"
          :key="p.product_id"
          class="flex justify-between text-sm text-gray-700"
        >
          <span>{{ p.product_name }}</span>
          <span class="text-gray-500">{{ p.quantity_amount }} {{ unitLabel(p.quantity_unit) }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { previewFlattenedProducts } from '@/api/client'
import type { FlattenedProduct, IngredientRow } from '@/api/types'

const props = defineProps<{
  recipeId: number
  ingredients: IngredientRow[]
  isDirty?: boolean
}>()

const emit = defineEmits<{
  refreshed: []
}>()

const expanded = ref(false)
const loading = ref(false)
const products = ref<FlattenedProduct[]>([])
const loaded = ref(false)

async function toggle() {
  expanded.value = !expanded.value
  if (expanded.value && !loaded.value) {
    await load()
  }
}

async function load() {
  loading.value = true
  try {
    products.value = await previewFlattenedProducts(props.recipeId, props.ingredients)
    loaded.value = true
    emit('refreshed')
  } finally {
    loading.value = false
  }
}

async function refresh() {
  await load()
}

function unitLabel(unit: string): string {
  const MAP: Record<string, string> = {
    g: 'г', kg: 'кг', ml: 'мл', l: 'л', tsp: 'ч.л.', tbsp: 'ст.л.',
    cup: 'ст.', oz: 'унц.', lb: 'фунт', pcs: 'шт', pack: 'уп.', serv: 'порц.',
  }
  return MAP[unit] ?? unit
}
</script>
