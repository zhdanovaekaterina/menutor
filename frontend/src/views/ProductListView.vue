<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { ProductCreate } from '@/api/types'
import ProductForm from '@/components/products/ProductForm.vue'
import ProductTable from '@/components/products/ProductTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ExportModal from '@/components/ui/ExportModal.vue'
import ImportModal from '@/components/ui/ImportModal.vue'
import SlidePanel from '@/components/ui/SlidePanel.vue'
import { useSelection } from '@/composables/useSelection'
import { useProductStore } from '@/stores/products'
import { useToastStore } from '@/stores/toast'

const store = useProductStore()
const toast = useToastStore()
const selection = useSelection()

const selectedId = ref<number | null>(null)
const confirmDeleteOpen = ref(false)
const formOpen = ref(false)
const exportOpen = ref(false)
const importOpen = ref(false)

onMounted(() => store.load())

const selectedProduct = computed(() =>
  store.items.find((p) => p.id === selectedId.value) ?? null,
)

function onSelect(id: number) {
  selectedId.value = id
  formOpen.value = true
}

function openNew() {
  selectedId.value = null
  formOpen.value = true
}

async function onSave(data: ProductCreate, id: number | null) {
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
  const ids = store.items.map((p) => p.id)
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
      <h1 class="text-xl font-bold">Продукты</h1>
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
        <template v-else>
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
            @click="toggleSelectMode"
          >
            Выбрать
          </button>
          <button
            v-if="store.items.length > 0"
            class="px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50"
            @click="confirmDeleteAllOpen = true"
          >
            Удалить все
          </button>
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
            @click="importOpen = true"
          >
            Импорт
          </button>
          <button
            class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
            @click="exportOpen = true"
          >
            Экспорт
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
            @click="openNew"
          >
            + Новый продукт
          </button>
        </template>
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
