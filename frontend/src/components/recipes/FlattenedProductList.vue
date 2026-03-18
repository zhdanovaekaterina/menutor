<template>
  <div class="mt-3">
    <button
      type="button"
      class="text-sm text-amber-700 underline hover:text-amber-900"
      @click="toggle"
    >
      {{ expanded ? 'Скрыть продукты' : 'Показать все продукты' }}
    </button>
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
import { fetchFlattenedProducts } from '@/api/client'
import type { FlattenedProduct } from '@/api/types'

const props = defineProps<{ recipeId: number }>()

const expanded = ref(false)
const loading = ref(false)
const products = ref<FlattenedProduct[]>([])
const loaded = ref(false)

async function toggle() {
  expanded.value = !expanded.value
  if (expanded.value && !loaded.value) {
    loading.value = true
    try {
      products.value = await fetchFlattenedProducts(props.recipeId)
      loaded.value = true
    } finally {
      loading.value = false
    }
  }
}

function unitLabel(unit: string): string {
  const MAP: Record<string, string> = {
    g: 'г', kg: 'кг', ml: 'мл', l: 'л', tsp: 'ч.л.', tbsp: 'ст.л.',
    cup: 'ст.', oz: 'унц.', lb: 'фунт', pcs: 'шт', pack: 'уп.', serv: 'порц.',
  }
  return MAP[unit] ?? unit
}
</script>
