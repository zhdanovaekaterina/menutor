<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { RecipeCreate } from '@/api/types'
import RecipeForm from '@/components/recipes/RecipeForm.vue'
import RecipeTable from '@/components/recipes/RecipeTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
import MoreActionsDropdown from '@/components/ui/MoreActionsDropdown.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useCrudView } from '@/composables/useCrudView'
import { useProductStore } from '@/stores/products'
import { useRecipeStore } from '@/stores/recipes'
import { fetchRecipeDependents } from '@/api/client'
import { useToastStore } from '@/stores/toast'

const store = useRecipeStore()
const productStore = useProductStore()
const toast = useToastStore()

const {
  selection,
  selectedId,
  selectedItem: selectedRecipe,
  confirmDeleteOpen,
  formOpen,
  exportOpen,
  importOpen,
  confirmBatchDeleteOpen,
  confirmDeleteAllOpen,
  onSelect: baseOnSelect,
  openNew,
  onSave,
  onClear: baseClear,
  toggleSelectMode,
  onConfirmBatchDelete,
  onConfirmDeleteAll,
} = useCrudView<(typeof store.items)[number], RecipeCreate>(store)

// Recipe-specific: sub-recipe navigation
const recipeStack = ref<number[]>([])
const dependentRecipes = ref<{ id: number; name: string }[]>([])

const parentRecipeName = computed(() => {
  if (recipeStack.value.length === 0) return undefined
  const parentId = recipeStack.value[recipeStack.value.length - 1]
  return store.allItems.find((r) => r.id === parentId)?.name
})

const ancestorIds = computed(() => {
  if (selectedId.value == null) return new Set<number>()
  return new Set([selectedId.value])
})

function onSelect(id: number) {
  recipeStack.value = []
  baseOnSelect(id)
}

async function onRemove(id: number) {
  dependentRecipes.value = []
  try {
    const deps = await fetchRecipeDependents(id)
    dependentRecipes.value = deps
  } catch { /* proceed without info */ }
  selectedId.value = id
  confirmDeleteOpen.value = true
}

async function onConfirmDelete() {
  confirmDeleteOpen.value = false
  if (!selectedId.value) return
  try {
    await store.remove(selectedId.value)
    selectedId.value = null
    recipeStack.value = []
    formOpen.value = false
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
  }
}

function onClear() {
  recipeStack.value = []
  baseClear()
}

function onNavigateToSubRecipe(subRecipeId: number) {
  if (selectedId.value != null) {
    recipeStack.value.push(selectedId.value)
  }
  selectedId.value = subRecipeId
}

function onNavigateBack() {
  const parentId = recipeStack.value.pop()
  if (parentId != null) {
    selectedId.value = parentId
  }
}

const search = ref('')
const categoryId = ref<number | null>(null)

let searchTimer: ReturnType<typeof setTimeout>
function onSearchInput(value: string) {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    store.setFilters(value, categoryId.value)
  }, 300)
}

function onCategoryChange() {
  store.setFilters(search.value, categoryId.value)
}

onMounted(async () => {
  await Promise.all([store.load(), productStore.load()])
})
</script>

<template>
  <div class="h-full flex flex-col p-3 sm:p-4 lg:p-6 gap-3 sm:gap-4">
    <div class="flex items-center justify-between flex-wrap gap-2">
      <h1 class="text-lg sm:text-xl font-bold">Рецепты</h1>
      <div class="flex items-center gap-2">
        <template v-if="selection.active.value">
          <span class="text-sm text-gray-500">Выбрано: {{ selection.count.value }}</span>
          <button
            v-if="selection.count.value > 0"
            class="px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50"
            @click="confirmBatchDeleteOpen = true"
          >
            Удалить выбранные
          </button>
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
            @click="toggleSelectMode"
          >
            Отменить
          </button>
        </template>
        <div v-else class="flex items-center gap-2">
          <button
            class="px-3 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors hidden sm:inline-flex"
            @click="toggleSelectMode"
          >
            Выбрать
          </button>

          <!-- More actions dropdown -->
          <MoreActionsDropdown
            :show-delete-all="store.total > 0"
            @select-mode="toggleSelectMode"
            @import="importOpen = true"
            @export="exportOpen = true"
            @delete-all="confirmDeleteAllOpen = true"
          />

          <button
            class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
            @click="openNew"
          >
            <span class="hidden sm:inline">+ Новый рецепт</span>
            <span class="sm:hidden">+ Новый</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Search and filter controls -->
    <div class="flex flex-col sm:flex-row gap-2">
      <SearchInput v-model="search" class="flex-1" @update:model-value="onSearchInput" />
      <select
        v-model="categoryId"
        class="border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        @change="onCategoryChange"
      >
        <option :value="null">Все категории</option>
        <option v-for="c in store.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <div class="flex-1 min-h-0 flex flex-col gap-2">
      <RecipeTable
        :recipes="store.items"
        :categories="store.categories"
        :selected-id="selectedId"
        :select-mode="selection.active.value"
        :selected-ids="selection.selected.value"
        @select="onSelect"
        @toggle-select="selection.toggle"
        @toggle-select-all="selection.toggleAll"
      />

      <!-- Pagination controls -->
      <div
        v-if="store.totalPages > 1"
        class="flex items-center justify-between gap-2 py-1 text-sm"
      >
        <span class="text-gray-500">
          {{ store.items.length > 0 ? (store.page - 1) * store.pageSize + 1 : 0 }}–{{ Math.min(store.page * store.pageSize, store.total) }} из {{ store.total }}
        </span>
        <div class="flex items-center gap-1">
          <button
            :disabled="store.page <= 1"
            class="px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            @click="store.setPage(store.page - 1)"
          >
            ←
          </button>
          <span class="px-2">{{ store.page }} / {{ store.totalPages }}</span>
          <button
            :disabled="store.page >= store.totalPages"
            class="px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            @click="store.setPage(store.page + 1)"
          >
            →
          </button>
        </div>
      </div>
    </div>

    <SlidePanel
      :open="formOpen && !selection.active.value"
      :title="selectedRecipe ? 'Редактировать рецепт' : 'Новый рецепт'"
      @close="onClear"
    >
      <RecipeForm
        :recipe="selectedRecipe"
        :categories="store.categories"
        :products="productStore.allItems"
        :recipes="store.allItems"
        :parent-recipe-name="parentRecipeName"
        :ancestor-ids="ancestorIds"
        @save="onSave"
        @remove="onRemove"
        @clear="onClear"
        @navigate-to-recipe="onNavigateToSubRecipe"
        @navigate-back="onNavigateBack"
      />
    </SlidePanel>

    <ConfirmDialog
      :open="confirmDeleteOpen"
      :message="`Удалить рецепт «${selectedRecipe?.name ?? ''}»?`"
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmDeleteOpen = false"
    >
      <template v-if="dependentRecipes.length > 0">
        <p class="mt-2 text-sm text-orange-600">
          Этот рецепт используется в: {{ dependentRecipes.map((d) => d.name).join(', ') }}.
          После удаления он будет убран из этих рецептов.
        </p>
      </template>
    </ConfirmDialog>

    <ConfirmDialog
      :open="confirmBatchDeleteOpen"
      :message="`Удалить выбранные рецепты (${selection.count.value})?`"
      danger
      @confirm="onConfirmBatchDelete"
      @cancel="confirmBatchDeleteOpen = false"
    />

    <ConfirmDialog
      :open="confirmDeleteAllOpen"
      :message="`Удалить все рецепты (${store.total})?`"
      danger
      @confirm="onConfirmDeleteAll"
      @cancel="confirmDeleteAllOpen = false"
    />

    <ExportModal
      :open="exportOpen"
      entity-type="recipes"
      :formats="[{ value: 'csv', label: 'CSV' }, { value: 'json', label: 'JSON' }]"
      @close="exportOpen = false"
    />
    <ImportModal
      :open="importOpen"
      entity-type="recipes"
      :allowed-extensions="['csv', 'json']"
      @close="importOpen = false"
      @imported="store.load()"
    />
  </div>
</template>
