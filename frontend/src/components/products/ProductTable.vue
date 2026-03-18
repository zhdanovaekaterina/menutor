<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ActiveCategory, Product } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', tsp: 'ч.л.', tbsp: 'ст.л.', pcs: 'шт', box: 'кор', pack: 'уп',
}

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

const search = ref('')
const categoryFilter = ref<number | null>(null)
const sortKey = ref<'name' | 'category' | 'price'>('name')
const sortAsc = ref(true)

const catMap = computed(() => Object.fromEntries(props.categories.map((c) => [c.id, c.name])))

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  let list = props.products.filter((p) => {
    if (categoryFilter.value !== null && p.category_id !== categoryFilter.value) return false
    if (q && !p.name.toLowerCase().includes(q)) return false
    return true
  })
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

const filteredIds = computed(() => filtered.value.map((p) => p.id))
const allChecked = computed(() =>
  filteredIds.value.length > 0 && filteredIds.value.every((id) => props.selectedIds?.has(id)),
)

function toggleSort(key: typeof sortKey.value) {
  if (sortKey.value === key) sortAsc.value = !sortAsc.value
  else { sortKey.value = key; sortAsc.value = true }
}

function sortIcon(key: typeof sortKey.value) {
  if (sortKey.value !== key) return '\u2195'
  return sortAsc.value ? '\u2191' : '\u2193'
}

function onRowClick(id: number) {
  if (props.selectMode) emit('toggleSelect', id)
  else emit('select', id)
}
</script>

<template>
  <div class="flex flex-col gap-3 h-full">
    <div class="flex flex-col sm:flex-row gap-2">
      <SearchInput v-model="search" class="flex-1" />
      <select
        v-model="categoryFilter"
        class="border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      >
        <option :value="null">Все категории</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>
    <div class="flex-1 overflow-y-auto border rounded-lg">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th v-if="selectMode" class="w-10 px-2 py-2">
              <input
                type="checkbox"
                :checked="allChecked"
                class="rounded border-gray-300"
                @change="emit('toggleSelectAll', filteredIds)"
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
            v-for="p in filtered"
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
  </div>
</template>
