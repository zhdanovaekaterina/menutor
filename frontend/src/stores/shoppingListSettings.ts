import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type GroupBy = 'category' | 'supplier'

const STORAGE_KEY = 'shoppingListSettings'

interface Settings {
  hidePurchased: boolean
  groupBy: GroupBy
}

function loadFromStorage(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { hidePurchased: false, groupBy: 'category', ...JSON.parse(raw) }
  } catch {}
  return { hidePurchased: false, groupBy: 'category' }
}

export const useShoppingListSettingsStore = defineStore('shoppingListSettings', () => {
  const saved = loadFromStorage()
  const hidePurchased = ref(saved.hidePurchased)
  const groupBy = ref<GroupBy>(saved.groupBy)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ hidePurchased: hidePurchased.value, groupBy: groupBy.value }))
  }

  watch(hidePurchased, persist)
  watch(groupBy, persist)

  function toggleHidePurchased() {
    hidePurchased.value = !hidePurchased.value
  }

  function setGroupBy(value: GroupBy) {
    groupBy.value = value
  }

  return { hidePurchased, groupBy, toggleHidePurchased, setGroupBy }
})
