import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'shoppingListSettings'

function loadFromStorage(): { hidePurchased: boolean } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return { hidePurchased: false }
}

export const useShoppingListSettingsStore = defineStore('shoppingListSettings', () => {
  const saved = loadFromStorage()
  const hidePurchased = ref(saved.hidePurchased)

  watch(hidePurchased, (val) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ hidePurchased: val }))
  })

  function toggleHidePurchased() {
    hidePurchased.value = !hidePurchased.value
  }

  return { hidePurchased, toggleHidePurchased }
})
