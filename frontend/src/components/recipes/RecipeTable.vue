<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ActiveCategory, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const props = defineProps<{
  recipes: Recipe[]
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
const sortKey = ref<'name' | 'category' | 'servings' | 'weight'>('name')
const sortAsc = ref(true)

const catMap = computed(() => Object.fromEntries(props.categories.map((c) => [c.id, c.name])))

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  let list = q
    ? props.recipes.filter((r) => r.name.toLowerCase().includes(q))
    : [...props.recipes]

  list.sort((a, b) => {
    let cmp = 0
    if (sortKey.value === 'name') cmp = a.name.localeCompare(b.name)
    else if (sortKey.value === 'category')
      cmp = (catMap.value[a.category_id] ?? '').localeCompare(catMap.value[b.category_id] ?? '')
    else if (sortKey.value === 'servings') cmp = a.servings - b.servings
    else cmp = a.weight - b.weight
    return sortAsc.value ? cmp : -cmp
  })
  return list
})

const filteredIds = computed(() => filtered.value.map((r) => r.id))
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
    <SearchInput v-model="search" />
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
            <th class="text-left px-4 py-2 cursor-pointer select-none hover:bg-gray-100"
                @click="toggleSort('name')">
              Название {{ sortIcon('name') }}
            </th>
            <th class="text-left px-4 py-2 cursor-pointer select-none hover:bg-gray-100"
                @click="toggleSort('category')">
              Категория {{ sortIcon('category') }}
            </th>
            <th class="text-center px-4 py-2 cursor-pointer select-none hover:bg-gray-100 w-20"
                @click="toggleSort('servings')">
              Порций {{ sortIcon('servings') }}
            </th>
            <th class="text-right px-4 py-2 cursor-pointer select-none hover:bg-gray-100 w-24"
                @click="toggleSort('weight')">
              Вес {{ sortIcon('weight') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr
            v-for="r in filtered"
            :key="r.id"
            :class="[
              selectMode && selectedIds?.has(r.id) ? 'bg-blue-50' :
              !selectMode && r.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50',
            ]"
            class="cursor-pointer"
            @click="onRowClick(r.id)"
          >
            <td v-if="selectMode" class="text-center px-2" @click.stop>
              <input
                type="checkbox"
                :checked="selectedIds?.has(r.id)"
                class="rounded border-gray-300"
                @change="emit('toggleSelect', r.id)"
              />
            </td>
            <td class="px-4 py-2">{{ r.name }}</td>
            <td class="px-4 py-2 text-gray-600">{{ catMap[r.category_id] ?? '—' }}</td>
            <td class="px-4 py-2 text-center">{{ r.servings }}</td>
            <td class="px-4 py-2 text-right">{{ r.weight ? r.weight + ' г' : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
