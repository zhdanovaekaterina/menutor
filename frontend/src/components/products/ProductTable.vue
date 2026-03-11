<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ActiveCategory, Product } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const UNIT_MAP: Record<string, string> = {
  g: 'г', kg: 'кг', ml: 'мл', l: 'л', pcs: 'шт', box: 'кор', pack: 'уп',
}

const props = defineProps<{
  products: Product[]
  categories: ActiveCategory[]
  selectedId: number | null
}>()

const emit = defineEmits<{ select: [id: number] }>()

const search = ref('')
const sortKey = ref<'name' | 'category' | 'price'>('name')
const sortAsc = ref(true)

const catMap = computed(() => Object.fromEntries(props.categories.map((c) => [c.id, c.name])))

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  let list = q
    ? props.products.filter((p) => p.name.toLowerCase().includes(q))
    : [...props.products]
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

function toggleSort(key: typeof sortKey.value) {
  if (sortKey.value === key) sortAsc.value = !sortAsc.value
  else { sortKey.value = key; sortAsc.value = true }
}

function sortIcon(key: typeof sortKey.value) {
  if (sortKey.value !== key) return '\u2195'
  return sortAsc.value ? '\u2191' : '\u2193'
}
</script>

<template>
  <div class="flex flex-col gap-3 h-full">
    <SearchInput v-model="search" />
    <div class="flex-1 overflow-y-auto border rounded-lg">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th class="text-left px-4 py-2 cursor-pointer select-none hover:bg-gray-100" @click="toggleSort('name')">
              Название {{ sortIcon('name') }}
            </th>
            <th class="text-left px-4 py-2 cursor-pointer select-none hover:bg-gray-100" @click="toggleSort('category')">
              Категория {{ sortIcon('category') }}
            </th>
            <th class="px-4 py-2 text-center">Ед. рец.</th>
            <th class="px-4 py-2 text-center">Ед. пок.</th>
            <th class="text-right px-4 py-2 cursor-pointer select-none hover:bg-gray-100 w-28" @click="toggleSort('price')">
              Цена {{ sortIcon('price') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr
            v-for="p in filtered"
            :key="p.id"
            :class="p.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50'"
            class="cursor-pointer"
            @click="emit('select', p.id)"
          >
            <td class="px-4 py-2">{{ p.name }}</td>
            <td class="px-4 py-2 text-gray-600">{{ catMap[p.category_id] ?? '—' }}</td>
            <td class="px-4 py-2 text-center text-gray-500">{{ UNIT_MAP[p.recipe_unit] ?? p.recipe_unit }}</td>
            <td class="px-4 py-2 text-center text-gray-500">{{ UNIT_MAP[p.purchase_unit] ?? p.purchase_unit }}</td>
            <td class="px-4 py-2 text-right tabular-nums">{{ Number(p.price_amount).toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
