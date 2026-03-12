<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ShoppingListItem } from '@/api/types'
import AddProductForm from '@/components/shopping/AddProductForm.vue'
import ShoppingSummary from '@/components/shopping/ShoppingSummary.vue'
import ShoppingTable from '@/components/shopping/ShoppingTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import InputDialog from '@/components/ui/InputDialog.vue'
import { useMenuStore } from '@/stores/menus'
import { useProductStore } from '@/stores/products'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useToastStore } from '@/stores/toast'

const store = useShoppingListStore()
const productStore = useProductStore()
const menuStore = useMenuStore()
const toast = useToastStore()

const selectedProductId = ref<number | null>(null)
const confirmRemoveOpen = ref(false)
const exportTextOpen = ref(false)
const exportedText = ref('')
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
  const text = await store.exportText(menuStore.current.id)
  if (text) {
    exportedText.value = text
    exportTextOpen.value = true
  }
}

function copyToClipboard() {
  navigator.clipboard.writeText(exportedText.value)
  toast.show('Скопировано в буфер', 'success')
}

function onExportCsv() {
  if (!store.data) return
  const lines = ['Продукт;Количество;Единица;Сумма']
  for (const item of store.items) {
    lines.push(`${item.product_name};${item.quantity.amount};${item.quantity.unit};${item.cost.amount}`)
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'shopping_list.csv'
  a.click()
  URL.revokeObjectURL(url)
}

function onAddProduct(productId: number, quantity: number) {
  const product = productStore.products.find((p) => p.id === productId)
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
</script>

<template>
  <div class="h-full flex flex-col p-4 gap-4">
    <h1 class="text-xl font-bold">Список покупок</h1>

    <div v-if="!store.data" class="flex-1 flex items-center justify-center text-gray-400">
      Список покупок пуст. Сформируйте его в планировщике меню.
    </div>

    <div v-else class="flex-1 flex gap-4 min-h-0">
      <!-- Table -->
      <div class="flex-1 overflow-y-auto border rounded-lg">
        <ShoppingTable
          :items-by-category="store.itemsByCategory"
          @toggle="onToggle"
          @edit-quantity="onEditQuantity"
        />
      </div>

      <!-- Sidebar -->
      <div class="w-72 shrink-0 flex flex-col gap-4">
        <ShoppingSummary
          :total-cost="store.totalCost"
          :item-count="store.items.length"
          :purchased-count="store.purchasedCount"
          :progress-percent="store.progressPercent"
          @remove="onRemove"
          @export-text="onExportText"
          @export-csv="onExportCsv"
        />
        <AddProductForm
          :products="productStore.products"
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

    <!-- Export text modal -->
    <Teleport to="body">
      <div v-if="exportTextOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6">
          <h3 class="text-lg font-semibold mb-4">Список покупок</h3>
          <pre class="bg-gray-50 border rounded-lg p-4 text-sm whitespace-pre-wrap max-h-80 overflow-y-auto">{{ exportedText }}</pre>
          <div class="flex justify-end gap-2 mt-4">
            <button class="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-50"
              @click="exportTextOpen = false">Закрыть</button>
            <button class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700"
              @click="copyToClipboard">Копировать</button>
          </div>
        </div>
      </div>
    </Teleport>

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
