import axios from 'axios'
import type {
  ActiveCategory,
  Category,
  FamilyMember,
  FamilyMemberCreate,
  Menu,
  MenuSlot,
  Product,
  ProductCreate,
  Recipe,
  RecipeCreate,
  RemoveItemRequest,
  ShoppingList,
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

/* Recipes */
export const fetchRecipes = () => api.get<Recipe[]>('/recipes').then((r) => r.data)
export const fetchRecipe = (id: number) => api.get<Recipe>(`/recipes/${id}`).then((r) => r.data)
export const fetchRecipeCategories = () =>
  api.get<ActiveCategory[]>('/recipes/categories').then((r) => r.data)
export const createRecipe = (data: RecipeCreate) =>
  api.post<Recipe>('/recipes', data).then((r) => r.data)
export const updateRecipe = (id: number, data: RecipeCreate) =>
  api.put<Recipe>(`/recipes/${id}`, data).then((r) => r.data)
export const deleteRecipe = (id: number) => api.delete(`/recipes/${id}`)

/* Products */
export const fetchProducts = () => api.get<Product[]>('/products').then((r) => r.data)
export const fetchProductCategories = () =>
  api.get<ActiveCategory[]>('/products/categories').then((r) => r.data)
export const createProduct = (data: ProductCreate) =>
  api.post<Product>('/products', data).then((r) => r.data)
export const updateProduct = (id: number, data: ProductCreate) =>
  api.put<Product>(`/products/${id}`, data).then((r) => r.data)
export const deleteProduct = (id: number) => api.delete(`/products/${id}`)

/* Menus */
export const fetchMenus = () => api.get<Menu[]>('/menus').then((r) => r.data)
export const fetchMenu = (id: number) => api.get<Menu>(`/menus/${id}`).then((r) => r.data)
export const createMenu = (name: string) =>
  api.post<Menu>('/menus', { name }).then((r) => r.data)
export const deleteMenu = (id: number) => api.delete(`/menus/${id}`)
export const addSlot = (menuId: number, slot: MenuSlot) =>
  api.post<Menu>(`/menus/${menuId}/slots`, slot).then((r) => r.data)
export const removeSlot = (menuId: number, data: RemoveItemRequest) =>
  api.delete<Menu>(`/menus/${menuId}/slots`, { data }).then((r) => r.data)
export const clearMenu = (menuId: number) =>
  api.post<Menu>(`/menus/${menuId}/clear`).then((r) => r.data)

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
export const createCategory = (type: 'product' | 'recipe', name: string) =>
  api.post<{ id: number }>(`/${type}-categories`, { name }).then((r) => r.data)
export const editCategory = (type: 'product' | 'recipe', id: number, name: string) =>
  api.put<{ id: number }>(`/${type}-categories/${id}`, { name }).then((r) => r.data)
export const deleteCategoryApi = (type: 'product' | 'recipe', id: number, hard = false) =>
  api.delete(`/${type}-categories/${id}`, { params: hard ? { hard: true } : {} })
export const activateCategory = (type: 'product' | 'recipe', id: number) =>
  api.post(`/${type}-categories/${id}/activate`)
export const checkCategoryUsed = (type: 'product' | 'recipe', id: number) =>
  api.get<{ used: boolean }>(`/${type}-categories/${id}/used`).then((r) => r.data.used)

/* Shopping List */
export const generateShoppingList = (menuId: number) =>
  api.post<ShoppingList>(`/menus/${menuId}/shopping-list`).then((r) => r.data)
export const exportShoppingListText = (menuId: number) =>
  api.post<string>(`/menus/${menuId}/shopping-list/export/text`).then((r) => r.data)
