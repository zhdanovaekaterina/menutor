import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  copySavedShoppingList,
  createSavedShoppingList,
  deleteSavedShoppingList,
  fetchSavedShoppingList,
  fetchSavedShoppingLists,
  generateShoppingList,
  renameSavedShoppingList,
  toggleItemPurchasedApi,
  updateSavedShoppingList,
} from '@/api/client'
import type { SavedShoppingList, SavedShoppingListItem, SavedShoppingListMeta } from '@/api/types'
import { useToastStore } from './toast'

// Build a comparable snapshot of items, excluding the `purchased` field so that
// purchased toggles (which auto-save via the API) do not contribute to dirty state.
function buildComparableSnapshot(items: SavedShoppingListItem[]): string {
  const comparable = items.map((item) => ({
    id: item.id,
    product_id: item.product_id,
    product_name: item.product_name,
    category: item.category,
    quantity: item.quantity,
    buy_quantity: item.buy_quantity,
    buy_quantity_overridden: item.buy_quantity_overridden,
    cost: item.cost,
    recipe_quantity: item.recipe_quantity,
    item_order: item.item_order,
  }))
  return JSON.stringify(comparable)
}

export const useShoppingListStore = defineStore('shoppingList', () => {
  const savedLists = ref<SavedShoppingListMeta[]>([])
  const currentListId = ref<number | null>(null)
  const data = ref<SavedShoppingList | null>(null)
  const snapshot = ref<string>('')
  const loading = ref(false)
  const listsLoading = ref(false)
  const sidebarOpen = ref(true)

  // ----- Computed -----

  const isDirty = computed(() => {
    if (!data.value || !snapshot.value) return false
    return buildComparableSnapshot(data.value.items) !== snapshot.value
  })

  const items = computed(() => data.value?.items ?? [])

  const totalCost = computed(() => {
    const sum = items.value.reduce((acc, i) => acc + Number(i.cost.amount), 0)
    return { amount: sum.toFixed(2), currency: 'RUB' }
  })

  const purchasedCount = computed(() => items.value.filter((i) => i.purchased).length)

  const progressPercent = computed(() =>
    items.value.length ? Math.round((purchasedCount.value / items.value.length) * 100) : 0,
  )

  const PURCHASED_CATEGORY = 'Куплено'

  const itemsByCategory = computed(() => {
    const grouped: Record<string, SavedShoppingListItem[]> = {}
    const purchased: SavedShoppingListItem[] = []
    for (const item of items.value) {
      if (item.purchased) {
        purchased.push(item)
      } else {
        ;(grouped[item.category] ??= []).push(item)
      }
    }
    if (purchased.length) {
      grouped[PURCHASED_CATEGORY] = purchased
    }
    return grouped
  })

  // ----- Helpers -----

  function takeSnapshot() {
    snapshot.value = data.value ? buildComparableSnapshot(data.value.items) : ''
  }

  function updateMetaInList(updated: SavedShoppingList) {
    const idx = savedLists.value.findIndex((l) => l.id === updated.id)
    const meta: SavedShoppingListMeta = {
      id: updated.id,
      name: updated.name,
      source_menu_id: updated.source_menu_id,
      created_at: updated.created_at,
      updated_at: updated.updated_at,
    }
    if (idx !== -1) {
      savedLists.value[idx] = meta
    }
  }

  function prependMeta(list: SavedShoppingList) {
    const meta: SavedShoppingListMeta = {
      id: list.id,
      name: list.name,
      source_menu_id: list.source_menu_id,
      created_at: list.created_at,
      updated_at: list.updated_at,
    }
    savedLists.value.unshift(meta)
  }

  // ----- Actions -----

  async function loadLists(): Promise<void> {
    listsLoading.value = true
    try {
      savedLists.value = await fetchSavedShoppingLists()
    } catch {
      useToastStore().show('Ошибка загрузки списков покупок', 'error')
    } finally {
      listsLoading.value = false
    }
  }

  async function loadList(id: number): Promise<void> {
    loading.value = true
    try {
      data.value = await fetchSavedShoppingList(id)
      currentListId.value = id
      takeSnapshot()
    } catch {
      useToastStore().show('Ошибка загрузки списка покупок', 'error')
    } finally {
      loading.value = false
    }
  }

  async function generate(menuId: number): Promise<void> {
    loading.value = true
    try {
      const list = await generateShoppingList(menuId)
      data.value = list
      currentListId.value = list.id
      takeSnapshot()
      // Prepend to sidebar list and reload full list to keep in sync
      prependMeta(list)
    } catch {
      useToastStore().show('Ошибка генерации списка покупок', 'error')
    } finally {
      loading.value = false
    }
  }

  async function saveChanges(): Promise<void> {
    if (!data.value) return
    loading.value = true
    try {
      const updated = await updateSavedShoppingList(data.value.id, {
        name: data.value.name,
        items: data.value.items.map((item) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          category: item.category,
          quantity_amount: item.quantity.amount,
          quantity_unit: item.quantity.unit,
          buy_quantity_amount: item.buy_quantity.amount,
          buy_quantity_unit: item.buy_quantity.unit,
          buy_quantity_overridden: item.buy_quantity_overridden,
          cost_amount: Number(item.cost.amount),
          cost_currency: item.cost.currency,
          purchased: item.purchased,
          recipe_quantity_amount: item.recipe_quantity?.amount ?? null,
          recipe_quantity_unit: item.recipe_quantity?.unit ?? null,
          item_order: item.item_order,
        })),
      })
      data.value = updated
      takeSnapshot()
      updateMetaInList(updated)
      useToastStore().show('Список сохранён', 'success')
    } catch {
      useToastStore().show('Ошибка сохранения списка', 'error')
    } finally {
      loading.value = false
    }
  }

  async function createEmpty(): Promise<void> {
    loading.value = true
    try {
      const list = await createSavedShoppingList()
      data.value = list
      currentListId.value = list.id
      takeSnapshot()
      prependMeta(list)
    } catch {
      useToastStore().show('Ошибка создания списка', 'error')
    } finally {
      loading.value = false
    }
  }

  async function rename(id: number, name: string): Promise<void> {
    try {
      const updated = await renameSavedShoppingList(id, { name })
      updateMetaInList(updated)
      if (data.value && data.value.id === id) {
        data.value = { ...data.value, name: updated.name, updated_at: updated.updated_at }
      }
    } catch {
      useToastStore().show('Ошибка переименования списка', 'error')
    }
  }

  async function copy(id: number): Promise<void> {
    loading.value = true
    try {
      const list = await copySavedShoppingList(id)
      data.value = list
      currentListId.value = list.id
      takeSnapshot()
      prependMeta(list)
    } catch {
      useToastStore().show('Ошибка копирования списка', 'error')
    } finally {
      loading.value = false
    }
  }

  async function remove(id: number): Promise<void> {
    try {
      await deleteSavedShoppingList(id)
      savedLists.value = savedLists.value.filter((l) => l.id !== id)
      if (currentListId.value === id) {
        data.value = null
        currentListId.value = null
        snapshot.value = ''
      }
    } catch {
      useToastStore().show('Ошибка удаления списка', 'error')
    }
  }

  async function togglePurchased(itemId: number): Promise<void> {
    if (!currentListId.value) return
    try {
      const updated = await toggleItemPurchasedApi(currentListId.value, itemId)
      data.value = updated
      // Re-take snapshot so purchased-only change doesn't inflate isDirty.
      // Since buildComparableSnapshot excludes purchased, snapshot stays valid;
      // but if other changes were already pending we keep them dirty — no re-snapshot here.
    } catch {
      useToastStore().show('Ошибка обновления статуса покупки', 'error')
    }
  }

  // ----- Local mutations (optimistic UI, set isDirty via computed) -----

  function removeItem(productId: number) {
    if (!data.value) return
    data.value.items = data.value.items.filter((i) => i.product_id !== productId)
  }

  function removeMany(productIds: number[]) {
    if (!data.value || !productIds.length) return
    const idSet = new Set(productIds)
    data.value.items = data.value.items.filter(
      (i) => i.product_id === null || !idSet.has(i.product_id),
    )
  }

  function updateQuantity(productId: number, newAmount: number) {
    if (!data.value) return
    const index = data.value.items.findIndex((i) => i.product_id === productId)
    if (index === -1) return
    const item = data.value.items[index]
    if (!item) return
    const pricePerUnit =
      item.buy_quantity.amount > 0 ? Number(item.cost.amount) / item.buy_quantity.amount : 0
    data.value.items[index] = {
      ...item,
      buy_quantity: { amount: newAmount, unit: item.buy_quantity.unit },
      buy_quantity_overridden: true,
      cost: { amount: (pricePerUnit * newAmount).toFixed(2), currency: item.cost.currency },
    }
  }

  function addItem(item: SavedShoppingListItem) {
    if (!data.value) return
    data.value.items.push(item)
  }

  function setSidebarOpen(open: boolean) {
    sidebarOpen.value = open
  }

  return {
    savedLists,
    currentListId,
    data,
    isDirty,
    loading,
    listsLoading,
    sidebarOpen,
    items,
    totalCost,
    purchasedCount,
    progressPercent,
    itemsByCategory,
    loadLists,
    loadList,
    generate,
    saveChanges,
    createEmpty,
    rename,
    copy,
    remove,
    togglePurchased,
    removeItem,
    removeMany,
    updateQuantity,
    addItem,
    setSidebarOpen,
  }
})
