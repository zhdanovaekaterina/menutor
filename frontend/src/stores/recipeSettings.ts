import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'recipeSettings'

interface Settings {
  showCostColumn: boolean
}

function loadFromStorage(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { showCostColumn: true, ...JSON.parse(raw) }
  } catch {}
  return { showCostColumn: true }
}

export const useRecipeSettingsStore = defineStore('recipeSettings', () => {
  const saved = loadFromStorage()
  const showCostColumn = ref(saved.showCostColumn)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ showCostColumn: showCostColumn.value }))
  }

  watch(showCostColumn, persist)

  function toggleShowCostColumn() {
    showCostColumn.value = !showCostColumn.value
  }

  return { showCostColumn, toggleShowCostColumn }
})
