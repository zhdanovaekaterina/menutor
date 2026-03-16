import {
  batchDeleteRecipes,
  createRecipe,
  deleteRecipe,
  fetchRecipeCategories,
  fetchRecipes,
  updateRecipe,
} from '@/api/client'
import type { Recipe, RecipeCreate } from '@/api/types'
import { createCrudStore } from './crud-factory'

export const useRecipeStore = createCrudStore<Recipe, RecipeCreate>('recipes', {
  fetchAll: fetchRecipes,
  fetchCategories: fetchRecipeCategories,
  createItem: createRecipe,
  updateItem: updateRecipe,
  deleteItem: deleteRecipe,
  batchDeleteItems: batchDeleteRecipes,
  messages: {
    loadError: 'Ошибка загрузки рецептов',
    created: 'Рецепт создан',
    updated: 'Рецепт обновлён',
    deleted: 'Рецепт удалён',
    batchDeleted: 'Рецепты удалены',
  },
})
