import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  activateCategory,
  checkCategoryUsed,
  createCategory,
  deleteCategoryApi,
  editCategory,
  fetchAllCategories,
} from '@/api/client'
import type { Category } from '@/api/types'
import { useToastStore } from './toast'

export const useCategoryStore = defineStore('categories', () => {
  const productCategories = ref<Category[]>([])
  const recipeCategories = ref<Category[]>([])
  const loading = ref(false)

  function list(type: 'product' | 'recipe') {
    return type === 'product' ? productCategories : recipeCategories
  }

  async function load(type: 'product' | 'recipe') {
    loading.value = true
    try {
      list(type).value = await fetchAllCategories(type)
    } catch {
      useToastStore().show('Ошибка загрузки категорий', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(type: 'product' | 'recipe', name: string) {
    await createCategory(type, name)
    await load(type)
    useToastStore().show('Категория создана', 'success')
  }

  async function edit(type: 'product' | 'recipe', id: number, name: string) {
    await editCategory(type, id, name)
    await load(type)
    useToastStore().show('Категория обновлена', 'success')
  }

  async function remove(type: 'product' | 'recipe', id: number, hard = false) {
    await deleteCategoryApi(type, id, hard)
    await load(type)
    useToastStore().show(hard ? 'Категория удалена' : 'Категория скрыта', 'success')
  }

  async function activate(type: 'product' | 'recipe', id: number) {
    await activateCategory(type, id)
    await load(type)
    useToastStore().show('Категория активирована', 'success')
  }

  async function isUsed(type: 'product' | 'recipe', id: number) {
    return checkCategoryUsed(type, id)
  }

  return { productCategories, recipeCategories, loading, list, load, create, edit, remove, activate, isUsed }
})
