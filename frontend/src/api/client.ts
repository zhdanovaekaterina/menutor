import axios from 'axios'
import type {
  ActiveCategory,
  Category,
  CostPreviewRequest,
  CostPreviewResponse,
  FamilyMember,
  FamilyMemberCreate,
  FlattenedProduct,
  GenerateFilteredShoppingListRequest,
  ImportResult,
  IngredientRow,
  MealSummaryResponse,
  MealType,
  MealTypeCreate,
  MealTypeUsageResponse,
  Menu,
  MenuSlot,
  MoveSlotRequest,
  PaginatedResponse,
  Preference,
  PreferenceCreate,
  PreferenceMatchResponse,
  Product,
  ProductCreate,
  Recipe,
  RecipeCreate,
  RecipeDependent,
  RemoveItemRequest,
  RenameSavedShoppingListRequest,
  SavedShoppingList,
  SavedShoppingListMeta,
  UpdateSavedShoppingListRequest,
  ValidateSubRecipeRequest,
  ValidateSubRecipeResponse,
} from './types'

const api = axios.create({ baseURL: '/api' })

/* --- Auth interceptors --- */

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (!isRefreshing) {
        isRefreshing = true
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          isRefreshing = false
          redirectToLogin()
          return Promise.reject(error)
        }
        try {
          const { data } = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          isRefreshing = false
          onTokenRefreshed(data.access_token)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return api(originalRequest)
        } catch {
          isRefreshing = false
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          refreshSubscribers = []
          redirectToLogin()
          return Promise.reject(error)
        }
      }

      return new Promise((resolve) => {
        refreshSubscribers.push((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          resolve(api(originalRequest))
        })
      })
    }
    return Promise.reject(error)
  },
)

function redirectToLogin() {
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

/* Auth */
export const changePassword = (current_password: string, new_password: string) =>
  api.post('/auth/me/password', { current_password, new_password })

/* Recipes */
export interface RecipeListParams {
  page?: number
  search?: string
  categoryId?: number
}

export const fetchRecipes = (params?: RecipeListParams) => {
  const p: Record<string, unknown> = {}
  if (params?.page !== undefined) p.page = params.page
  if (params?.search) p.search = params.search
  if (params?.categoryId !== undefined) p.category_id = params.categoryId
  return api.get<PaginatedResponse<Recipe>>('/recipes', { params: p }).then((r) => r.data)
}
export const fetchRecipe = (id: number) => api.get<Recipe>(`/recipes/${id}`).then((r) => r.data)
export const fetchRecipeCategories = () =>
  api.get<ActiveCategory[]>('/recipes/categories').then((r) => r.data)
export const createRecipe = (data: RecipeCreate) =>
  api.post<Recipe>('/recipes', data).then((r) => r.data)
export const updateRecipe = (id: number, data: RecipeCreate) =>
  api.put<Recipe>(`/recipes/${id}`, data).then((r) => r.data)
export const deleteRecipe = (id: number) => api.delete(`/recipes/${id}`)
export const batchDeleteRecipes = (ids: number[]) =>
  api.post('/recipes/batch-delete', ids)

export const validateSubRecipe = (data: ValidateSubRecipeRequest) =>
  api.post<ValidateSubRecipeResponse>('/recipes/validate-sub-recipe', data).then((r) => r.data)

export const fetchFlattenedProducts = (recipeId: number) =>
  api.get<FlattenedProduct[]>(`/recipes/${recipeId}/flattened-products`).then((r) => r.data)

export const previewFlattenedProducts = (recipeId: number, ingredients: IngredientRow[]) =>
  api
    .post<FlattenedProduct[]>(`/recipes/${recipeId}/flattened-products-preview`, { ingredients })
    .then((r) => r.data)

export const fetchRecipeDependents = (recipeId: number) =>
  api.get<RecipeDependent[]>(`/recipes/${recipeId}/dependents`).then((r) => r.data)

export const previewRecipeCost = (data: CostPreviewRequest) =>
  api.post<CostPreviewResponse>('/recipes/cost-preview', data).then((r) => r.data)

export const deleteRecipeWithCheck = (id: number) =>
  api.delete(`/recipes/${id}`, { params: { check_dependents: true } })

/* Products */
export interface ProductListParams {
  page?: number
  search?: string
  categoryId?: number
}

export const fetchProducts = (params?: ProductListParams) => {
  const p: Record<string, unknown> = {}
  if (params?.page !== undefined) p.page = params.page
  if (params?.search) p.search = params.search
  if (params?.categoryId !== undefined) p.category_id = params.categoryId
  return api.get<PaginatedResponse<Product>>('/products', { params: p }).then((r) => r.data)
}
export const fetchProductCategories = () =>
  api.get<ActiveCategory[]>('/products/categories').then((r) => r.data)
export const createProduct = (data: ProductCreate) =>
  api.post<Product>('/products', data).then((r) => r.data)
export const updateProduct = (id: number, data: ProductCreate) =>
  api.put<Product>(`/products/${id}`, data).then((r) => r.data)
export const deleteProduct = (id: number) => api.delete(`/products/${id}`)
export const batchDeleteProducts = (ids: number[]) =>
  api.post('/products/batch-delete', ids)

/* Menus */
export const fetchMenus = () => api.get<Menu[]>('/menus').then((r) => r.data)
export const fetchMenu = (id: number) => api.get<Menu>(`/menus/${id}`).then((r) => r.data)
export const createMenu = (name: string) =>
  api.post<Menu>('/menus', { name }).then((r) => r.data)
export const deleteMenu = (id: number) => api.delete(`/menus/${id}`)
export const addSlot = (menuId: number, slot: MenuSlot) =>
  api.post<Menu>(`/menus/${menuId}/slots`, slot).then((r) => r.data)
export const moveSlotApi = (menuId: number, data: MoveSlotRequest) =>
  api.post<Menu>(`/menus/${menuId}/slots/move`, data).then((r) => r.data)
export const removeSlot = (menuId: number, data: RemoveItemRequest) =>
  api.delete<Menu>(`/menus/${menuId}/slots`, { data }).then((r) => r.data)
export const clearMenu = (menuId: number) =>
  api.post<Menu>(`/menus/${menuId}/clear`).then((r) => r.data)
export const copyMenu = (menuId: number) =>
  api.post<Menu>(`/menus/${menuId}/copy`).then((r) => r.data)

/* Family */
export const fetchFamilyMembers = () =>
  api.get<FamilyMember[]>('/family-members').then((r) => r.data)
export const createFamilyMember = (data: FamilyMemberCreate) =>
  api.post<FamilyMember>('/family-members', data).then((r) => r.data)
export const updateFamilyMember = (id: number, data: FamilyMemberCreate) =>
  api.put<FamilyMember>(`/family-members/${id}`, data).then((r) => r.data)
export const deleteFamilyMember = (id: number) => api.delete(`/family-members/${id}`)

/* Categories */
export const fetchAllCategories = (type: 'product' | 'recipe') =>
  api.get<Category[]>(`/${type}-categories`).then((r) => r.data)
export const createCategory = (type: 'product' | 'recipe', name: string, color: string | null = null) =>
  api.post<{ id: number }>(`/${type}-categories`, { name, color }).then((r) => r.data)
export const editCategory = (type: 'product' | 'recipe', id: number, name: string, color: string | null = null) =>
  api.put<{ id: number }>(`/${type}-categories/${id}`, { name, color }).then((r) => r.data)
export const deleteCategoryApi = (type: 'product' | 'recipe', id: number, hard = false) =>
  api.delete(`/${type}-categories/${id}`, { params: hard ? { hard: true } : {} })
export const activateCategory = (type: 'product' | 'recipe', id: number) =>
  api.post(`/${type}-categories/${id}/activate`)
export const checkCategoryUsed = (type: 'product' | 'recipe', id: number) =>
  api.get<{ used: boolean }>(`/${type}-categories/${id}/used`).then((r) => r.data.used)
export const moveCategoryAndDelete = (
  type: 'product' | 'recipe',
  fromId: number,
  targetCategoryId: number,
) => api.post(`/${type}-categories/${fromId}/move-and-delete`, { target_category_id: targetCategoryId })

/* Shopping List */
export const generateShoppingList = (menuId: number) =>
  api.post<SavedShoppingList>(`/menus/${menuId}/shopping-list`).then((r) => r.data)

/* Meal Summary */
export const fetchMealSummary = (menuId: number) =>
  api.get<MealSummaryResponse>(`/menus/${menuId}/summary`).then((r) => r.data)

export const generateFilteredShoppingList = (menuId: number, slotIndices: number[], excludedSubRecipeIds: number[] = []) =>
  api
    .post<SavedShoppingList>(`/menus/${menuId}/shopping-list/filtered`, {
      slot_indices: slotIndices,
      excluded_sub_recipe_ids: excludedSubRecipeIds,
    } as GenerateFilteredShoppingListRequest)
    .then((r) => r.data)

/* Saved Shopping Lists */
export const fetchSavedShoppingLists = () =>
  api.get<SavedShoppingListMeta[]>('/shopping-lists').then((r) => r.data)

export const createSavedShoppingList = () =>
  api.post<SavedShoppingList>('/shopping-lists').then((r) => r.data)

export const fetchSavedShoppingList = (id: number) =>
  api.get<SavedShoppingList>(`/shopping-lists/${id}`).then((r) => r.data)

export const updateSavedShoppingList = (id: number, data: UpdateSavedShoppingListRequest) =>
  api.put<SavedShoppingList>(`/shopping-lists/${id}`, data).then((r) => r.data)

export const renameSavedShoppingList = (id: number, data: RenameSavedShoppingListRequest) =>
  api.patch<SavedShoppingList>(`/shopping-lists/${id}`, data).then((r) => r.data)

export const deleteSavedShoppingList = (id: number) =>
  api.delete(`/shopping-lists/${id}`)

export const copySavedShoppingList = (id: number) =>
  api.post<SavedShoppingList>(`/shopping-lists/${id}/copy`).then((r) => r.data)

export const toggleItemPurchasedApi = (listId: number, itemId: number) =>
  api
    .post<SavedShoppingList>(`/shopping-lists/${listId}/items/${itemId}/toggle-purchased`)
    .then((r) => r.data)
export const downloadShoppingListText = (menuId: number) =>
  api
    .post(`/menus/${menuId}/shopping-list/export/text`, null, { responseType: 'blob' })
    .then((r) => r.data as Blob)
export const downloadShoppingListCsv = (menuId: number) =>
  api
    .post(`/menus/${menuId}/shopping-list/export/csv`, null, { responseType: 'blob' })
    .then((r) => r.data as Blob)
export const downloadShoppingListPdf = (menuId: number) =>
  api
    .post(`/menus/${menuId}/shopping-list/export/pdf`, null, { responseType: 'blob' })
    .then((r) => r.data as Blob)
export const downloadShoppingListJson = (menuId: number) =>
  api
    .post(`/menus/${menuId}/shopping-list/export/json`, null, { responseType: 'blob' })
    .then((r) => r.data as Blob)

/* Menu PDF export */
export const exportMenuPdf = (menuId: number, paper: 'a4' | 'a3'): Promise<Blob> =>
  api
    .post(`/menus/${menuId}/export/pdf`, null, {
      params: { paper },
      responseType: 'blob',
    })
    .then((r) => r.data as Blob)

/* Import / Export */
export const exportEntities = (entityType: string, format: string, ids?: number[]) =>
  api
    .get(`/${entityType}/export/${format}`, {
      params: ids?.length ? { ids: ids.join(',') } : {},
      responseType: 'blob',
    })
    .then((r) => r.data as Blob)

export const exportExample = (entityType: string, format: string) =>
  api
    .get(`/${entityType}/export/${format}/example`, { responseType: 'blob' })
    .then((r) => r.data as Blob)

export const importEntities = (entityType: string, format: string, file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post<ImportResult>(`/${entityType}/import/${format}`, formData).then((r) => r.data)
}

/* Preferences */
export const fetchPreferences = () =>
  api.get<Preference[]>('/preferences').then((r) => r.data)
export const createPreference = (data: PreferenceCreate) =>
  api.post<Preference>('/preferences', data).then((r) => r.data)
export const updatePreference = (id: number, data: PreferenceCreate) =>
  api.put<Preference>(`/preferences/${id}`, data).then((r) => r.data)
export const deletePreference = (id: number) => api.delete(`/preferences/${id}`)
export const fetchRecipeMatchingPreferences = (recipeId: number) =>
  api.get<PreferenceMatchResponse>(`/recipes/${recipeId}/matching-preferences`).then((r) => r.data)

/* Meal Types */
export const fetchMealTypes = () =>
  api.get<MealType[]>('/meal-types').then((r) => r.data)
export const createMealType = (data: MealTypeCreate) =>
  api.post<MealType>('/meal-types', data).then((r) => r.data)
export const updateMealType = (id: number, data: MealTypeCreate) =>
  api.put<MealType>(`/meal-types/${id}`, data).then((r) => r.data)
export const deleteMealType = (id: number) =>
  api.delete(`/meal-types/${id}`)
export const fetchMealTypeUsage = (id: number) =>
  api.get<MealTypeUsageResponse>(`/meal-types/${id}/usage`).then((r) => r.data)
