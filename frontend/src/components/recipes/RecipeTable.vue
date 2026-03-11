<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ActiveCategory, Recipe } from '@/api/types'
import SearchInput from '@/components/ui/SearchInput.vue'

const props = defineProps<{
  recipes: Recipe[]
  categories: ActiveCategory[]
  selectedId: number | null
}>()

const emit = defineEmits<{ select: [id: number] }>()

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
            :class="r.id === selectedId ? 'bg-blue-50' : 'hover:bg-gray-50'"
            class="cursor-pointer"
            @click="emit('select', r.id)"
          >
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
