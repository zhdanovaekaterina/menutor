# Frontend — Vue 3 + TypeScript + Pinia

**File location:** `frontend/src/`

The frontend is a Vue 3 SPA with TypeScript, Pinia state management, and Tailwind CSS v4. It mirrors the backend's architecture: views correspond to routes, stores manage state, and the API client handles HTTP communication.

---

## Project Structure

```
frontend/src/
├── main.ts                        # Vue app initialization
├── App.vue                        # Root layout component
├── router/
│   └── index.ts                   # Vue Router configuration (6 routes + nested settings)
├── stores/                        # Pinia stores (state management)
│   ├── auth.ts                    # User, tokens, login/logout
│   ├── recipes.ts                 # Recipe state and CRUD operations
│   ├── products.ts                # Product state and CRUD operations
│   ├── menus.ts                   # Menu and slot state
│   ├── family.ts                  # Family members state
│   ├── categories.ts              # Product/recipe categories state
│   ├── shoppingList.ts            # Shopping list items, cost tracking
│   ├── toast.ts                   # Toast notification queue
│   └── crud-factory.ts            # Reusable CRUD store generator
├── api/
│   ├── client.ts                  # axios instance with JWT interceptor
│   ├── auth.ts                    # Auth API calls
│   └── types.ts                   # TypeScript interfaces (match Pydantic)
├── views/                         # Page-level components
│   ├── AuthView.vue               # Login/register
│   ├── MenuPlannerView.vue        # 7-day meal planner
│   ├── ShoppingListView.vue       # Shopping list page
│   ├── RecipeListView.vue         # Recipe management page
│   ├── ProductListView.vue        # Product management page
│   └── SettingsView.vue           # Settings container
├── components/                    # Reusable UI components
│   ├── layout/                    # Layout components (AppSidebar, MobileBottomNav)
│   ├── planner/                   # Planner-specific (PlannerGrid, GridCell, SourcePanel)
│   ├── shopping/                  # Shopping-specific (ShoppingTable, ShoppingSummary)
│   ├── recipes/                   # Recipe-specific (RecipeTable, RecipeForm)
│   ├── products/                  # Product-specific (ProductTable, ProductForm)
│   ├── settings/                  # Settings-specific (FamilyPanel, CategoryPanel)
│   └── ui/                        # Generic UI primitives (ConfirmDialog, ToastNotification, etc.)
├── composables/                   # Reusable Vue 3 composition functions
│   ├── useSelection.ts            # Multi-row selection
│   ├── useDropdown.ts             # Dropdown open/close state
│   ├── useCategoryFilter.ts       # Category filtering logic
│   ├── useContextMenu.ts          # Right-click context menu
│   └── useFileDownload.ts         # File/blob download utility
├── utils/
│   ├── units.ts                   # Unit conversion, formatting helpers
│   └── api.ts                     # API response error handling
├── assets/
│   └── index.css                  # Tailwind CSS, global styles
└── vite.config.ts                 # Vite + Tailwind plugin configuration
```

---

## Initialization

**File:** `frontend/src/main.ts`

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/index.css'

const app = createApp(App)

app.use(createPinia())  // State management
app.use(router)         // Routing

app.mount('#app')
```

---

## Root Layout

**File:** `frontend/src/App.vue`

```vue
<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar navigation -->
    <AppSidebar />

    <!-- Main content -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/layout/AppSidebar.vue'
</script>
```

---

## Vue Router

**File:** `frontend/src/router/index.ts`

```typescript
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/planner',
  },
  {
    path: '/auth',
    component: () => import('@/views/AuthView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/planner',
    component: () => import('@/views/MenuPlannerView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/shopping-list',
    component: () => import('@/views/ShoppingListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/recipes',
    component: () => import('@/views/RecipeListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/products',
    component: () => import('@/views/ProductListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { requiresAuth: true },
    redirect: '/settings/family',
    children: [
      {
        path: 'family',
        component: () => import('@/components/settings/FamilyPanel.vue'),
      },
      {
        path: 'product-categories',
        component: () => import('@/components/settings/CategoryPanel.vue'),
        props: { type: 'product' },
      },
      {
        path: 'recipe-categories',
        component: () => import('@/components/settings/CategoryPanel.vue'),
        props: { type: 'recipe' },
      },
      {
        path: 'about',
        component: () => import('@/components/settings/AboutPanel.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Global navigation guard: check authentication
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/auth')
  } else if (to.path === '/auth' && auth.isAuthenticated) {
    next('/planner')
  } else {
    next()
  }
})

export default router
```

---

## Pinia Stores

### Auth Store

**File:** `frontend/src/stores/auth.ts`

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ─── Computed ───────────────────────────────────────────

  const isAuthenticated = computed(() => !!accessToken.value)

  // ─── Actions ─────────────────────────────────────────────

  async function register(email: string, password: string, nickname: string) {
    loading.value = true
    error.value = null

    try {
      const response = await authApi.register({ email, password, nickname })
      setTokens(response.access_token, response.refresh_token)
      await fetchUser()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Registration failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    error.value = null

    try {
      const response = await authApi.login({ email, password })
      setTokens(response.access_token, response.refresh_token)
      await fetchUser()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    try {
      user.value = await authApi.getMe()
    } catch (err) {
      console.error('Failed to fetch user:', err)
    }
  }

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      logout()
      return
    }

    try {
      const newAccessToken = await authApi.refresh(refreshToken.value)
      accessToken.value = newAccessToken
      localStorage.setItem('access_token', newAccessToken)
    } catch (err) {
      logout()
      throw err
    }
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    accessToken,
    refreshToken,
    user,
    loading,
    error,
    isAuthenticated,
    register,
    login,
    fetchUser,
    setTokens,
    refreshAccessToken,
    logout,
  }
})
```

### Recipe Store (CRUD Factory)

**File:** `frontend/src/stores/recipes.ts`

```typescript
import { defineStore } from 'pinia'
import * as api from '@/api/client'
import { useToastStore } from './toast'

export const useRecipeStore = defineStore('recipes', () => {
  const recipes = ref<Recipe[]>([])
  const selectedId = ref<number | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const toast = useToastStore()

  const selected = computed(() =>
    recipes.value.find(r => r.id === selectedId.value)
  )

  async function loadRecipes(categoryId?: number) {
    loading.value = true
    error.value = null

    try {
      recipes.value = await api.getRecipes({ category_id: categoryId })
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load recipes'
      toast.error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function createRecipe(data: RecipeCreate) {
    loading.value = true
    error.value = null

    try {
      const recipe = await api.createRecipe(data)
      recipes.value.push(recipe)
      toast.success('Рецепт создан')
      return recipe
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create recipe'
      toast.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateRecipe(id: number, data: RecipeUpdate) {
    loading.value = true
    error.value = null

    try {
      const recipe = await api.updateRecipe(id, data)
      const idx = recipes.value.findIndex(r => r.id === id)
      if (idx >= 0) recipes.value[idx] = recipe
      toast.success('Рецепт обновлен')
      return recipe
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update recipe'
      toast.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteRecipe(id: number) {
    loading.value = true
    error.value = null

    try {
      await api.deleteRecipe(id)
      recipes.value = recipes.value.filter(r => r.id !== id)
      if (selectedId.value === id) selectedId.value = null
      toast.success('Рецепт удален')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete recipe'
      toast.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  function select(id: number) {
    selectedId.value = id
  }

  function clearSelection() {
    selectedId.value = null
  }

  return {
    recipes,
    selectedId,
    selected,
    loading,
    error,
    loadRecipes,
    createRecipe,
    updateRecipe,
    deleteRecipe,
    select,
    clearSelection,
  }
})
```

### Other Stores

- `products.ts` — Product CRUD
- `menus.ts` — Menu and slot management
- `family.ts` — Family member CRUD
- `categories.ts` — Category CRUD
- `shoppingList.ts` — Shopping list state (items, total cost, purchased tracking)
- `toast.ts` — Toast notification queue

---

## API Client

**File:** `frontend/src/api/client.ts`

```typescript
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

const client: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: add JWT token
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// Response interceptor: handle 401 (auto-refresh)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    const originalRequest = error.config

    if (error.response?.status === 401 && auth.refreshToken) {
      try {
        await auth.refreshAccessToken()
        // Retry original request with new token
        return client(originalRequest)
      } catch {
        auth.logout()
        window.location.href = '/auth'
      }
    }

    return Promise.reject(error)
  }
)

export default client

// Typed API wrappers
export const getRecipes = (params?: { category_id?: number }) =>
  client.get<Recipe[]>('/recipes', { params }).then(r => r.data)

export const createRecipe = (data: RecipeCreate) =>
  client.post<Recipe>('/recipes', data).then(r => r.data)

export const updateRecipe = (id: number, data: RecipeUpdate) =>
  client.put<Recipe>(`/recipes/${id}`, data).then(r => r.data)

export const deleteRecipe = (id: number) =>
  client.delete(`/recipes/${id}`).then(r => r.data)

// ... similar for products, menus, etc.
```

**File:** `frontend/src/api/types.ts`

TypeScript interfaces matching Pydantic schemas:

```typescript
export interface User {
  id: number
  email: string
  nickname: string
}

export interface Recipe {
  id: number
  name: string
  servings: number
  category_id: number
  ingredients: RecipeIngredient[]
  steps: CookingStep[]
  weight: number
  total_pieces: number | null
  pieces_per_portion: number | null
}

export interface RecipeCreate {
  name: string
  servings: number
  category_id: number
  ingredients: RecipeIngredientCreate[]
  steps: CookingStepCreate[]
  weight?: number
  total_pieces?: number | null
  pieces_per_portion?: number | null
}

export interface RecipeIngredient {
  product_id: number
  sub_recipe_id: number | null
  quantity_amount: number
  quantity_unit: string
  sub_recipe_name?: string
}

export interface CookingStep {
  description: string
  order: number
}

// ... similar for Product, Menu, ShoppingList, etc.
```

---

## Components

### RecipeForm Component

**File:** `frontend/src/components/recipes/RecipeForm.vue`

```vue
<template>
  <form @submit.prevent="submit" class="space-y-4">
    <!-- Name -->
    <div>
      <label class="block text-sm font-medium mb-1">Название *</label>
      <input
        v-model="form.name"
        type="text"
        class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
        placeholder="Блины, Борщ, Суп..."
        required
      />
    </div>

    <!-- Category & Servings -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium mb-1">Категория *</label>
        <select v-model.number="form.category_id" class="w-full border rounded-lg px-3 py-2">
          <option value="">Выберите категорию</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">
            {{ cat.name }}
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">Порций</label>
        <input
          v-model.number="form.servings"
          type="number"
          min="1"
          class="w-full border rounded-lg px-3 py-2"
        />
      </div>
    </div>

    <!-- Ingredients -->
    <fieldset>
      <legend class="block text-sm font-medium mb-2 bg-slate-200 px-3 py-2 rounded">
        Ингредиенты
      </legend>

      <div class="space-y-2 mb-2">
        <div v-for="(ing, i) in form.ingredients" :key="i" class="flex gap-2 items-end">
          <select
            v-model.number="ing.product_id"
            class="flex-1 border rounded px-2 py-1 text-sm"
          >
            <option v-for="p in products" :key="p.id" :value="p.id">
              {{ p.name }}
            </option>
          </select>

          <input
            v-model.number="ing.quantity_amount"
            type="number"
            step="0.01"
            min="0.01"
            class="w-20 border rounded px-2 py-1 text-sm"
          />

          <span class="w-12 text-center text-sm text-gray-500">
            {{ getUnitFor(ing.product_id) }}
          </span>

          <button
            type="button"
            @click="form.ingredients.splice(i, 1)"
            class="text-red-600 hover:text-red-800"
          >
            ✕
          </button>
        </div>
      </div>

      <button
        type="button"
        @click="addIngredient"
        class="btn-outline text-sm"
      >
        + Добавить
      </button>
    </fieldset>

    <!-- Steps -->
    <fieldset>
      <legend class="block text-sm font-medium mb-2 bg-slate-200 px-3 py-2 rounded">
        Шаги приготовления
      </legend>

      <ol class="space-y-1 mb-2 list-decimal list-inside">
        <li v-for="(step, i) in form.steps" :key="i" class="text-sm">
          {{ step.description }}
          <button
            type="button"
            @click="form.steps.splice(i, 1)"
            class="ml-2 text-red-600"
          >
            ✕
          </button>
        </li>
      </ol>

      <div class="flex gap-2">
        <input
          v-model="newStep"
          type="text"
          placeholder="Описание шага..."
          class="flex-1 border rounded px-2 py-1 text-sm"
          @keydown.enter="addStep"
        />
        <button
          type="button"
          @click="addStep"
          class="btn-outline text-sm"
        >
          +
        </button>
      </div>
    </fieldset>

    <!-- Actions -->
    <div class="flex gap-2 pt-4 border-t">
      <button type="submit" class="btn-primary flex-1">Сохранить</button>
      <button
        type="button"
        @click="reset"
        class="btn-outline flex-1"
      >
        Отмена
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRecipeStore } from '@/stores/recipes'
import { useProductStore } from '@/stores/products'
import { useCategoryStore } from '@/stores/categories'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{ recipe?: Recipe }>()
const emit = defineEmits<{ saved: [recipe: Recipe] }>()

const recipeStore = useRecipeStore()
const productStore = useProductStore()
const categoryStore = useCategoryStore()
const toast = useToastStore()

const form = reactive<RecipeCreate>({
  name: props.recipe?.name || '',
  servings: props.recipe?.servings || 4,
  category_id: props.recipe?.category_id || 0,
  ingredients: props.recipe?.ingredients.map(i => ({
    product_id: i.product_id,
    sub_recipe_id: i.sub_recipe_id,
    quantity_amount: i.quantity_amount,
    quantity_unit: i.quantity_unit,
  })) || [],
  steps: props.recipe?.steps || [],
})

const newStep = ref('')

const categories = computed(() => categoryStore.recipeCategories)
const products = computed(() => productStore.products)

function getUnitFor(productId: number): string {
  const product = products.value.find(p => p.id === productId)
  return product?.recipe_unit || ''
}

function addIngredient() {
  form.ingredients.push({
    product_id: 0,
    quantity_amount: 1,
    quantity_unit: 'g',
  })
}

function addStep() {
  if (newStep.value.trim()) {
    form.steps.push({
      description: newStep.value,
      order: form.steps.length,
    })
    newStep.value = ''
  }
}

async function submit() {
  if (!form.category_id) {
    toast.error('Выберите категорию')
    return
  }

  try {
    if (props.recipe?.id) {
      await recipeStore.updateRecipe(props.recipe.id, form)
    } else {
      await recipeStore.createRecipe(form)
    }
    reset()
    emit('saved', form as Recipe)
  } catch (err) {
    // Error handled by store
  }
}

function reset() {
  form.name = ''
  form.servings = 4
  form.category_id = 0
  form.ingredients = []
  form.steps = []
  newStep.value = ''
}
</script>
```

### MenuPlannerView Component

Complex component with:
- 7×3 drag-drop grid
- Recipe/product source panel
- Saved menus list
- Family display
- Shopping list generation

See `frontend/src/views/MenuPlannerView.vue` for full implementation.

---

## Composables

**File:** `frontend/src/composables/useSelection.ts`

```typescript
import { ref, computed } from 'vue'

export function useSelection<T extends { id: number }>(items: Ref<T[]>) {
  const selectedIds = ref<Set<number>>(new Set())

  const selected = computed(() =>
    items.value.filter(item => selectedIds.value.has(item.id))
  )

  function select(id: number) {
    selectedIds.value.add(id)
  }

  function deselect(id: number) {
    selectedIds.value.delete(id)
  }

  function toggle(id: number) {
    if (selectedIds.value.has(id)) {
      selectedIds.value.delete(id)
    } else {
      selectedIds.value.add(id)
    }
  }

  function selectAll() {
    items.value.forEach(item => selectedIds.value.add(item.id))
  }

  function clear() {
    selectedIds.value.clear()
  }

  return { selected, selectedIds, select, deselect, toggle, selectAll, clear }
}
```

---

## Vite Configuration

**File:** `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'
import path from 'path'

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },

  css: {
    postcss: {
      plugins: [tailwindcss, autoprefixer],
    },
  },

  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
  },
})
```

---

## Tailwind CSS v4

**File:** `frontend/src/assets/index.css`

```css
@import "tailwindcss";

/* Global styles */
body {
  @apply bg-gray-50;
}

/* Component-scoped styles */
.btn-primary {
  @apply px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white
         hover:bg-blue-700 transition-colors;
}

.btn-outline {
  @apply px-4 py-2 rounded-lg text-sm border border-gray-300 text-gray-700
         hover:bg-gray-50 transition-colors;
}

.btn-danger {
  @apply px-4 py-2 rounded-lg text-sm font-medium bg-red-600 text-white
         hover:bg-red-700 transition-colors;
}

.input-field {
  @apply w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
         focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none;
}
```

---

## Summary

The Vue 3 frontend:
- **Routes** 6 main pages via Vue Router
- **Manages** state with Pinia stores (auth, CRUD entities, UI state)
- **Communicates** with API via axios with JWT interceptor
- **Renders** components using Vue 3 Composition API + TypeScript
- **Styles** with Tailwind CSS v4 utility classes

Key patterns:
- **Composables:** Reusable logic (useSelection, useDropdown)
- **Stores:** Centralized reactive state with actions
- **Components:** Tree-based UI hierarchy
- **Router Guards:** Protect routes requiring authentication
- **API Client:** Typed HTTP requests with auto-refresh

---

**Next:** See [testing.md](08-testing.md) for test strategies and fixtures.
