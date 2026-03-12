<script setup lang="ts">
import type { ShoppingListItem } from '@/api/types'

defineProps<{
  itemsByCategory: Record<string, ShoppingListItem[]>
}>()

const emit = defineEmits<{
  toggle: [productId: number]
  editQuantity: [productId: number]
}>()

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', pcs: 'шт', box: 'кор', pack: 'уп',
}

function fmtUnit(u: string) { return UNIT_MAP[u] ?? u }

function fmtQty(item: ShoppingListItem) {
  const main = `${Number(item.quantity.amount.toFixed(2))} ${fmtUnit(item.quantity.unit)}`
  if (item.recipe_quantity && item.recipe_quantity.unit !== item.quantity.unit) {
    return `${main} (${Number(item.recipe_quantity.amount.toFixed(1))} ${fmtUnit(item.recipe_quantity.unit)})`
  }
  return main
}
</script>

<template>
  <table class="w-full text-sm">
    <thead class="sticky top-0 bg-white border-b">
      <tr class="text-left text-xs text-gray-500">
        <th class="w-8 px-2 py-2"></th>
        <th class="px-4 py-2">Продукт</th>
        <th class="px-4 py-2 text-right">Количество</th>
        <th class="px-4 py-2 text-right">Сумма, руб.</th>
      </tr>
    </thead>
    <tbody>
      <template v-for="(items, category) in itemsByCategory" :key="category">
        <tr class="bg-slate-200">
          <td colspan="4" class="px-4 py-2 font-semibold text-slate-700 text-sm">
            {{ category }}
          </td>
        </tr>
        <tr
          v-for="item in items"
          :key="item.product_id"
          :class="item.purchased ? 'bg-green-50/50' : ''"
          class="hover:bg-gray-50 border-b"
        >
          <td class="text-center px-2">
            <input
              type="checkbox"
              :checked="item.purchased"
              class="rounded border-gray-300"
              @change="emit('toggle', item.product_id)"
            />
          </td>
          <td
            :class="item.purchased ? 'line-through text-gray-400' : ''"
            class="px-4 py-2"
          >
            {{ item.product_name }}
          </td>
          <td
            :class="item.purchased ? 'text-gray-400' : 'cursor-pointer hover:text-blue-600'"
            class="px-4 py-2 text-right"
            @click="!item.purchased && emit('editQuantity', item.product_id)"
          >
            {{ fmtQty(item) }}
          </td>
          <td
            :class="item.purchased ? 'text-gray-400' : ''"
            class="px-4 py-2 text-right tabular-nums"
          >
            {{ Number(item.cost.amount).toFixed(2) }}
          </td>
        </tr>
      </template>
    </tbody>
  </table>
</template>
