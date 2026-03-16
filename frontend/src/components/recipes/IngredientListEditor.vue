<script setup lang="ts">
import type { Product } from '@/api/types'

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', pcs: 'шт', box: 'кор', pack: 'уп',
}

const NEW_PRODUCT = -1

const props = defineProps<{
  products: Product[]
}>()

const emit = defineEmits<{
  'create-product': [index: number]
}>()

const ingredients = defineModel<{ product_id: number | null; quantity_amount: number; quantity_unit: string }[]>({
  required: true,
})

function productUnit(productId: number | null) {
  if (productId == null) return ''
  const p = props.products.find((pr) => pr.id === productId)
  return p ? (UNIT_MAP[p.recipe_unit] ?? p.recipe_unit) : ''
}

function onProductChange(ing: { product_id: number | null; quantity_amount: number; quantity_unit: string }, index: number) {
  if (ing.product_id === NEW_PRODUCT) {
    ing.product_id = null
    emit('create-product', index)
    return
  }
  ing.quantity_unit = props.products.find((p) => p.id === ing.product_id)?.recipe_unit ?? 'g'
}

function add() {
  ingredients.value.push({ product_id: null, quantity_amount: 100, quantity_unit: 'g' })
}

function removeLast() {
  ingredients.value.pop()
}
</script>

<template>
  <details open>
    <summary class="bg-slate-200 px-3 py-2 rounded font-medium text-sm cursor-pointer select-none hover:bg-slate-300">
      Ингредиенты
    </summary>
    <div class="pt-2 space-y-2">
      <div v-for="(ing, i) in ingredients" :key="i" class="flex gap-2 items-center">
        <select v-model="ing.product_id"
          class="flex-1 border border-gray-300 rounded px-2 py-1 text-xs"
          @change="onProductChange(ing, i)">
          <option :value="null">Продукт...</option>
          <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          <option disabled>───────────</option>
          <option :value="NEW_PRODUCT">+ Создать новый продукт...</option>
        </select>
        <input v-model.number="ing.quantity_amount" type="number" min="0.01" step="0.01"
          class="w-20 border border-gray-300 rounded px-2 py-1 text-xs" />
        <span class="text-xs text-gray-500 w-8">{{ productUnit(ing.product_id) }}</span>
      </div>
      <div class="flex gap-2">
        <button class="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50" @click="add">+ Добавить</button>
        <button class="px-3 py-1 text-xs rounded border border-gray-300 text-red-600 hover:bg-red-50" @click="removeLast">− Удалить</button>
      </div>
    </div>
  </details>
</template>
