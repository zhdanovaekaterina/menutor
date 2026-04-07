<script setup lang="ts">
import { computed } from 'vue'
import type { ActiveCategory, Recipe } from '@/api/types'
import { useSortableTable } from '@/composables/useSortableTable'
import { useRecipeSettingsStore } from '@/stores/recipeSettings'
import CostBadge from './CostBadge.vue'
import PreferenceBadges from './PreferenceBadges.vue'

const recipeSettings = useRecipeSettingsStore()

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

const { sortKey, sortAsc, toggleSort, sortIcon } = useSortableTable<'name' | 'category' | 'servings' | 'cost' | 'weight'>('name')

const catMap = computed(() => Object.fromEntries(props.categories.map((c) => [c.id, c.name])))

const sorted = computed(() => {
  const list = [...props.recipes]
  list.sort((a, b) => {
    let cmp = 0
    if (sortKey.value === 'name') cmp = a.name.localeCompare(b.name)
    else if (sortKey.value === 'category')
      cmp = (catMap.value[a.category_id] ?? '').localeCompare(catMap.value[b.category_id] ?? '')
    else if (sortKey.value === 'servings') cmp = a.servings - b.servings
    else if (sortKey.value === 'cost') {
      const aCost = a.cost_per_portion ?? Infinity
      const bCost = b.cost_per_portion ?? Infinity
      cmp = aCost - bCost
    }
    else cmp = a.weight - b.weight
    return sortAsc.value ? cmp : -cmp
  })
  return list
})

const sortedIds = computed(() => sorted.value.map((r) => r.id))
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
          <th v-if="recipeSettings.showCostColumn" class="hidden sm:table-cell text-right px-4 py-2 cursor-pointer select-none hover:bg-gray-100 w-24"
              @click="toggleSort('cost')">
            Стоимость {{ sortIcon('cost') }}
          </th>
          <th class="hidden sm:table-cell text-right px-4 py-2 cursor-pointer select-none hover:bg-gray-100 w-24"
              @click="toggleSort('weight')">
            Вес {{ sortIcon('weight') }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y">
        <tr
          v-for="r in sorted"
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
          <td class="px-4 py-2">
            <div>{{ r.name }}
            <svg
              v-if="r.ingredients.some((i) => i.sub_recipe_id != null)"
              class="inline-block w-3.5 h-3.5 text-amber-500 ml-1 align-text-bottom"
              title="Содержит вложенные рецепты"
              xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
              stroke-width="2" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
            </svg>
            <!-- Mobile cost badge -->
            <CostBadge
              v-if="recipeSettings.showCostColumn && r.cost_per_portion !== null"
              :cost-per-portion="r.cost_per_portion"
              :cost-is-partial="r.cost_is_partial"
              badge
              class="sm:hidden ml-2"
            />
            </div>
            <PreferenceBadges :recipe-id="r.id" class="mt-1" />
          </td>
          <td class="px-4 py-2 text-gray-600">{{ catMap[r.category_id] ?? '—' }}</td>
          <td class="px-4 py-2 text-center">{{ r.servings }}</td>
          <td v-if="recipeSettings.showCostColumn" class="hidden sm:table-cell px-4 py-2 text-right text-sm">
            <CostBadge
              :cost-per-portion="r.cost_per_portion"
              :cost-is-partial="r.cost_is_partial"
            />
          </td>
          <td class="hidden sm:table-cell px-4 py-2 text-right">{{ r.weight ? r.weight + ' г' : '—' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
