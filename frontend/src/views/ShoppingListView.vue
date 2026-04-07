<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import type { SavedShoppingListItem } from '@/api/types'
import AddProductForm from '@/components/shopping/AddProductForm.vue'
import SavedShoppingLists from '@/components/shopping/SavedShoppingLists.vue'
import ShoppingSummary from '@/components/shopping/ShoppingSummary.vue'
import ShoppingTable from '@/components/shopping/ShoppingTable.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import InputDialog from '@/components/ui/InputDialog.vue'
import IconChevronLeft from '@/components/ui/icons/IconChevronLeft.vue'
import IconChevronRight from '@/components/ui/icons/IconChevronRight.vue'
import IconClose from '@/components/ui/icons/IconClose.vue'
import IconHamburger from '@/components/ui/icons/IconHamburger.vue'
import { downloadShoppingListPdf, downloadShoppingListJson } from '@/api/client'
import { downloadBlob } from '@/composables/useFileDownload'
import { useSelection } from '@/composables/useSelection'
import { useProductStore } from '@/stores/products'
import { useShoppingListStore } from '@/stores/shoppingList'
import { useShoppingListSettingsStore } from '@/stores/shoppingListSettings'
import { useToastStore } from '@/stores/toast'
import { formatUnit } from '@/utils/units'

const route = useRoute()
const store = useShoppingListStore()
const productStore = useProductStore()
const shoppingSettings = useShoppingListSettingsStore()
const toast = useToastStore()
const selection = useSelection()

const PURCHASED_CATEGORY = 'Куплено'

const groupedItems = computed((): Record<string, SavedShoppingListItem[]> => {
  if (shoppingSettings.groupBy === 'category') return store.itemsByCategory
  // Group by supplier
  const grouped: Record<string, SavedShoppingListItem[]> = {}
  const purchased: SavedShoppingListItem[] = []
  for (const item of store.items) {
    if (item.purchased) {
      if (!shoppingSettings.hidePurchased) purchased.push(item)
    } else {
      const product = productStore.allItems.find((p) => p.id === item.product_id)
      const key = product?.supplier?.trim() || 'Без поставщика'
      ;(grouped[key] ??= []).push(item)
    }
  }
  if (purchased.length) grouped[PURCHASED_CATEGORY] = purchased
  return grouped
})

// ---- Sidebar state ----
const sidebarOpen = ref(true)
const mobileSavedListsOpen = ref(false)
// Bottom sheet (export/add product panel) on mobile
const mobileSidebarOpen = ref(false)

const selectedProductId = ref<number | null>(null)
const confirmRemoveOpen = ref(false)
const editProductId = ref<number | null>(null)
const editQtyValue = ref('')
const editPriceProductId = ref<number | null>(null)
const editPriceValue = ref('')

const existingIds = computed(() =>
  store.items.map((i) => i.product_id).filter((id): id is number => id !== null),
)

onMounted(async () => {
  // Determine sidebar visibility based on navigation source
  const fromPlanner = route.query.from === 'planner'
  sidebarOpen.value = !fromPlanner
  store.setSidebarOpen(!fromPlanner)

  await Promise.all([store.loadLists(), productStore.load()])
})

// ---- Sidebar actions ----
async function onSelectList(id: number) {
  await store.loadList(id)
  mobileSavedListsOpen.value = false
}

async function onCreateList() {
  await store.createEmpty()
  mobileSavedListsOpen.value = false
}

// ---- Save ----
const saving = ref(false)

async function onSave() {
  saving.value = true
  try {
    await store.saveChanges()
  } finally {
    saving.value = false
  }
}

// ---- Toggle purchased ----
function onToggle(productId: number) {
  const item = store.items.find((i) => i.product_id === productId)
  if (item) store.togglePurchased(item.id)
}

// ---- Edit quantity ----
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

// ---- Edit price ----
function onEditPrice(productId: number) {
  const item = store.items.find((i) => i.product_id === productId)
  if (!item) return
  const pricePerUnit = item.buy_quantity.amount > 0
    ? Number(item.cost.amount) / item.buy_quantity.amount
    : 0
  editPriceProductId.value = productId
  editPriceValue.value = pricePerUnit.toFixed(2)
}

async function onEditPriceConfirm(val: string) {
  if (editPriceProductId.value == null) return
  const num = parseFloat(val)
  const productId = editPriceProductId.value
  editPriceProductId.value = null
  if (isNaN(num) || num < 0) return
  store.updatePrice(productId, num)
  try {
    await productStore.patchPrice(productId, num)
  } catch {
    toast.show('Ошибка обновления цены продукта', 'error')
  }
}

// ---- Remove ----
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

// ---- Export helpers ----
function fmtRound2(n: number) { return String(Number(n.toFixed(2))) }
function fmtBuyAmt(amount: number, unit: string) { return unit === 'kg' ? fmtRound2(amount) : String(amount) }

function buildTextExport(): string {
  const lines: string[] = ['Список покупок', '']
  for (const [category, items] of Object.entries(groupedItems.value).sort()) {
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

function buildJsonExport(): string {
  const payload = {
    title: 'Список покупок',
    total_cost: store.totalCost,
    items: store.items.map((item) => ({
      category: item.category,
      product_name: item.product_name,
      recipe_quantity: item.recipe_quantity ?? null,
      buy_quantity: item.buy_quantity,
      cost: item.cost,
      purchased: item.purchased,
    })),
  }
  return JSON.stringify(payload, null, 2)
}

function onExportJson() {
  if (!store.data) { toast.show('Список покупок пуст', 'info'); return }
  downloadBlob(new Blob([buildJsonExport()], { type: 'application/json;charset=utf-8' }), 'shopping_list.json')
}

async function onExportPdf() {
  if (!store.data) { toast.show('Список покупок пуст', 'info'); return }
  const sourceMenuId = store.data.source_menu_id
  if (!sourceMenuId) { toast.show('Не удалось определить меню для экспорта', 'error'); return }
  try {
    const blob = await downloadShoppingListPdf(sourceMenuId)
    downloadBlob(blob, 'shopping_list.pdf')
  } catch {
    toast.show('Ошибка экспорта в PDF', 'error')
  }
}

const exportLoading = ref(false)

async function onExport(format: string) {
  if (!store.data) { toast.show('Список покупок пуст', 'info'); return }
  if (format === 'txt') { onExportText(); return }
  if (format === 'csv') { onExportCsv(); return }
  if (format === 'json') {
    const sourceMenuId = store.data?.source_menu_id
    if (sourceMenuId) {
      exportLoading.value = true
      try {
        const blob = await downloadShoppingListJson(sourceMenuId)
        downloadBlob(blob, 'shopping_list.json')
      } catch {
        toast.show('Ошибка экспорта в JSON', 'error')
      } finally {
        exportLoading.value = false
      }
    } else {
      onExportJson()
    }
    return
  }
  if (format === 'pdf') { await onExportPdf(); return }
}

// ---- Add product ----
function onAddProduct(productId: number, quantity: number) {
  const product = productStore.items.find((p) => p.id === productId)
  if (!product) return
  const nextOrder = store.items.length
  const category = productStore.categories.find((c) => c.id === product.category_id)?.name ?? ''
  const buyAmount = product.purchase_unit === 'kg' ? quantity : Math.ceil(quantity)
  const cost = (buyAmount * parseFloat(product.price_amount)).toFixed(2)
  const item: SavedShoppingListItem = {
    id: 0,
    product_id: product.id,
    product_name: product.name,
    category,
    quantity: { amount: quantity, unit: product.purchase_unit },
    buy_quantity: { amount: buyAmount, unit: product.purchase_unit },
    buy_quantity_overridden: false,
    cost: { amount: cost, currency: product.price_currency },
    purchased: false,
    recipe_quantity: null,
    item_order: nextOrder,
  }
  store.addItem(item)
  toast.show('Продукт добавлен', 'success')
}

// ---- Batch select / delete ----
const mobileActionsOpen = ref(false)
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
  store.removeMany(store.items.map((i) => i.product_id).filter((id): id is number => id !== null))
  selection.exit()
  toast.show('Список покупок очищен', 'success')
}
</script>

<template>
  <div class="h-full flex flex-col p-3 sm:p-4 lg:p-6 pb-28 sm:pb-4 lg:pb-6 gap-3 sm:gap-4">

    <!-- Page header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <!-- Mobile: hamburger to open saved lists drawer -->
        <button
          class="lg:hidden p-2 -ml-2 rounded-lg hover:bg-gray-100"
          @click="mobileSavedListsOpen = true"
        >
          <IconHamburger class="w-5 h-5" />
        </button>
        <h1 class="text-lg sm:text-xl font-bold">Список покупок</h1>
      </div>

      <div class="flex items-center gap-2">
        <!-- Save button (always visible when a list is loaded) -->
        <button
          v-if="store.data"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="store.isDirty
            ? (saving ? 'bg-blue-600 text-white opacity-75 cursor-wait shadow-sm' : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm')
            : 'bg-gray-100 text-gray-400 cursor-default'"
          :disabled="saving || !store.isDirty"
          @click="onSave"
        >
          <span v-if="saving" class="flex items-center gap-1.5">
            <svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Сохранение...
          </span>
          <span v-else>Сохранить</span>
        </button>

        <!-- Selection / delete actions -->
        <template v-if="store.data">
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
            <!-- Desktop: all action buttons visible -->
            <div class="hidden lg:flex items-center gap-2">
              <!-- Hide/show purchased toggle -->
              <button
                :title="shoppingSettings.hidePurchased ? 'Показать купленные' : 'Скрыть купленные'"
                :class="shoppingSettings.hidePurchased ? 'border-blue-300 text-blue-600 bg-blue-50 hover:bg-blue-100' : 'border-gray-300 text-gray-600 hover:bg-gray-50'"
                class="p-2 rounded-lg border text-sm transition-colors"
                @click="shoppingSettings.toggleHidePurchased()"
              >
                <svg v-if="shoppingSettings.hidePurchased" class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
                </svg>
                <svg v-else class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                </svg>
              </button>
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
            </div>

            <!-- Mobile: kebab menu -->
            <div class="lg:hidden relative">
              <button
                class="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
                aria-label="Действия"
                @click="mobileActionsOpen = !mobileActionsOpen"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
                </svg>
              </button>
              <div v-if="mobileActionsOpen" class="fixed inset-0 z-40" @click="mobileActionsOpen = false" />
              <div v-if="mobileActionsOpen" class="absolute right-0 top-full mt-1 bg-white border rounded-xl shadow-xl z-50 min-w-[200px] py-1 overflow-hidden">
                <button
                  class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 flex items-center gap-3"
                  :class="shoppingSettings.hidePurchased ? 'text-blue-600' : 'text-gray-700'"
                  @click="shoppingSettings.toggleHidePurchased(); mobileActionsOpen = false"
                >
                  <svg v-if="shoppingSettings.hidePurchased" class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
                  </svg>
                  <svg v-else class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                  </svg>
                  {{ shoppingSettings.hidePurchased ? 'Показать купленные' : 'Скрыть купленные' }}
                </button>
                <div class="border-t mx-3 my-1" />
                <button
                  class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50"
                  @click="toggleSelectMode(); mobileActionsOpen = false"
                >
                  Выбрать
                </button>
                <button
                  v-if="selectedProductId !== null"
                  class="w-full text-left px-4 py-3 text-sm hover:bg-red-50 text-red-600"
                  @click="confirmRemoveOpen = true; mobileActionsOpen = false"
                >
                  Удалить выбранный
                </button>
                <button
                  v-if="store.items.length > 0"
                  class="w-full text-left px-4 py-3 text-sm hover:bg-red-50 text-red-600"
                  @click="confirmDeleteAllOpen = true; mobileActionsOpen = false"
                >
                  Удалить все
                </button>
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Main layout: sidebar + content -->
    <div class="flex-1 flex gap-4 min-h-0">

      <!-- Left sidebar (desktop only, collapsible) -->
      <div
        :class="sidebarOpen ? 'w-64' : 'w-10'"
        class="shrink-0 transition-all duration-200 flex flex-col bg-white overflow-hidden hidden lg:flex border-r"
      >
        <!-- Toggle button -->
        <button
          class="p-2 text-gray-400 hover:text-gray-600 self-end shrink-0"
          :title="sidebarOpen ? 'Свернуть' : 'Развернуть'"
          @click="sidebarOpen = !sidebarOpen"
        >
          <IconChevronLeft v-if="sidebarOpen" class="w-4 h-4" />
          <IconChevronRight v-else class="w-4 h-4" />
        </button>

        <div v-show="sidebarOpen" class="flex-1 min-h-0 overflow-hidden">
          <SavedShoppingLists
            :lists="store.sortedLists"
            :selected-id="store.currentListId"
            @select="onSelectList"
            @create="onCreateList"
          />
        </div>
      </div>

      <!-- Center: main content area -->
      <div class="flex-1 flex flex-col gap-4 min-w-0">

        <!-- Empty state: no list selected -->
        <div
          v-if="!store.data && !store.loading"
          class="flex-1 flex items-center justify-center text-gray-400"
        >
          <div class="text-center">
            <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z" />
            </svg>
            <p class="text-sm">Выберите список из панели слева</p>
            <p class="text-xs text-gray-400 mt-1">или создайте новый</p>
          </div>
        </div>

        <!-- Loading state -->
        <div
          v-else-if="store.loading && !store.data"
          class="flex-1 flex items-center justify-center text-gray-400"
        >
          <svg class="w-6 h-6 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>

        <!-- Shopping content -->
        <div v-else-if="store.data" class="flex-1 flex flex-col lg:flex-row gap-4 min-h-0">
          <!-- Table (full width on mobile) -->
          <div class="flex-1 overflow-y-auto border rounded-lg">
            <ShoppingTable
              :items-by-category="groupedItems"
              :select-mode="selection.active.value"
              :selected-ids="selection.selected.value"
              :selected-id="selectedProductId"
              @toggle="onToggle"
              @edit-quantity="onEditQuantity"
              @edit-price="onEditPrice"
              @toggle-select="selection.toggle"
              @toggle-select-all="selection.toggleAll"
              @select="(id) => { selectedProductId = selectedProductId === id ? null : id }"
            />
          </div>

          <!-- Right sidebar: hidden on mobile, shown on desktop -->
          <div class="w-64 xl:w-72 shrink-0 hidden lg:flex flex-col gap-4">
            <ShoppingSummary
              :total-cost="store.totalCost"
              :item-count="store.items.length"
              :purchased-count="store.purchasedCount"
              :progress-percent="store.progressPercent"
              :export-loading="exportLoading"
              @export="onExport"
            />
            <AddProductForm
              :products="productStore.items"
              :existing-ids="existingIds"
              @add="onAddProduct"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Dialogs -->
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

    <InputDialog
      :open="editPriceProductId != null"
      title="Изменить цену за единицу"
      label="Цена за единицу, руб."
      :initial-value="editPriceValue"
      input-type="number"
      @confirm="onEditPriceConfirm"
      @cancel="editPriceProductId = null"
    />

    <!-- Mobile: Compact summary bar (above bottom nav) -->
    <template v-if="store.data">
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
        <div class="flex items-center gap-2">
          <!-- Save button in mobile bar -->
          <button
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
            :class="store.isDirty ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-100 text-gray-400 cursor-default'"
            :disabled="saving || !store.isDirty"
            @click="onSave"
          >
            Сохранить
          </button>
          <button
            class="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
            @click="mobileSidebarOpen = true"
          >
            <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Mobile bottom sheet (export/add product) -->
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
            <div class="flex justify-center pt-3 pb-1">
              <div class="w-10 h-1 bg-gray-300 rounded-full" />
            </div>
            <div class="flex-1 overflow-y-auto px-4 pb-6 space-y-4">
              <ShoppingSummary
                :total-cost="store.totalCost"
                :item-count="store.items.length"
                :purchased-count="store.purchasedCount"
                :progress-percent="store.progressPercent"
                :export-loading="exportLoading"
                @export="onExport"
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

    <!-- Mobile: saved lists drawer -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="mobileSavedListsOpen"
          class="lg:hidden fixed inset-0 bg-black/40 z-40"
          @click="mobileSavedListsOpen = false"
        />
      </Transition>
      <Transition name="slide-left">
        <div
          v-if="mobileSavedListsOpen"
          class="lg:hidden fixed inset-y-0 left-0 w-72 bg-white z-50 shadow-xl flex flex-col"
        >
          <!-- Drawer header -->
          <div class="flex items-center justify-between px-4 py-3 border-b shrink-0">
            <h2 class="font-semibold">Списки покупок</h2>
            <div class="flex items-center gap-2">
              <button
                class="p-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                title="Новый список"
                @click="onCreateList"
              >
                <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </button>
              <button
                class="p-1 rounded hover:bg-gray-100"
                @click="mobileSavedListsOpen = false"
              >
                <IconClose class="w-5 h-5" />
              </button>
            </div>
          </div>

          <!-- List content -->
          <div class="flex-1 overflow-y-auto">
            <SavedShoppingLists
              :lists="store.sortedLists"
              :selected-id="store.currentListId"
              @select="onSelectList"
              @create="onCreateList"
            />
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>
