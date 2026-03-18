import { ref } from 'vue'

interface Filterable {
  category_id: number
  name: string
}

export function useCategoryFilter<T extends Filterable>() {
  const categoryFilter = ref<number | null>(null)

  function applyFilter(items: T[], searchQuery = ''): T[] {
    const q = searchQuery.toLowerCase()
    return items.filter((item) => {
      if (categoryFilter.value !== null && item.category_id !== categoryFilter.value) return false
      if (q && !item.name.toLowerCase().includes(q)) return false
      return true
    })
  }

  function reset() {
    categoryFilter.value = null
  }

  return { categoryFilter, applyFilter, reset }
}
