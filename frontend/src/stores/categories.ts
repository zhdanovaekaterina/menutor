import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  activateCategory,
  checkCategoryUsed,
  createCategory,
  deleteCategoryApi,
  editCategory,
  fetchAllCategories,
  moveCategoryAndDelete,
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
    const result = await createCategory(type, name)
    list(type).value.push({ id: result.id, name, active: true })
    useToastStore().show('Категория создана', 'success')
  }

  async function edit(type: 'product' | 'recipe', id: number, name: string) {
    await editCategory(type, id, name)
    const cat = list(type).value.find((c) => c.id === id)
    if (cat) cat.name = name
    useToastStore().show('Категория обновлена', 'success')
  }

  async function remove(type: 'product' | 'recipe', id: number, hard = false) {
    await deleteCategoryApi(type, id, hard)
    if (hard) {
      list(type).value = list(type).value.filter((c) => c.id !== id)
    } else {
      const cat = list(type).value.find((c) => c.id === id)
      if (cat) cat.active = false
    }
    useToastStore().show(hard ? 'Категория удалена' : 'Категория скрыта', 'success')
  }

  async function activate(type: 'product' | 'recipe', id: number) {
    await activateCategory(type, id)
    const cat = list(type).value.find((c) => c.id === id)
    if (cat) cat.active = true
    useToastStore().show('Категория активирована', 'success')
  }

  async function isUsed(type: 'product' | 'recipe', id: number) {
    return checkCategoryUsed(type, id)
  }

  async function moveAndDelete(type: 'product' | 'recipe', fromId: number, targetId: number): Promise<void> {
    await moveCategoryAndDelete(type, fromId, targetId)
    list(type).value = list(type).value.filter((c) => c.id !== fromId)
  }

  return { productCategories, recipeCategories, loading, list, load, create, edit, remove, activate, isUsed, moveAndDelete }
})
