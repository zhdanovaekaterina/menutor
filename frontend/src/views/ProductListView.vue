<script setup lang="ts">
import { onMounted } from 'vue'
import type { ProductCreate } from '@/api/types'
import ProductForm from '@/components/products/ProductForm.vue'
import ProductTable from '@/components/products/ProductTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
import MoreActionsDropdown from '@/components/ui/MoreActionsDropdown.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useCrudView } from '@/composables/useCrudView'
import { useProductStore } from '@/stores/products'

const store = useProductStore()

const {
  selection,
  selectedId,
  selectedItem: selectedProduct,
  confirmDeleteOpen,
  formOpen,
  exportOpen,
  importOpen,
  confirmBatchDeleteOpen,
  confirmDeleteAllOpen,
  onSelect,
  openNew,
  onSave,
  onRemove,
  onConfirmDelete,
  onClear,
  toggleSelectMode,
  onConfirmBatchDelete,
  onConfirmDeleteAll,
} = useCrudView<(typeof store.items)[number], ProductCreate>(store)

onMounted(() => {
  store.load()
})
</script>

<template>
  <div class="h-full flex flex-col p-3 sm:p-4 lg:p-6 gap-3 sm:gap-4">
    <div class="flex items-center justify-between flex-wrap gap-2">
      <h1 class="text-lg sm:text-xl font-bold">Продукты</h1>
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
            <span class="hidden sm:inline">+ Новый продукт</span>
            <span class="sm:hidden">+ Новый</span>
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 min-h-0">
      <ProductTable
        :products="store.items"
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
      :title="selectedProduct ? 'Редактировать продукт' : 'Новый продукт'"
      @close="onClear"
    >
      <ProductForm
        :product="selectedProduct"
        :categories="store.categories"
        @save="onSave"
        @remove="onRemove"
        @clear="onClear"
      />
    </SlidePanel>

    <ConfirmDialog
      :open="confirmDeleteOpen"
      :message="`Удалить продукт «${selectedProduct?.name ?? ''}»?`"
      danger
      @confirm="onConfirmDelete"
      @cancel="confirmDeleteOpen = false"
    />

    <ConfirmDialog
      :open="confirmBatchDeleteOpen"
      :message="`Удалить выбранные продукты (${selection.count.value})?`"
      danger
      @confirm="onConfirmBatchDelete"
      @cancel="confirmBatchDeleteOpen = false"
    />

    <ConfirmDialog
      :open="confirmDeleteAllOpen"
      :message="`Удалить все продукты (${store.items.length})?`"
      danger
      @confirm="onConfirmDeleteAll"
      @cancel="confirmDeleteAllOpen = false"
    />

    <ExportModal
      :open="exportOpen"
      entity-type="products"
      :formats="[{ value: 'csv', label: 'CSV' }, { value: 'json', label: 'JSON' }]"
      @close="exportOpen = false"
    />
    <ImportModal
      :open="importOpen"
      entity-type="products"
      :allowed-extensions="['csv', 'json']"
      @close="importOpen = false"
      @imported="store.load()"
    />
  </div>
</template>
