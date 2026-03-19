<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Product } from '@/api/types'

const props = defineProps<{
  products: Product[]
  existingIds: number[]
}>()

const emit = defineEmits<{
  add: [productId: number, quantity: number]
}>()

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', pcs: 'шт', box: 'кор', pack: 'уп', tsp: 'ч.л.', tbsp: 'ст.л.',
}

const selectedId = ref<number | null>(null)
const quantity = ref(1)

const selectedProduct = computed(() =>
  props.products.find((p) => p.id === selectedId.value),
)

const unitLabel = computed(() => {
  const u = selectedProduct.value?.purchase_unit
  return u ? (UNIT_MAP[u] ?? u) : ''
})

watch(selectedId, () => { quantity.value = 1 })

function onAdd() {
  if (selectedId.value == null) return
  if (props.existingIds.includes(selectedId.value)) return
  emit('add', selectedId.value, quantity.value)
  selectedId.value = null
  quantity.value = 1
}
</script>

<template>
  <div class="border rounded-lg p-3">
    <h4 class="font-medium text-sm mb-2">Добавить продукт</h4>
    <div class="flex gap-2 items-center">
      <select
        v-model="selectedId"
        class="flex-1 min-w-0 border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
      >
        <option :value="null">Выберите продукт...</option>
        <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <input
        v-model.number="quantity"
        type="number"
        min="0.01"
        step="0.01"
        class="w-20 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
      />
      <span class="text-sm text-gray-500 shrink-0">{{ unitLabel }}</span>
      <button
        :disabled="!selectedId"
        class="shrink-0 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
        @click="onAdd"
      >
        Добавить
      </button>
    </div>
  </div>
</template>
