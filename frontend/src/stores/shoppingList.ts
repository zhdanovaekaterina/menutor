import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { exportShoppingListText, generateShoppingList } from '@/api/client'
import type { ShoppingList, ShoppingListItem } from '@/api/types'
import { useToastStore } from './toast'

export const useShoppingListStore = defineStore('shoppingList', () => {
  const data = ref<ShoppingList | null>(null)
  const loading = ref(false)

  const items = computed(() => data.value?.items ?? [])
  const totalCost = computed(() => data.value?.total_cost ?? { amount: '0', currency: 'RUB' })
  const purchasedCount = computed(() => items.value.filter((i) => i.purchased).length)
  const progressPercent = computed(() =>
    items.value.length ? Math.round((purchasedCount.value / items.value.length) * 100) : 0,
  )

  const itemsByCategory = computed(() => {
    const grouped: Record<string, ShoppingListItem[]> = {}
    for (const item of items.value) {
      ;(grouped[item.category] ??= []).push(item)
    }
    return grouped
  })

  async function generate(menuId: number) {
    loading.value = true
    try {
      data.value = await generateShoppingList(menuId)
    } catch {
      useToastStore().show('Ошибка генерации списка покупок', 'error')
    } finally {
      loading.value = false
    }
  }

  async function exportText(menuId: number) {
    try {
      return await exportShoppingListText(menuId)
    } catch {
      useToastStore().show('Ошибка экспорта', 'error')
      return null
    }
  }

  function togglePurchased(productId: number) {
    const item = items.value.find((i) => i.product_id === productId)
    if (item) item.purchased = !item.purchased
  }

  function removeItem(productId: number) {
    if (!data.value) return
    data.value.items = data.value.items.filter((i) => i.product_id !== productId)
  }

  function updateQuantity(productId: number, newAmount: number) {
    const item = items.value.find((i) => i.product_id === productId)
    if (item) item.quantity.amount = newAmount
  }

  function addItem(item: ShoppingListItem) {
    if (!data.value) {
      data.value = { items: [], total_cost: { amount: '0', currency: 'RUB' } }
    }
    data.value.items.push(item)
  }

  return {
    data,
    loading,
    items,
    totalCost,
    purchasedCount,
    progressPercent,
    itemsByCategory,
    generate,
    exportText,
    togglePurchased,
    removeItem,
    updateQuantity,
    addItem,
  }
})
