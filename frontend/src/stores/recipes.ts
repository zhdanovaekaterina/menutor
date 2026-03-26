import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { ActiveCategory, Recipe, RecipeCreate } from '@/api/types'
import {
  batchDeleteRecipes,
  createRecipe,
  deleteRecipe,
  fetchRecipeCategories,
  fetchRecipes,
  updateRecipe,
} from '@/api/client'
import { PAGE_SIZE } from '@/utils/pagination'
import { useToastStore } from './toast'

export const useRecipeStore = defineStore('recipes', () => {
  const items = ref<Recipe[]>([])
  const allItems = ref<Recipe[]>([])
  const categories = ref<ActiveCategory[]>([])
  const loading = ref(false)
  const page = ref(1)
  const total = ref(0)
  const pageSize = ref(PAGE_SIZE)
  const search = ref('')
  const categoryId = ref<number | null>(null)

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  async function _loadPage() {
    const data = await fetchRecipes({
      page: page.value,
      search: search.value || undefined,
      categoryId: categoryId.value ?? undefined,
    })
    items.value = data.items
    total.value = data.total
    pageSize.value = data.page_size || PAGE_SIZE
  }

  async function _loadAll() {
    const data = await fetchRecipes()
    allItems.value = data.items
  }

  async function load() {
    loading.value = true
    try {
      const [, cats] = await Promise.all([
        Promise.all([_loadPage(), _loadAll()]),
        fetchRecipeCategories(),
      ])
      categories.value = cats
    } catch {
      useToastStore().show('Ошибка загрузки рецептов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function setPage(p: number) {
    page.value = p
    loading.value = true
    try {
      await _loadPage()
    } catch {
      useToastStore().show('Ошибка загрузки рецептов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function setFilters(newSearch: string, newCategoryId: number | null) {
    search.value = newSearch
    categoryId.value = newCategoryId
    page.value = 1
    loading.value = true
    try {
      await _loadPage()
    } catch {
      useToastStore().show('Ошибка загрузки рецептов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(data: RecipeCreate): Promise<Recipe> {
    const item = await createRecipe(data)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Рецепт создан', 'success')
    return item
  }

  async function update(id: number, data: RecipeCreate): Promise<Recipe> {
    const item = await updateRecipe(id, data)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Рецепт обновлён', 'success')
    return item
  }

  async function remove(id: number) {
    await deleteRecipe(id)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Рецепт удалён', 'success')
  }

  async function removeMany(ids: number[]) {
    if (!ids.length) return
    await batchDeleteRecipes(ids)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Рецепты удалены', 'success')
  }

  async function removeAll() {
    const ids = allItems.value.map((i) => i.id)
    if (!ids.length) return
    await batchDeleteRecipes(ids)
    await Promise.all([_loadPage(), _loadAll()])
    useToastStore().show('Рецепты удалены', 'success')
  }

  return {
    items,
    allItems,
    categories,
    loading,
    page,
    total,
    totalPages,
    search,
    categoryId,
    pageSize,
    load,
    setPage,
    setFilters,
    create,
    update,
    remove,
    removeMany,
    removeAll,
  }
})
