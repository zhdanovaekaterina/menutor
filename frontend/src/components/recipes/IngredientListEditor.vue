<script setup lang="ts">
import { ref } from 'vue'
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

const expanded = ref(true)

function productUnit(productId: number | null) {
  if (productId == null) return ''
  const p = props.products.find((pr) => pr.id === productId)
  return p ? (UNIT_MAP[p.recipe_unit] ?? p.recipe_unit) : ''
}

function defaultQuantity(unit: string) {
  return unit === 'g' ? 100 : 1
}

function onProductChange(ing: { product_id: number | null; quantity_amount: number; quantity_unit: string }, index: number) {
  if (ing.product_id === NEW_PRODUCT) {
    ing.product_id = null
    emit('create-product', index)
    return
  }
  const unit = props.products.find((p) => p.id === ing.product_id)?.recipe_unit ?? 'g'
  ing.quantity_unit = unit
  ing.quantity_amount = defaultQuantity(unit)
}

function add() {
  ingredients.value.push({ product_id: null, quantity_amount: 100, quantity_unit: 'g' })
}

function remove(index: number) {
  ingredients.value.splice(index, 1)
}
</script>

<template>
  <div>
    <button
      type="button"
      class="flex items-center justify-between w-full bg-slate-100 px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-200 transition-colors"
      @click="expanded = !expanded"
    >
      <span>Ингредиенты</span>
      <svg
        :class="expanded ? 'rotate-180' : ''"
        class="w-4 h-4 transition-transform duration-200"
        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
      </svg>
    </button>
    <div v-show="expanded" class="pt-2 space-y-2">
      <div v-for="(ing, i) in ingredients" :key="i" class="flex items-center gap-2">
        <select
          v-model="ing.product_id"
          class="flex-1 min-w-0 border border-gray-300 rounded px-2 py-1.5 text-xs"
          @change="onProductChange(ing, i)"
        >
          <option :value="null">Продукт...</option>
          <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          <option disabled>---</option>
          <option :value="NEW_PRODUCT">+ Создать новый...</option>
        </select>
        <input
          v-model.number="ing.quantity_amount"
          type="number"
          min="0.01"
          step="0.01"
          class="w-16 shrink-0 border border-gray-300 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
        <span class="text-xs text-gray-500 shrink-0 w-6">{{ productUnit(ing.product_id) }}</span>
        <button
          type="button"
          class="p-1 text-gray-400 hover:text-red-600 shrink-0 transition-colors"
          title="Удалить ингредиент"
          @click="remove(i)"
        >&times;</button>
      </div>
      <div>
        <button class="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50" @click="add">+ Добавить</button>
      </div>
    </div>
  </div>
</template>
