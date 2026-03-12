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
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', pcs: 'шт', box: 'кор', pack: 'уп',
}

const selectedId = ref<number | null>(null)
const quantity = ref(1)

const selectedProduct = computed(() =>
  props.products.find((p) => p.id === selectedId.value),
)

const unitLabel = computed(() => {
  const u = selectedProduct.value?.recipe_unit
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
    <select
      v-model="selectedId"
      class="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm mb-2"
    >
      <option :value="null">Выберите продукт...</option>
      <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
    </select>
    <div class="flex gap-2 items-center mb-2">
      <input
        v-model.number="quantity"
        type="number"
        min="0.01"
        step="0.01"
        class="w-24 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
      />
      <span class="text-sm text-gray-500">{{ unitLabel }}</span>
    </div>
    <button
      :disabled="!selectedId"
      class="w-full px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
      @click="onAdd"
    >
      Добавить в список
    </button>
  </div>
</template>
