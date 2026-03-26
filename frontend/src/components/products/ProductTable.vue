<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ActiveCategory, Product } from '@/api/types'
import { UNIT_MAP } from '@/utils/units'
import { useSortableTable } from '@/composables/useSortableTable'

const props = defineProps<{
  products: Product[]
  categories: ActiveCategory[]
  selectedId: number | null
  selectMode?: boolean
  selectedIds?: Set<number>
}>()

const emit = defineEmits<{
  select: [id: number]
  toggleSelect: [id: number]
  toggleSelectAll: [ids: number[]]
}>()

const { sortKey, sortAsc, toggleSort, sortIcon } = useSortableTable<'name' | 'category' | 'price'>('name')

const catMap = computed(() => Object.fromEntries(props.categories.map((c) => [c.id, c.name])))

const sorted = computed(() => {
  const list = [...props.products]
  list.sort((a, b) => {
    let cmp = 0
    if (sortKey.value === 'name') cmp = a.name.localeCompare(b.name)
    else if (sortKey.value === 'category')
      cmp = (catMap.value[a.category_id] ?? '').localeCompare(catMap.value[b.category_id] ?? '')
    else cmp = Number(a.price_amount) - Number(b.price_amount)
    return sortAsc.value ? cmp : -cmp
  })
  return list
})

const sortedIds = computed(() => sorted.value.map((p) => p.id))
const allChecked = computed(() =>
  sortedIds.value.length > 0 && sortedIds.value.every((id) => props.selectedIds?.has(id)),
)

function onRowClick(id: number) {
  if (props.selectMode) emit('toggleSelect', id)
  else emit('select', id)
}
</script>

<template>
  <div class="flex-1 overflow-y-auto border rounded-lg">
    <table class="w-full text-sm">
      <thead class="bg-gray-50 sticky top-0">
        <tr>
          <th v-if="selectMode" class="w-10 px-2 py-2">
            <input
              type="checkbox"
              :checked="allChecked"
              class="rounded border-gray-300"
              @change="emit('toggleSelectAll', sortedIds)"
            />
          </th>
          <th class="text-left px-4 py-2 cursor-pointer select-none hover:bg-gray-100" @click="toggleSort('name')">
            Название {{ sortIcon('name') }}
          </th>
          <th class="text-left px-4 py-2 cursor-pointer select-none hover:bg-gray-100" @click="toggleSort('category')">
            Категория {{ sortIcon('category') }}
          </th>
          <th class="hidden sm:table-cell px-4 py-2 text-center">Ед. рец.</th>
          <th class="hidden sm:table-cell px-4 py-2 text-center">Ед. пок.</th>
          <th class="text-right px-4 py-2 cursor-pointer select-none hover:bg-gray-100 w-28" @click="toggleSort('price')">
            Цена {{ sortIcon('price') }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y">
        <tr
          v-for="p in sorted"
          :key="p.id"
          :class="[
            selectMode && selectedIds?.has(p.id) ? 'bg-blue-50' :
            !selectMode && p.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50',
          ]"
          class="cursor-pointer"
          @click="onRowClick(p.id)"
        >
          <td v-if="selectMode" class="text-center px-2" @click.stop>
            <input
              type="checkbox"
              :checked="selectedIds?.has(p.id)"
              class="rounded border-gray-300"
              @change="emit('toggleSelect', p.id)"
            />
          </td>
          <td class="px-4 py-2">{{ p.name }}</td>
          <td class="px-4 py-2 text-gray-600">{{ catMap[p.category_id] ?? '—' }}</td>
          <td class="hidden sm:table-cell px-4 py-2 text-center text-gray-500">{{ UNIT_MAP[p.recipe_unit] ?? p.recipe_unit }}</td>
          <td class="hidden sm:table-cell px-4 py-2 text-center text-gray-500">{{ UNIT_MAP[p.purchase_unit] ?? p.purchase_unit }}</td>
          <td class="px-4 py-2 text-right tabular-nums">{{ Number(p.price_amount).toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
