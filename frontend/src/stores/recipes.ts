import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  createRecipe,
  deleteRecipe,
  fetchRecipeCategories,
  fetchRecipes,
  updateRecipe,
} from '@/api/client'
import type { ActiveCategory, Recipe, RecipeCreate } from '@/api/types'
import { useToastStore } from './toast'

export const useRecipeStore = defineStore('recipes', () => {
  const recipes = ref<Recipe[]>([])
  const categories = ref<ActiveCategory[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      ;[recipes.value, categories.value] = await Promise.all([
        fetchRecipes(),
        fetchRecipeCategories(),
      ])
    } catch {
      useToastStore().show('Ошибка загрузки рецептов', 'error')
    } finally {
      loading.value = false
    }
  }

  async function create(data: RecipeCreate) {
    const recipe = await createRecipe(data)
    recipes.value.push(recipe)
    useToastStore().show('Рецепт создан', 'success')
    return recipe
  }

  async function update(id: number, data: RecipeCreate) {
    const recipe = await updateRecipe(id, data)
    const idx = recipes.value.findIndex((r) => r.id === id)
    if (idx !== -1) recipes.value[idx] = recipe
    useToastStore().show('Рецепт обновлён', 'success')
    return recipe
  }

  async function remove(id: number) {
    await deleteRecipe(id)
    recipes.value = recipes.value.filter((r) => r.id !== id)
    useToastStore().show('Рецепт удалён', 'success')
  }

  return { recipes, categories, loading, load, create, update, remove }
})
