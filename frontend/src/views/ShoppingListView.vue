<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ShoppingListItem } from '@/api/types'
import AddProductForm from '@/components/shopping/AddProductForm.vue'
import ShoppingSummary from '@/components/shopping/ShoppingSummary.vue'
import ShoppingTable from '@/components/shopping/ShoppingTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import InputDialog from '@/components/ui/InputDialog.vue'
import { downloadBlob } from '@/composables/useFileDownload'
import { useSelection } from '@/composables/useSelection'
import { useProductStore } from '@/stores/products'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useToastStore } from '@/stores/toast'
import { formatUnit } from '@/utils/units'

const store = useShoppingListStore()
const productStore = useProductStore()
const toast = useToastStore()
const selection = useSelection()

const selectedProductId = ref<number | null>(null)
const confirmRemoveOpen = ref(false)
const editProductId = ref<number | null>(null)
const editQtyValue = ref('')
const mobileSidebarOpen = ref(false)

const existingIds = computed(() => store.items.map((i) => i.product_id))

function onToggle(productId: number) {
  store.togglePurchased(productId)
}

function onEditQuantity(productId: number) {
  const item = store.items.find((i) => i.product_id === productId)
  if (!item) return
  editProductId.value = productId
  editQtyValue.value = String(item.buy_quantity.amount)
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

function fmtRound2(n: number) { return String(Number(n.toFixed(2))) }
function fmtBuyAmt(amount: number, unit: string) { return unit === 'kg' ? fmtRound2(amount) : String(amount) }

function buildTextExport(): string {
  const lines: string[] = ['Список покупок', '']
  for (const [category, items] of Object.entries(store.itemsByCategory).sort()) {
    lines.push(`${category}:`)
    for (const item of items) {
      const rq = item.recipe_quantity
      const bq = item.buy_quantity
      const recipeStr = rq ? `${fmtRound2(rq.amount)} ${formatUnit(rq.unit)}` : '-'
      const buyStr = `${fmtBuyAmt(bq.amount, bq.unit)} ${formatUnit(bq.unit)}`
      lines.push(`• ${item.product_name} — купить: ${buyStr} (рецепт: ${recipeStr}) — ${Number(item.cost.amount).toFixed(2)} руб`)
    }
    lines.push('')
  }
  lines.push(`Итого: ${store.totalCost.amount} руб`)
  return lines.join('\n')
}

function buildCsvExport(): string {
  const esc = (v: string) => `"${v.replace(/"/g, '""')}"`
  const rows: string[][] = [
    ['category', 'name', 'recipe_quantity', 'recipe_unit', 'buy_quantity', 'buy_unit', 'cost', 'purchased'],
  ]
  for (const item of store.items) {
    const rq = item.recipe_quantity
    const bq = item.buy_quantity
    rows.push([
      item.category, item.product_name,
      rq ? fmtRound2(rq.amount) : '-', rq ? rq.unit : '',
      fmtBuyAmt(bq.amount, bq.unit), bq.unit,
      Number(item.cost.amount).toFixed(2),
      String(item.purchased),
    ])
  }
  return rows.map((r) => r.map(esc).join(',')).join('\n')
}

function onExportText() {
  if (!store.data) { toast.show('Список покупок пуст', 'info'); return }
  downloadBlob(new Blob([buildTextExport()], { type: 'text/plain;charset=utf-8' }), 'shopping_list.txt')
}

function onExportCsv() {
  if (!store.data) { toast.show('Список покупок пуст', 'info'); return }
  downloadBlob(new Blob([buildCsvExport()], { type: 'text/csv;charset=utf-8' }), 'shopping_list.csv')
}

function onAddProduct(productId: number, quantity: number) {
  const product = productStore.items.find((p) => p.id === productId)
  if (!product) return
  const item: ShoppingListItem = {
    product_id: product.id,
    product_name: product.name,
    category: '',
    quantity: { amount: quantity, unit: product.purchase_unit },
    buy_quantity: { amount: product.purchase_unit === 'kg' ? quantity : Math.ceil(quantity), unit: product.purchase_unit },
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
  <div class="h-full flex flex-col p-3 sm:p-4 lg:p-6 pb-28 sm:pb-4 lg:pb-6 gap-3 sm:gap-4">
    <div class="flex items-center justify-between">
      <h1 class="text-lg sm:text-xl font-bold">Список покупок</h1>
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

    <div v-else class="flex-1 flex flex-col lg:flex-row gap-4 min-h-0">
      <!-- Table (full width on mobile) -->
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

      <!-- Sidebar: hidden on mobile, shown on desktop -->
      <div class="w-64 xl:w-72 shrink-0 hidden lg:flex flex-col gap-4">
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

    <!-- Mobile: Floating summary bar + bottom sheet -->
    <template v-if="store.data">
      <!-- Compact summary bar (sits above the bottom nav) -->
      <div
        class="lg:hidden fixed bottom-[56px] inset-x-0 bg-white border-t shadow-lg z-30 px-4 py-3 flex items-center justify-between"
        style="padding-bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px))"
      >
        <div class="flex items-center gap-4">
          <span class="text-base font-bold">{{ Number(store.totalCost.amount).toFixed(0) }} р.</span>
          <span class="text-sm text-gray-500">{{ store.purchasedCount }}/{{ store.items.length }}</span>
          <div class="w-24 bg-gray-200 rounded-full h-2.5">
            <div class="bg-green-500 h-2.5 rounded-full" :style="{ width: store.progressPercent + '%' }" />
          </div>
        </div>
        <button
          class="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
          @click="mobileSidebarOpen = true"
        >
          <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" />
          </svg>
        </button>
      </div>

      <!-- Bottom sheet (Teleport to body) -->
      <Teleport to="body">
        <Transition name="fade">
          <div
            v-if="mobileSidebarOpen"
            class="fixed inset-0 bg-black/40 z-40 lg:hidden"
            @click="mobileSidebarOpen = false"
          />
        </Transition>
        <Transition name="slide-up">
          <div
            v-if="mobileSidebarOpen"
            class="fixed bottom-0 inset-x-0 bg-white z-50 rounded-t-2xl shadow-xl max-h-[75vh] flex flex-col lg:hidden"
          >
            <!-- Handle bar -->
            <div class="flex justify-center pt-3 pb-1">
              <div class="w-10 h-1 bg-gray-300 rounded-full" />
            </div>
            <div class="flex-1 overflow-y-auto px-4 pb-6 space-y-4">
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
        </Transition>
      </Teleport>
    </template>
  </div>
</template>

