<script setup lang="ts">
import { computed } from 'vue'
import type { ShoppingListItem } from '@/api/types'

const props = defineProps<{
  itemsByCategory: Record<string, ShoppingListItem[]>
  selectMode?: boolean
  selectedIds?: Set<number>
  selectedId?: number | null
}>()

const emit = defineEmits<{
  toggle: [productId: number]
  editQuantity: [productId: number]
  toggleSelect: [productId: number]
  toggleSelectAll: [productIds: number[]]
  select: [productId: number]
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

const allProductIds = computed(() => {
  const ids: number[] = []
  for (const items of Object.values(props.itemsByCategory)) {
    for (const item of items) ids.push(item.product_id)
  }
  return ids
})

const allChecked = computed(() =>
  allProductIds.value.length > 0 && allProductIds.value.every((id) => props.selectedIds?.has(id)),
)
</script>

<template>
  <table class="w-full text-sm">
    <thead class="sticky top-0 bg-white border-b">
      <tr class="text-left text-xs text-gray-500">
        <th v-if="selectMode" class="w-10 px-2 py-2">
          <input
            type="checkbox"
            :checked="allChecked"
            class="rounded border-gray-300"
            @change="emit('toggleSelectAll', allProductIds)"
          />
        </th>
        <th v-else class="w-8 px-2 py-2"></th>
        <th class="px-4 py-2">Продукт</th>
        <th class="px-4 py-2 text-right">Количество</th>
        <th class="px-4 py-2 text-right">Сумма, руб.</th>
      </tr>
    </thead>
    <tbody>
      <template v-for="(items, category) in itemsByCategory" :key="category">
        <tr class="bg-slate-200">
          <td :colspan="selectMode ? 5 : 4" class="px-4 py-2 font-semibold text-slate-700 text-sm">
            {{ category }}
          </td>
        </tr>
        <tr
          v-for="item in items"
          :key="item.product_id"
          :class="[
            selectMode && selectedIds?.has(item.product_id) ? 'bg-blue-50' :
            !selectMode && item.product_id === selectedId ? 'bg-blue-50' :
            item.purchased ? 'bg-green-50/50' : '',
          ]"
          class="hover:bg-gray-50 border-b cursor-pointer"
          @click="selectMode ? emit('toggleSelect', item.product_id) : emit('select', item.product_id)"
        >
          <td v-if="selectMode" class="text-center px-2" @click.stop>
            <input
              type="checkbox"
              :checked="selectedIds?.has(item.product_id)"
              class="rounded border-gray-300"
              @change="emit('toggleSelect', item.product_id)"
            />
          </td>
          <td v-else class="text-center px-2">
            <input
              type="checkbox"
              :checked="item.purchased"
              class="rounded border-gray-300"
              @change="emit('toggle', item.product_id)"
            />
          </td>
          <td
            :class="!selectMode && item.purchased ? 'line-through text-gray-400' : ''"
            class="px-4 py-2"
          >
            {{ item.product_name }}
          </td>
          <td
            :class="!selectMode && item.purchased ? 'text-gray-400' : !selectMode ? 'cursor-pointer hover:text-blue-600' : ''"
            class="px-4 py-2 text-right"
            @click="!selectMode && !item.purchased && emit('editQuantity', item.product_id)"
          >
            {{ fmtQty(item) }}
          </td>
          <td
            :class="!selectMode && item.purchased ? 'text-gray-400' : ''"
            class="px-4 py-2 text-right tabular-nums"
          >
            {{ Number(item.cost.amount).toFixed(2) }}
          </td>
        </tr>
      </template>
    </tbody>
  </table>
</template>
