<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { RecipeCreate } from '@/api/types'
import RecipeForm from '@/components/recipes/RecipeForm.vue'
import RecipeTable from '@/components/recipes/RecipeTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
import MoreActionsDropdown from '@/components/ui/MoreActionsDropdown.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useSelection } from '@/composables/useSelection'
import { useProductStore } from '@/stores/products'
import { useRecipeStore } from '@/stores/recipes'
import { useToastStore } from '@/stores/toast'

const store = useRecipeStore()
const productStore = useProductStore()
const toast = useToastStore()
const selection = useSelection()

const selectedId = ref<number | null>(null)
const confirmDeleteOpen = ref(false)
const formOpen = ref(false)
const exportOpen = ref(false)
const importOpen = ref(false)

onMounted(async () => {
  await Promise.all([store.load(), productStore.load()])
})

const selectedRecipe = computed(() =>
  store.items.find((r) => r.id === selectedId.value) ?? null,
)

function onSelect(id: number) {
  selectedId.value = id
  formOpen.value = true
}

function openNew() {
  selectedId.value = null
  formOpen.value = true
}

async function onSave(data: RecipeCreate, id: number | null) {
  try {
    if (id) {
      await store.update(id, data)
    } else {
      const created = await store.create(data)
      selectedId.value = created.id
    }
    formOpen.value = false
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка сохранения', 'error')
  }
}

function onRemove(id: number) {
  selectedId.value = id
  confirmDeleteOpen.value = true
}

async function onConfirmDelete() {
  confirmDeleteOpen.value = false
  if (!selectedId.value) return
  try {
    await store.remove(selectedId.value)
    selectedId.value = null
    formOpen.value = false
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
  }
}

function onClear() {
  selectedId.value = null
  formOpen.value = false
}

const confirmBatchDeleteOpen = ref(false)
const confirmDeleteAllOpen = ref(false)

function toggleSelectMode() {
  if (selection.active.value) selection.exit()
  else { selection.enter(); formOpen.value = false }
}

async function onConfirmBatchDelete() {
  confirmBatchDeleteOpen.value = false
  const ids = [...selection.selected.value]
  try {
    await store.removeMany(ids)
    selection.clear()
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
  }
}

async function onConfirmDeleteAll() {
  confirmDeleteAllOpen.value = false
  const ids = store.items.map((r) => r.id)
  try {
    await store.removeMany(ids)
    selection.exit()
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка удаления', 'error')
  }
}
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
            :show-delete-all="store.items.length > 0"
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

    <div class="flex-1 min-h-0">
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
    </div>

    <SlidePanel
      :open="formOpen && !selection.active.value"
      :title="selectedRecipe ? 'Редактировать рецепт' : 'Новый рецепт'"
      @close="onClear"
    >
      <RecipeForm
        :recipe="selectedRecipe"
        :categories="store.categories"
        :products="productStore.items"
        @save="onSave"
        @remove="onRemove"
        @clear="onClear"
      />
    </SlidePanel>

    <ConfirmDialog
      :open="confirmDeleteOpen"
      :message="`Удалить рецепт «${selectedRecipe?.name ?? ''}»?`"
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmDeleteOpen = false"
    />

    <ConfirmDialog
      :open="confirmBatchDeleteOpen"
      :message="`Удалить выбранные рецепты (${selection.count.value})?`"
      danger
      @confirm="onConfirmBatchDelete"
      @cancel="confirmBatchDeleteOpen = false"
    />

    <ConfirmDialog
      :open="confirmDeleteAllOpen"
      :message="`Удалить все рецепты (${store.items.length})?`"
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
