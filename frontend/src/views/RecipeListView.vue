<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { RecipeCreate } from '@/api/types'
import RecipeForm from '@/components/recipes/RecipeForm.vue'
import RecipeTable from '@/components/recipes/RecipeTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
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
  document.addEventListener('click', closeMore)
})
onUnmounted(() => document.removeEventListener('click', closeMore))

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
const showMore = ref(false)

function closeMore() {
  showMore.value = false
}

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
  <div class="h-full flex flex-col p-4 gap-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold">Рецепты</h1>
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
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
            @click="toggleSelectMode"
          >
            Выбрать
          </button>

          <!-- More actions dropdown -->
          <div class="relative" @click.stop>
            <button
              class="px-3 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50 transition-colors"
              @click="showMore = !showMore"
              title="Дополнительные действия"
            >
              <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
              </svg>
            </button>
            <div
              v-if="showMore"
              class="absolute left-0 top-full mt-1 w-44 bg-white border rounded-lg shadow-lg z-30 py-1"
            >
              <button
                class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
                @click="importOpen = true; showMore = false"
              >
                Импорт
              </button>
              <button
                class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
                @click="exportOpen = true; showMore = false"
              >
                Экспорт
              </button>
              <div v-if="store.items.length > 0" class="border-t my-1" />
              <button
                v-if="store.items.length > 0"
                class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                @click="confirmDeleteAllOpen = true; showMore = false"
              >
                Удалить все
              </button>
            </div>
          </div>

          <button
            class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
            @click="openNew"
          >
            + Новый рецепт
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
