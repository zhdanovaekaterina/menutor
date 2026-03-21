import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { generateShoppingList } from '@/api/client'
import type { ShoppingList, ShoppingListItem } from '@/api/types'
import { useToastStore } from './toast'

export const useShoppingListStore = defineStore('shoppingList', () => {
  const data = ref<ShoppingList | null>(null)
  const loading = ref(false)
  const menuId = ref<number | null>(null)

  const items = computed(() => data.value?.items ?? [])
  const totalCost = computed(() => {
    const sum = items.value.reduce((acc, i) => acc + Number(i.cost.amount), 0)
    return { amount: sum.toFixed(2), currency: 'RUB' }
  })
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

  async function generate(id: number) {
    loading.value = true
    try {
      data.value = await generateShoppingList(id)
      menuId.value = id
    } catch {
      useToastStore().show('Ошибка генерации списка покупок', 'error')
    } finally {
      loading.value = false
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

  function removeMany(productIds: number[]) {
    if (!data.value || !productIds.length) return
    const idSet = new Set(productIds)
    data.value.items = data.value.items.filter((i) => !idSet.has(i.product_id))
  }

  function updateQuantity(productId: number, newAmount: number) {
    if (!data.value) return
    const index = data.value.items.findIndex((i) => i.product_id === productId)
    if (index === -1) return
    const item = data.value.items[index]
    if (!item) return
    const pricePerUnit = item.buy_quantity.amount > 0
      ? Number(item.cost.amount) / item.buy_quantity.amount
      : 0
    data.value.items[index] = {
      ...item,
      buy_quantity: { amount: newAmount, unit: item.buy_quantity.unit },
      buy_quantity_overridden: true,
      cost: { amount: (pricePerUnit * newAmount).toFixed(2), currency: item.cost.currency },
    }
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
    menuId,
    items,
    totalCost,
    purchasedCount,
    progressPercent,
    itemsByCategory,
    generate,
    togglePurchased,
    removeItem,
    removeMany,
    updateQuantity,
    addItem,
  }
})
