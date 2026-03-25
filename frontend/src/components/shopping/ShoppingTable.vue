<script setup lang="ts">
import { computed } from 'vue'
import type { SavedShoppingListItem } from '@/api/types'
import { formatUnit } from '@/utils/units'

const props = defineProps<{
  itemsByCategory: Record<string, SavedShoppingListItem[]>
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

function fmtQty(item: SavedShoppingListItem) {
  if (!item.recipe_quantity) return '—'
  return `${Number(item.recipe_quantity.amount.toFixed(2))} ${formatUnit(item.recipe_quantity.unit)}`
}

function fmtBuyQty(item: SavedShoppingListItem) {
  const q = item.buy_quantity
  const amount = q.unit === 'kg' ? Number(q.amount.toFixed(2)) : q.amount
  return `${amount} ${formatUnit(q.unit)}`
}

const allProductIds = computed(() => {
  const ids: number[] = []
  for (const items of Object.values(props.itemsByCategory)) {
    for (const item of items) {
      if (item.product_id !== null) ids.push(item.product_id)
    }
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
        <th class="px-4 py-2 text-right">Кол-во по рецепту</th>
        <th class="px-4 py-2 text-right">Купить</th>
        <th class="px-4 py-2 text-right">Сумма, руб.</th>
      </tr>
    </thead>
    <tbody>
      <template v-for="(items, category) in itemsByCategory" :key="category">
        <tr :class="category === 'Куплено' ? 'bg-slate-100' : 'bg-slate-200'">
          <td
            :colspan="selectMode ? 6 : 5"
            :class="category === 'Куплено' ? 'text-slate-400' : 'text-slate-700'"
            class="px-4 py-2 font-semibold text-sm"
          >
            <span v-if="category === 'Куплено'" class="mr-1.5">&#10003;</span>{{ category }}
          </td>
        </tr>
        <tr
          v-for="item in items"
          :key="item.product_id ?? item.id"
          :class="[
            selectMode && item.product_id !== null && selectedIds?.has(item.product_id) ? 'bg-blue-50' :
            !selectMode && item.product_id === selectedId ? 'bg-blue-50' :
            item.purchased ? 'bg-green-50/50' : '',
          ]"
          class="hover:bg-gray-50 border-b cursor-pointer"
          @click="item.product_id !== null && (selectMode ? emit('toggleSelect', item.product_id) : emit('select', item.product_id))"
        >
          <td v-if="selectMode" class="text-center px-2" @click.stop>
            <input
              v-if="item.product_id !== null"
              type="checkbox"
              :checked="selectedIds?.has(item.product_id)"
              class="rounded border-gray-300"
              @change="emit('toggleSelect', item.product_id!)"
            />
          </td>
          <td v-else class="text-center px-2" @click.stop>
            <label class="flex items-center justify-center w-10 h-10 cursor-pointer mx-auto">
              <input
                type="checkbox"
                :checked="item.purchased"
                class="rounded border-gray-300 w-5 h-5"
                @change="item.product_id !== null && emit('toggle', item.product_id)"
              />
            </label>
          </td>
          <td
            :class="!selectMode && item.purchased ? 'line-through text-gray-400' : ''"
            class="px-4 py-2"
          >
            {{ item.product_name }}
          </td>
          <td
            :class="!selectMode && item.purchased ? 'text-gray-400' : ''"
            class="px-4 py-2 text-right"
          >
            {{ fmtQty(item) }}
          </td>
          <td
            :class="!selectMode && item.purchased ? 'text-gray-400' : !selectMode ? 'cursor-pointer hover:text-blue-600' : ''"
            class="px-4 py-2 text-right tabular-nums font-medium"
            @click="!selectMode && !item.purchased && item.product_id !== null && emit('editQuantity', item.product_id)"
          >
            {{ fmtBuyQty(item) }}
            <span
              v-if="item.buy_quantity_overridden"
              class="ml-1 text-orange-400 text-xs font-normal"
              title="Изменено вручную"
            >✎</span>
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
