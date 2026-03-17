<script setup lang="ts">
import { computed, ref } from 'vue'
import { downloadShoppingListCsv, downloadShoppingListText } from '@/api/client'
import type { ShoppingListItem } from '@/api/types'
import AddProductForm from '@/components/shopping/AddProductForm.vue'
import ShoppingSummary from '@/components/shopping/ShoppingSummary.vue'
import ShoppingTable from '@/components/shopping/ShoppingTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import InputDialog from '@/components/ui/InputDialog.vue'
import { downloadBlob } from '@/composables/useFileDownload'
import { useSelection } from '@/composables/useSelection'
import { useMenuStore } from '@/stores/menus'
import { useProductStore } from '@/stores/products'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useToastStore } from '@/stores/toast'

const store = useShoppingListStore()
const productStore = useProductStore()
const menuStore = useMenuStore()
const toast = useToastStore()
const selection = useSelection()

const selectedProductId = ref<number | null>(null)
const confirmRemoveOpen = ref(false)
const editProductId = ref<number | null>(null)
const editQtyValue = ref('')

const existingIds = computed(() => store.items.map((i) => i.product_id))

function onToggle(productId: number) {
  store.togglePurchased(productId)
}

function onEditQuantity(productId: number) {
  const item = store.items.find((i) => i.product_id === productId)
  if (!item) return
  editProductId.value = productId
  editQtyValue.value = String(item.quantity.amount)
}

function onEditConfirm(val: string) {
  if (editProductId.value == null) return
  const num = parseFloat(val)
  if (!isNaN(num) && num > 0) store.updateQuantity(editProductId.value, num)
  editProductId.value = null
}

function onRemove() {
  if (!selectedProductId.value) {
    toast.show('Выберите продукт для удаления', 'info')
    return
  }
  confirmRemoveOpen.value = true
}

function onConfirmRemove() {
  confirmRemoveOpen.value = false
  if (selectedProductId.value) {
    store.removeItem(selectedProductId.value)
    selectedProductId.value = null
  }
}

async function onExportText() {
  if (!menuStore.current) { toast.show('Нет активного меню', 'error'); return }
  try {
    const blob = await downloadShoppingListText(menuStore.current.id)
    downloadBlob(blob, 'shopping_list.txt')
  } catch {
    toast.show('Ошибка экспорта', 'error')
  }
}

async function onExportCsv() {
  if (!menuStore.current) { toast.show('Нет активного меню', 'error'); return }
  try {
    const blob = await downloadShoppingListCsv(menuStore.current.id)
    downloadBlob(blob, 'shopping_list.csv')
  } catch {
    toast.show('Ошибка экспорта', 'error')
  }
}

function onAddProduct(productId: number, quantity: number) {
  const product = productStore.items.find((p) => p.id === productId)
  if (!product) return
  const item: ShoppingListItem = {
    product_id: product.id,
    product_name: product.name,
    category: '',
    quantity: { amount: quantity, unit: product.recipe_unit },
    cost: { amount: '0', currency: 'RUB' },
    purchased: false,
    recipe_quantity: null,
  }
  store.addItem(item)
  toast.show('Продукт добавлен', 'success')
}

const confirmBatchDeleteOpen = ref(false)
const confirmDeleteAllOpen = ref(false)

function toggleSelectMode() {
  if (selection.active.value) selection.exit()
  else selection.enter()
}

function onConfirmBatchDelete() {
  confirmBatchDeleteOpen.value = false
  store.removeMany([...selection.selected.value])
  selection.clear()
  toast.show('Продукты удалены из списка', 'success')
}

function onConfirmDeleteAll() {
  confirmDeleteAllOpen.value = false
  store.removeMany(store.items.map((i) => i.product_id))
  selection.exit()
  toast.show('Список покупок очищен', 'success')
}
</script>

<template>
  <div class="h-full flex flex-col p-4 lg:p-6 gap-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold">Список покупок</h1>
      <div v-if="store.data" class="flex items-center gap-2">
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
            v-if="selectedProductId !== null"
            class="px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50 transition-colors"
            @click="confirmRemoveOpen = true"
          >
            Удалить выбранный
          </button>
          <button
            v-if="store.items.length > 0"
            class="px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm hover:bg-red-50"
            @click="confirmDeleteAllOpen = true"
          >
            Удалить все
          </button>
        </template>
      </div>
    </div>

    <div v-if="!store.data" class="flex-1 flex items-center justify-center text-gray-400">
      Список покупок пуст. Сформируйте его в планировщике меню.
    </div>

    <div v-else class="flex-1 flex gap-4 min-h-0">
      <!-- Table -->
      <div class="flex-1 overflow-y-auto border rounded-lg">
        <ShoppingTable
          :items-by-category="store.itemsByCategory"
          :select-mode="selection.active.value"
          :selected-ids="selection.selected.value"
          :selected-id="selectedProductId"
          @toggle="onToggle"
          @edit-quantity="onEditQuantity"
          @toggle-select="selection.toggle"
          @toggle-select-all="selection.toggleAll"
          @select="(id) => { selectedProductId = selectedProductId === id ? null : id }"
        />
      </div>

      <!-- Sidebar -->
      <div class="w-64 xl:w-72 shrink-0 flex flex-col gap-4">
        <ShoppingSummary
          :total-cost="store.totalCost"
          :item-count="store.items.length"
          :purchased-count="store.purchasedCount"
          :progress-percent="store.progressPercent"
          @export-text="onExportText"
          @export-csv="onExportCsv"
        />
        <AddProductForm
          :products="productStore.items"
          :existing-ids="existingIds"
          @add="onAddProduct"
        />
      </div>
    </div>

    <ConfirmDialog
      :open="confirmRemoveOpen"
      message="Удалить продукт из списка?"
      danger
      @confirm="onConfirmRemove"
      @cancel="confirmRemoveOpen = false"
    />

    <ConfirmDialog
      :open="confirmBatchDeleteOpen"
      :message="`Удалить выбранные продукты (${selection.count.value}) из списка?`"
      danger
      @confirm="onConfirmBatchDelete"
      @cancel="confirmBatchDeleteOpen = false"
    />

    <ConfirmDialog
      :open="confirmDeleteAllOpen"
      :message="`Очистить весь список покупок (${store.items.length})?`"
      danger
      @confirm="onConfirmDeleteAll"
      @cancel="confirmDeleteAllOpen = false"
    />

    <InputDialog
      :open="editProductId != null"
      title="Изменить количество"
      label="Количество"
      :initial-value="editQtyValue"
      input-type="number"
      @confirm="onEditConfirm"
      @cancel="editProductId = null"
    />
  </div>
</template>
