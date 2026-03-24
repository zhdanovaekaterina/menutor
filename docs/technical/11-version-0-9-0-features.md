# v0.9.0 — Экран сводки блюд и план приготовления

**Дата:** 24.03.2026

Версия 0.9.0 добавляет экран сводки блюд (Meal Summary Screen) для удобного просмотра всех блюд в меню, их выбора и экспорта плана приготовления.

---

## Обзор функции

Экран сводки блюд позволяет:

1. **Просмотреть сводку меню** — все рецепты, вложенные рецепты и отдельные продукты в одном месте
2. **Выбрать приёмы пищи** — трёхуровневые чекбоксы для выбора всех/некоторых/ни одного приёма пищи
3. **Просмотреть масштабированные ингредиенты** — список ингредиентов каждого рецепта с учётом выбранных приёмов пищи
4. **Экспортировать план приготовления** — текстовый файл с форматом техкарты кухни
5. **Сгенерировать отфильтрованный список покупок** — на основе выбранных приёмов пищи и рецептов

---

## Архитектура

### Слой представления (Vue 3 компоненты)

**Директория:** `frontend/src/components/summary/` и `frontend/src/views/MealSummaryView.vue`

#### Основные компоненты

| Компонент | Файл | Назначение |
|-----------|------|-----------|
| **MealSummaryView** | `views/MealSummaryView.vue` | Основной экран сводки, контейнер для всех секций |
| **SummaryHeader** | `components/summary/SummaryHeader.vue` | Заголовок с названием меню и счётчиком блюд |
| **MealCard** | `components/summary/MealCard.vue` | Карточка основного рецепта с трёхуровневым чекбоксом и раскрывающимися приёмами пищи |
| **NestedRecipeCard** | `components/summary/NestedRecipeCard.vue` | Карточка подрецепта, аналогично MealCard |
| **StandaloneProductCard** | `components/summary/StandaloneProductCard.vue` | Карточка отдельного продукта (не входящего в рецепты) |
| **SummaryFooter** | `components/summary/SummaryFooter.vue` | Подвал с кнопкой формирования списка покупок |
| **SummaryExportModal** | `components/summary/SummaryExportModal.vue` | Модальное окно экспорта плана приготовления |
| **IngredientTree** | `components/summary/IngredientTree.vue` | Компонент визуализации древовидной структуры ингредиентов (для вложенных рецептов) |
| **SubRecipeNode** | `components/summary/SubRecipeNode.vue` | Узел древовидной структуры подрецепта |

#### MealCard компонент

**Входные параметры (props):**

```typescript
interface MealCardProps {
  recipe: Recipe              // Объект рецепта
  mealSlots: MealSlot[]       // Приёмы пищи, в которых используется рецепт
  selectedSlots: number[]     // ID выбранных приёмов пищи (для этого рецепта)
  familyMembers: FamilyMember[]  // Члены семьи для расчёта порций
}
```

**Вычисляемые свойства:**

- `totalPortions` — сумма порций по всем приёмам пищи
- `totalPieces` — сумма штук по всем приёмам пищи (если штучный режим)
- `checkboxState` — состояние чекбокса (0 = ничего, 1 = часть, 2 = все)
- `scaledIngredients` — масштабированные ингредиенты на основе выбранных приёмов пищи

**События (emits):**

```typescript
emit('update:selectedSlots', newSlots)  // Обновление выбранных приёмов пищи
```

**Логика:**

1. Отображает название рецепта и трёхуровневый чекбокс в заголовке
2. Показывает количество порций и штук (если штучный режим) в формате «X п. · Y шт»
3. При клике на чекбокс в заголовке — выбирает/отменяет все приёмы пищи
4. При развёртывании показывает список приёмов пищи как чипы с отдельными чекбоксами
5. Под чипсами отображает список ингредиентов, масштабированных для выбранных приёмов пищи
6. Порции округляются до 0.1

#### NestedRecipeCard компонент

Аналогичен MealCard, но для подрецептов с дополнительной информацией:

```typescript
interface NestedRecipeCardProps {
  nestedRecipe: NestedRecipe  // Подрецепт (Recipe используемый как ингредиент)
  mealSlots: MealSlot[]
  selectedSlots: number[]
  familyMembers: FamilyMember[]
  scalingMode: 'portions' | 'grams'  // Режим масштабирования подрецепта
}
```

**Особенности:**

- Показывает режим масштабирования (по порциям или по граммам)
- Развёртывает ингредиенты с учётом масштабирования вложенного рецепта
- Может быть отменена (исключена из списка покупок)

#### StandaloneProductCard компонент

**Входные параметры:**

```typescript
interface StandaloneProductCardProps {
  product: Product            // Объект продукта
  mealSlots: MealSlot[]       // Приёмы пищи с этим продуктом
  selectedSlots: number[]     // Выбранные приёмы пищи
}
```

**Особенности:**

- Отображает общее количество по всем приёмам пищи
- Показывает чипы приёмов пищи с индивидуальными количествами
- Эдит-бокс для изменения количества

#### SummaryExportModal компонент

**Входные параметры:**

```typescript
interface SummaryExportModalProps {
  isOpen: boolean            // Видимость модали
  mealPlanText: string       // Текст плана приготовления
}
```

**События:**

```typescript
emit('close')               // Закрыть модаль
emit('copy')               // Скопировать текст
emit('download')           // Скачать файл
```

**Логика:**

1. Отображает текст плана в читаемом виде (техкарта кухни)
2. Кнопка «Копировать» копирует текст в буфер обмена с уведомлением
3. Кнопка «Скачать» генерирует файл `meal_plan.txt` и инициирует скачивание
4. Модаль закрывается кликом вне области или кнопкой закрытия

---

### Слой приложения (Use Cases)

**Директория:** `backend/application/use_cases/`

#### GenerateMealSummary

**Файл:** `backend/application/use_cases/generate_meal_summary.py`

**Назначение:** Собрать всю информацию о блюдах меню и подготовить структурированные данные для экрана сводки.

**Входные параметры:**

```python
@dataclass
class GenerateMealSummaryRequest:
    user_id: UserId
    menu_id: MenuId
```

**Выходные данные:**

```python
@dataclass
class MealSummaryResponse:
    menu_id: MenuId
    menu_name: str
    recipes: List[MealSummaryRecipe]  # Основные рецепты с приёмами пищи
    nested_recipes: List[MealSummaryNestedRecipe]  # Подрецепты
    standalone_products: List[MealSummaryProduct]  # Отдельные продукты
```

**Структура MealSummaryRecipe:**

```python
@dataclass
class MealSummaryRecipe:
    recipe_id: RecipeId
    recipe_name: str
    total_portions: Quantity
    total_pieces: Optional[int]  # None если не штучный режим
    meal_slots: List[MealSlotDetail]  # Приёмы пищи
```

**Логика:**

1. Получить меню с all slots
2. Для каждого slot с рецептом:
   - Извлечь рецепт
   - Сгруппировать по recipe_id
   - Собрать все meal_slot_details
   - Рассчитать total portions и pieces (если штучный режим)
   - Рассчитать масштабированные ингредиенты для каждого slot
3. Аналогично для подрецептов и отдельных продуктов
4. Вернуть структурированный ответ

#### GenerateFilteredShoppingList

**Файл:** `backend/application/use_cases/generate_filtered_shopping_list.py`

**Назначение:** Генерировать список покупок на основе выбранных приёмов пищи, рецептов и подрецептов из экрана сводки.

**Входные параметры:**

```python
@dataclass
class GenerateFilteredShoppingListRequest:
    user_id: UserId
    menu_id: MenuId
    selected_slot_ids: List[MealSlotId]  # Выбранные приёмы пищи
    excluded_nested_recipe_ids: List[RecipeId] = field(default_factory=list)  # Исключённые подрецепты
```

**Логика:**

1. Получить меню
2. Отфильтровать slots по selected_slot_ids
3. Для каждого выбранного slot:
   - Если это рецепт — развернуть его ингредиенты, исключив excluded_nested_recipe_ids
   - Если это продукт — добавить в список
4. Агрегировать по продуктам и рассчитать суммы
5. Вернуть полный список покупок

---

### API слой

**Директория:** `backend/api/routers/`

#### Эндпоинт GET /menus/{id}/summary

**Файл:** `backend/api/routers/menus.py`

```python
@router.get("/{menu_id}/summary")
async def get_meal_summary(
    menu_id: MenuId,
    current_user: User = Depends(get_current_user),
    container = Depends(get_container)
) -> MealSummaryResponse:
    """
    Получить сводку блюд меню.

    Параметры:
    - menu_id: ID меню

    Возвращает:
    - Структурированная сводка с рецептами, подрецептами и продуктами
    """
    use_case = container.generate_meal_summary()
    return await use_case(GenerateMealSummaryRequest(
        user_id=current_user.id,
        menu_id=menu_id
    ))
```

**Статус коды:**

- `200` — успешно
- `404` — меню не найдено
- `403` — доступ запрещён (меню другого пользователя)

#### Эндпоинт POST /menus/{id}/shopping-list/filtered

**Файл:** `backend/api/routers/menus.py`

```python
@router.post("/{menu_id}/shopping-list/filtered")
async def generate_filtered_shopping_list(
    menu_id: MenuId,
    request: GenerateFilteredShoppingListRequest,
    current_user: User = Depends(get_current_user),
    container = Depends(get_container)
) -> ShoppingListResponse:
    """
    Сгенерировать отфильтрованный список покупок.

    Body:
    - selected_slot_ids: List[int] — ID выбранных приёмов пищи
    - excluded_nested_recipe_ids: List[int] — ID исключённых подрецептов

    Возвращает:
    - Список покупок (ShoppingListResponse)
    """
    use_case = container.generate_filtered_shopping_list()
    request.user_id = current_user.id
    return await use_case(request)
```

**Pydantic схемы:**

```python
class MealSummaryRecipeResponse(BaseModel):
    recipe_id: int
    recipe_name: str
    total_portions: float
    total_pieces: Optional[int]
    meal_slots: List[MealSlotDetailResponse]

class MealSummaryResponse(BaseModel):
    menu_id: int
    menu_name: str
    recipes: List[MealSummaryRecipeResponse]
    nested_recipes: List[NestedRecipeResponse]
    standalone_products: List[ProductResponse]

class FilteredShoppingListRequest(BaseModel):
    selected_slot_ids: List[int]
    excluded_nested_recipe_ids: List[int] = Field(default_factory=list)
```

---

## Утилиты экспорта

### exportSummaryTxt.ts

**Файл:** `frontend/src/utils/exportSummaryTxt.ts`

**Назначение:** Формировать текст плана приготовления в формате техкарты кухни.

**Основная функция:**

```typescript
export function generateMealPlanText(
  recipes: MealSummaryRecipe[],
  nestedRecipes: MealSummaryNestedRecipe[],
  standaloneProducts: MealSummaryProduct[],
  selectedSlots: Record<number, boolean>  // Выбранные приёмы пищи
): string
```

**Форматирование:**

1. **РЕЦЕПТЫ** — основные блюда
   - Для каждого рецепта: день недели, приём пищи, название рецепта
   - Количество порций и штук (если штучный режим)
   - Список ингредиентов с масштабированными количествами

2. **ВЛОЖЕННЫЕ РЕЦЕПТЫ** — подрецепты
   - Название подрецепта
   - Режим масштабирования (по порциям / по граммам)
   - Список ингредиентов

3. **ОТДЕЛЬНЫЕ ПРОДУКТЫ** — не входящие в рецепты
   - День, приём пищи, название продукта
   - Количество

**Пример вывода:**

```
РЕЦЕПТЫ
═══════════════════════════════════════

Понедельник - Завтрак: Блины (2 порц. · 8 шт)
  Ингредиенты:
  • Мука: 200 г
  • Молоко: 400 мл

ВЛОЖЕННЫЕ РЕЦЕПТЫ
═══════════════════════════════════════

Дрожжевое тесто (0.5 кг)
  Ингредиенты:
  • Мука: 250 г

ОТДЕЛЬНЫЕ ПРОДУКТЫ
═══════════════════════════════════════

Понедельник - Завтрак: Хлеб (300 г)
```

---

## Логика выбора приёмов пищи

### Трёхуровневый чекбокс

**Состояния:**

- **0 (ничего не выбрано)** — пустой квадрат
- **1 (часть выбрана)** — квадрат с минусом
- **2 (все выбрано)** — квадрат с галочкой

**Вычисление состояния:**

```typescript
function getCheckboxState(totalSlots: number, selectedSlots: number[]): CheckboxState {
  const selected = selectedSlots.length
  if (selected === 0) return 0
  if (selected === totalSlots) return 2
  return 1
}
```

**Клик на чекбокс:**

- Если состояние 0 или 1 → выбрать все (состояние 2)
- Если состояние 2 → отменить все (состояние 0)

### Масштабирование ингредиентов

**Логика:**

1. Для каждого приёма пищи рассчитать коэффициент масштабирования:
   - Для рецептов: `quantities.portions / recipe.default_portions`
   - Для подрецептов в режиме порций: аналогично
   - Для подрецептов в режиме граммов: `quantities.weight / recipe.weight`

2. Для каждого ингредиента масштабировать:
   - Количество: `ingredient.quantity * scaling_factor`
   - Единицу оставить как есть

3. Для выбранных приёмов пищи агрегировать ингредиенты:
   - Суммировать количества по одинаковым продуктам
   - Преобразовать единицы (г → кг, мл → л и т.д.)
   - Округлить до 0.1

**Округление:**

```typescript
function roundQuantity(value: number, decimals: number = 1): number {
  return Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals)
}
```

---

## Маршруты и навигация

### Vue Router

**Файл:** `frontend/src/router/index.ts`

```typescript
{
  path: '/meal-summary/:menuId',
  component: () => import('@/views/MealSummaryView.vue'),
  meta: { requiresAuth: true },
  props: true  // Передать menuId как prop
}
```

**Навигация из Планировщика:**

```typescript
router.push({
  name: 'MealSummary',
  params: { menuId: selectedMenu.id }
})
```

---

## Интеграция с существующими сущностями

### Menu, MenuSlot, Recipe, Product

**Использование в сводке:**

- `Menu` — название, владелец (user_id)
- `MenuSlot` — приём пищи, день, название дня, тип (breakfast/lunch/dinner)
- `Recipe` — ингредиенты, масштабирование (default_portions, total_weight)
- `Product` — единицы (recipe_unit, purchase_unit, conversion_coefficient)

### Вложенные рецепты (Recipe as Ingredient)

**Схема:**

```
Recipe A
  ├─ Ingredient 1 (Product)
  ├─ Ingredient 2 (Recipe B) → scaling_mode: "portions" | "grams"
  │   └─ Ingredient 2.1 (Product)
  └─ Ingredient 3 (Product)
```

**Развёртывание:**

```
Recipe A (в меню) → для списка покупок развернуть рекурсивно:
  → Ingredient 1 (Product)
  → Recipe B ингредиенты:
    → Ingredient 2.1 (Product)
  → Ingredient 3 (Product)
```

---

## Тестирование

### Unit тесты

**Директория:** `tests/unit/application/use_cases/`

#### test_generate_meal_summary.py

```python
async def test_generate_meal_summary_with_recipes():
    """Тест сбора сводки с основными рецептами"""
    use_case = GenerateMealSummary(mock_repo)
    response = await use_case(GenerateMealSummaryRequest(...))
    assert len(response.recipes) > 0
    assert response.recipes[0].total_portions > 0

async def test_meal_summary_includes_nested_recipes():
    """Тест включения подрецептов в сводку"""
    ...

async def test_meal_summary_standalone_products():
    """Тест включения отдельных продуктов"""
    ...
```

#### test_generate_filtered_shopping_list.py

```python
async def test_filtered_shopping_list_selected_slots():
    """Тест фильтрации по выбранным приёмам пищи"""
    ...

async def test_filtered_shopping_list_excluded_nested_recipes():
    """Тест исключения подрецептов из списка"""
    ...
```

### API тесты

**Директория:** `tests/unit/api/`

#### test_meal_summary_endpoint.py

```python
def test_get_meal_summary_success(test_client):
    """Тест GET /menus/{id}/summary"""
    response = test_client.get(f"/api/menus/{menu_id}/summary")
    assert response.status_code == 200
    assert "recipes" in response.json()

def test_get_meal_summary_unauthorized(test_client):
    """Тест доступа без аутентификации"""
    ...

def test_get_meal_summary_not_found(test_client):
    """Тест несуществующего меню"""
    ...
```

---

## Производительность

### Оптимизации

1. **Ленивая загрузка ингредиентов** — раскрывающиеся чипы приёмов пищи загружают ингредиенты только при раскрытии
2. **Кеширование на фронтенде** — использование computed properties в Vue для кеширования масштабированных ингредиентов
3. **Пагинация в бэкенде** — для больших меню может быть добавлена пагинация при вызове summary

### Сложность

- **Время загрузки сводки:** O(n) где n — количество slots в меню
- **Время масштабирования ингредиентов:** O(m × k) где m — количество слотов, k — среднее количество ингредиентов в рецепте
- **Память:** O(n × k) для хранения масштабированных ингредиентов

---

## Совместимость

### Вложенные рецепты

Сводка полностью поддерживает вложенные рецепты (v0.6.0):

- Показывает подрецепты в отдельной секции
- Развёртывает ингредиенты подрецептов при экспорте плана
- Поддерживает оба режима масштабирования (по порциям и по граммам)

### Штучный режим

Сводка полностью поддерживает штучный режим рецептов (v0.7.0):

- Показывает количество штук в формате «X п. · Y шт»
- Включает информацию о штуках в экспортированный план
- Корректно масштабирует штуки при изменении количества приёмов пищи

### Сохранённые списки

Интеграция с v0.8.0 (сохранённые списки):

- Отфильтрованный список покупок может быть сохранён как новый список
- Связь между списком и исходным меню/сводкой сохраняется

---

## Будущие улучшения

1. **Печать плана** — оптимизированный макет для печати (без белых пространств)
2. **Правка ингредиентов в сводке** — изменение количества прямо на экране сводки
3. **Фильтры по категориям** — показать только рецепты определённой категории
4. **Импорт плана** — загрузить план из файла для использования в меню
5. **Интеграция с календарём** — привязка плана к дате в дневнике питания

---

**История версий:**

- **v0.9.0** (24.03.2026) — Экран сводки блюд, экспорт плана приготовления, отфильтрованный список покупок

