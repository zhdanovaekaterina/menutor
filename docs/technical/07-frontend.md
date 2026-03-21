# Фронтенд — Vue 3 + TypeScript + Pinia

**Расположение:** `frontend/src/`

Фронтенд является Vue 3 SPA с TypeScript, управлением состоянием Pinia и Tailwind CSS v4. Он отражает архитектуру бэкенда: представления соответствуют маршрутам, хранилища управляют состоянием, а API клиент обрабатывает HTTP связь.

---

## Структура проекта

```
frontend/src/
├── main.ts                        # Инициализация Vue приложения
├── App.vue                        # Корневой компонент разметки
├── router/
│   └── index.ts                   # Конфигурация Vue Router (6 маршрутов + вложенные настройки)
├── stores/                        # Pinia хранилища (управление состоянием)
│   ├── auth.ts                    # Пользователь, токены, логин/логаут
│   ├── recipes.ts                 # Состояние рецептов и операции CRUD
│   ├── products.ts                # Состояние продуктов и операции CRUD
│   ├── menus.ts                   # Состояние меню и слотов
│   ├── family.ts                  # Состояние членов семьи
│   ├── categories.ts              # Состояние категорий продуктов/рецептов
│   ├── shoppingList.ts            # Элементы списка покупок, отслеживание стоимости
│   ├── toast.ts                   # Очередь всплывающих уведомлений
│   └── crud-factory.ts            # Переиспользуемый генератор CRUD хранилища
├── api/
│   ├── client.ts                  # Экземпляр axios с JWT перехватчиком
│   ├── auth.ts                    # Вызовы API аутентификации
│   └── types.ts                   # TypeScript интерфейсы (соответствуют Pydantic)
├── views/                         # Компоненты уровня страницы
│   ├── AuthView.vue               # Логин/регистрация
│   ├── MenuPlannerView.vue        # Планировщик меню на 7 дней
│   ├── ShoppingListView.vue       # Страница списка покупок
│   ├── RecipeListView.vue         # Страница управления рецептами
│   ├── ProductListView.vue        # Страница управления продуктами
│   └── SettingsView.vue           # Контейнер настроек
├── components/                    # Переиспользуемые UI компоненты
│   ├── layout/                    # Компоненты разметки (AppSidebar, MobileBottomNav)
│   ├── planner/                   # Планировщик (PlannerGrid, GridCell, SourcePanel)
│   ├── shopping/                  # Покупки (ShoppingTable, ShoppingSummary)
│   ├── recipes/                   # Рецепты (RecipeTable, RecipeForm)
│   ├── products/                  # Продукты (ProductTable, ProductForm)
│   ├── settings/                  # Настройки (FamilyPanel, CategoryPanel)
│   └── ui/                        # Примитивные UI (ConfirmDialog, ToastNotification, и т.д.)
├── composables/                   # Переиспользуемые функции Vue 3 composition
│   ├── useSelection.ts            # Выбор нескольких строк
│   ├── useDropdown.ts             # Состояние открытия/закрытия выпадающего меню
│   ├── useCategoryFilter.ts       # Логика фильтрации по категориям
│   ├── useContextMenu.ts          # Контекстное меню по клику правой кнопки
│   ├── useCrudView.ts             # Управление состоянием CRUD форм (создание, редактирование, удаление)
│   ├── useSortableTable.ts        # Сортировка таблиц и алфавитное упорядочивание
│   ├── useTabbedFilter.ts         # Фильтрация с несколькими вкладками
│   └── useFileDownload.ts         # Утилита скачивания файлов/blob
├── utils/
│   ├── units.ts                   # Преобразование единиц, вспомогательные функции форматирования
│   ├── api.ts                     # Обработка ошибок ответов API
│   ├── exporters.ts               # Экспортеры (PDF, JSON, CSV, TXT) для списка покупок и меню
│   └── fileDownload.ts            # Скачивание файлов на клиентской стороне
├── assets/
│   └── index.css                  # Tailwind CSS, глобальные стили
└── vite.config.ts                 # Конфигурация Vite + плагин Tailwind
```

---

## Инициализация

**Файл:** `frontend/src/main.ts`

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/index.css'

const app = createApp(App)

app.use(createPinia())  // Управление состоянием
app.use(router)         // Маршрутизация

app.mount('#app')
```

---

## Корневая разметка

**Файл:** `frontend/src/App.vue`

```vue
<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Боковая навигация -->
    <AppSidebar />

    <!-- Основное содержимое -->
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

**Файл:** `frontend/src/router/index.ts`

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

// Глобальная защита маршрутов: проверка аутентификации
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

## Pinia хранилища

### Хранилище аутентификации

**Файл:** `frontend/src/stores/auth.ts`

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

  // ─── Вычисляемые свойства ───────────────────────────────────────────

  const isAuthenticated = computed(() => !!accessToken.value)

  // ─── Действия ─────────────────────────────────────────────

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

### Хранилище рецептов (CRUD фабрика)

**Файл:** `frontend/src/stores/recipes.ts`

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

### Другие хранилища

- `products.ts` — CRUD продукты
- `menus.ts` — Управление меню и слотами
- `family.ts` — CRUD члены семьи
- `categories.ts` — CRUD категории
- `shoppingList.ts` — Состояние списка покупок (элементы, общая стоимость, отслеживание покупок)
- `toast.ts` — Очередь всплывающих уведомлений

---

## API клиент

**Файл:** `frontend/src/api/client.ts`

```typescript
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

const client: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Перехватчик запроса: добавление JWT токена
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// Перехватчик ответа: обработка 401 (автоматическое обновление)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    const originalRequest = error.config

    if (error.response?.status === 401 && auth.refreshToken) {
      try {
        await auth.refreshAccessToken()
        // Повтор исходного запроса с новым токеном
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

// Типизированные обертки API
export const getRecipes = (params?: { category_id?: number }) =>
  client.get<Recipe[]>('/recipes', { params }).then(r => r.data)

export const createRecipe = (data: RecipeCreate) =>
  client.post<Recipe>('/recipes', data).then(r => r.data)

export const updateRecipe = (id: number, data: RecipeUpdate) =>
  client.put<Recipe>(`/recipes/${id}`, data).then(r => r.data)

export const deleteRecipe = (id: number) =>
  client.delete(`/recipes/${id}`).then(r => r.data)

// ... аналогично для продуктов, меню и т.д.
```

**Файл:** `frontend/src/api/types.ts`

TypeScript интерфейсы, соответствующие схемам Pydantic:

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

// ... аналогично для Product, Menu, ShoppingList и т.д.
```

---

## Компоненты

### Компонент RecipeForm

**Файл:** `frontend/src/components/recipes/RecipeForm.vue`

```vue
<template>
  <form @submit.prevent="submit" class="space-y-4">
    <!-- Название -->
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

    <!-- Категория & Порции -->
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

    <!-- Ингредиенты -->
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

    <!-- Шаги -->
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

    <!-- Действия -->
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
    // Ошибка обработана хранилищем
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

### Компонент MenuPlannerView

Сложный компонент с:
- Сеткой 7×3 с drag-drop
- Панель источников рецептов/продуктов
- Список сохраненных меню
- Отображение семьи
- Генерация списка покупок

Смотрите `frontend/src/views/MenuPlannerView.vue` для полной реализации.

---

## Composables

### useSelection

**Файл:** `frontend/src/composables/useSelection.ts`

Управляет выбором нескольких строк в таблицах:

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

### useSortableTable

**Файл:** `frontend/src/composables/useSortableTable.ts`

Управляет сортировкой таблиц по колонкам с автоматическим алфавитным упорядочиванием по названиям. Поддерживает возрастающий и убывающий порядок.

### useCrudView

**Файл:** `frontend/src/composables/useCrudView.ts`

Управляет состоянием CRUD форм: открытие/закрытие формы редактирования, сохранение, удаление с подтверждением. Переиспользуется в представлениях рецептов, продуктов и других сущностей.

### useTabbedFilter

**Файл:** `frontend/src/composables/useTabbedFilter.ts`

Фильтрация со множественными вкладками (например, вкладки "Продукты" и "Рецепты" в окне выбора ингредиентов) с поддержкой поиска и категорий.

---

## Утилиты экспорта

### Экспортеры данных

**Файл:** `frontend/src/utils/exporters.ts`

Экспортеры для списка покупок и меню поддерживают несколько форматов:

- **TXT экспортер** — текстовый файл с простым форматированием
- **CSV экспортер** — табличный формат для электронных таблиц
- **JSON экспортер** — структурированный формат с полной информацией (для списка покупок: закупочное и рецептурное количество, стоимость)
- **PDF экспортер** — переносимый формат для печати (использует reportlab для генерации на клиентской стороне для меню и списка покупок)

Все экспортеры работают на клиентской стороне (без обращения к серверу) и автоматически скачивают файлы через функцию `downloadFile()`.

**Пример использования:**

```typescript
import { exportShoppingListToPDF, exportShoppingListToJSON } from '@/utils/exporters'
import { useFileDownload } from '@/composables/useFileDownload'

const { downloadFile } = useFileDownload()

// Экспорт в PDF
const pdfBlob = exportShoppingListToPDF(shoppingListItems)
downloadFile(pdfBlob, 'shopping_list.pdf')

// Экспорт в JSON
const jsonBlob = exportShoppingListToJSON(shoppingListItems)
downloadFile(jsonBlob, 'shopping_list.json')
```

---

## Конфигурация Vite

**Файл:** `frontend/vite.config.ts`

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

**Файл:** `frontend/src/assets/index.css`

```css
@import "tailwindcss";

/* Глобальные стили */
body {
  @apply bg-gray-50;
}

/* Стили компонентов */
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

## Резюме

Vue 3 фронтенд:
- **Маршруты** 6 основных страниц через Vue Router
- **Управляет** состоянием с хранилищами Pinia (auth, CRUD сущности, состояние UI)
- **Взаимодействует** с API через axios с перехватчиком JWT
- **Отрисовывает** компоненты используя Vue 3 Composition API + TypeScript
- **Стилизирует** с утилит Tailwind CSS v4

Ключевые паттерны:
- **Composables:** Переиспользуемая логика (useSelection, useSortableTable, useCrudView, useTabbedFilter, useDropdown)
- **Exporters:** Экспорт данных на клиентской стороне (PDF, JSON, CSV, TXT)
- **Stores:** Централизованное реактивное состояние с действиями
- **Components:** Иерархия UI на основе дерева
- **Router Guards:** Защита маршрутов требующих аутентификацию
- **API Client:** Типизированные HTTP запросы с автоматическим обновлением

---

**Далее:** См. [testing.md](08-testing.md) для стратегий тестирования и фикстур.
