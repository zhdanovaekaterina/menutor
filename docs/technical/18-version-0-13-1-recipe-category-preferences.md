# Версия 0.13.1 — Расширение системы пищевых предпочтений: категории рецептов

Документация расширений функций версии 0.13.1: добавлена поддержка выбора категорий рецептов при настройке пищевых предпочтений. Теперь пользователи могут ограничивать применение предпочтения к определённым типам блюд (Суп, Десерт, Напиток и т.п.). Система рекурсивно проверяет категории рецептов, включая вложенные рецепты, с защитой от циклических зависимостей.

## Обзор

Расширение позволяет уточнить применение пищевых предпочтений, связав их с категориями рецептов. Например, можно запретить молочные продукты только в супах, или разрешить только определённые категории для завтраков.

**Новые возможности:**
- Выбор одной или нескольких категорий рецептов при создании/редактировании предпочтения
- Поддержка категорий рецептов для обоих типов предпочтений (По категориям и Аллергия)
- Рекурсивная проверка категорий рецептов в вложенных рецептах
- Независимая AND-логика: предпочтение применяется только если выполнены оба условия (категория продуктов И категория рецепта)

## Доменный слой

### Расширение сущности Preference

**Файл:** `backend/domain/entities/preference.py`

```python
@dataclass
class Preference:
    id: PreferenceId
    name: str
    type: PreferenceType              # CATEGORY_BASED или ALLERGY
    mode: PreferenceMode              # BLOCKED или ALLOWED
    category_ids: list[ProductCategoryId] = field(default_factory=list)
    product_ids: list[ProductId] = field(default_factory=list)
    recipe_category_ids: list[RecipeCategoryId] = field(default_factory=list)  # НОВОЕ
    user_id: UserId = field(default=UserId(0))
```

**Новое поле:**
- `recipe_category_ids` — список ID категорий рецептов, к которым применяется предпочтение. Если пусто, предпочтение применяется ко всем рецептам независимо от их категории.

**Валидация (в `__post_init__`):**
- BR-1: Название не может быть пустым (только пробелы)
- BR-2: Если тип ALLERGY, режим обязательно BLOCKED
- BR-2a: Если тип CATEGORY_BASED, product_ids должны быть пусты
- **BR-10 (новое)**: Если тип ALLERGY и recipe_category_ids не пусто, то обеспечена валидация (аллергия может быть привязана к категориям рецептов)

### Расширение доменного сервиса PreferenceMatcher

**Файл:** `backend/domain/services/preference_matcher.py`

Сервис расширен методом для рекурсивного сбора категорий рецептов.

#### Новый метод помощника

**`_resolve_all_recipe_category_ids(recipe, visited)`**
- Рекурсивно собирает категории рецептов из основного рецепта и всех его подрецептов
- Использует `visited` set для предотвращения бесконечных циклов
- Возвращает список всех найденных ID категорий рецептов (без дублей)
- Логика:
  1. Проверяет, находится ли рецепт уже в `visited` (если да — возвращает пустой список)
  2. Добавляет рецепт в `visited`
  3. Собирает категорию текущего рецепта (если она не 0)
  4. Для каждого ингредиента-подрецепта рекурсивно вызывает метод
  5. Возвращает агрегированный список

```python
def _resolve_all_recipe_category_ids(self, recipe: Recipe, visited: set) -> list[RecipeCategoryId]:
    """Recursively resolve all recipe category IDs from the recipe and its sub-recipes."""
    if recipe.id in visited:
        return []
    
    visited.add(recipe.id)
    category_ids: list[RecipeCategoryId] = []
    
    if recipe.category_id != RecipeCategoryId(0):
        category_ids.append(recipe.category_id)
    
    for ingredient in recipe.ingredients:
        if ingredient.is_recipe:
            sub_recipe = self._recipe_repo.get_by_id(ingredient.recipe_id)
            if sub_recipe is not None:
                category_ids.extend(self._resolve_all_recipe_category_ids(sub_recipe, visited))
    
    return category_ids
```

#### Обновленные методы проверки

**`_matches_allergy(product_ids, category_ids, preference, recipe_category_ids)`** (сигнатура расширена)

- Проверяет по продуктам и категориям продуктов как раньше
- **Новая логика по категориям рецептов:**
  - Если `preference.recipe_category_ids` не пусто:
    - Если пересечение `recipe_category_ids` и `preference.recipe_category_ids` пусто — рецепт не подходит под категории (возвращает `True`, т.е. совместим по ингредиентам, но может быть не совместим по категории)
    - Если пересечение не пусто AND есть пересечение с запрещёнными продуктами/категориями — возвращает `False`
  - Если `preference.recipe_category_ids` пусто — применяется к любому рецепту

**`_matches_blocked(category_ids, preference, recipe_category_ids)`** (сигнатура расширена)

- Проверяет категории продуктов как раньше
- **Новая логика по категориям рецептов:**
  - Если `preference.recipe_category_ids` не пусто:
    - Если пересечение `recipe_category_ids` и `preference.recipe_category_ids` пусто — рецепт из другой категории, предпочтение не применяется (возвращает `True`)
    - Если пересечение не пусто AND есть пересечение с запрещёнными категориями продуктов — возвращает `False`
  - Если `preference.recipe_category_ids` пусто — применяется к любому рецепту

**`_matches_allowed(product_ids, category_ids, preference, has_uncategorized, recipe_category_ids)`** (сигнатура расширена)

- Проверяет категории продуктов как раньше
- **Новая логика по категориям рецептов:**
  - Если `preference.recipe_category_ids` не пусто:
    - Если пересечение `recipe_category_ids` и `preference.recipe_category_ids` пусто — рецепт из другой категории, не соответствует разрешённому списку (возвращает `False`)
    - Если пересечение не пусто — проверяет категории продуктов как раньше
  - Если `preference.recipe_category_ids` пусто — применяется к любому рецепту (категория рецепта не ограничена)

#### Обновленный основной метод

```python
def matches_preference(self, recipe: Recipe, preference: Preference) -> bool:
    """Return True if the recipe satisfies (is compatible with) the given preference."""
    all_product_ids = self._resolve_all_product_ids(recipe, set())
    all_category_ids, has_uncategorized = self._resolve_category_ids(all_product_ids)
    all_recipe_category_ids = self._resolve_all_recipe_category_ids(recipe, set())  # НОВОЕ
    
    if preference.type == PreferenceType.ALLERGY:
        return self._matches_allergy(all_product_ids, all_category_ids, preference, all_recipe_category_ids)
    
    if preference.mode == PreferenceMode.BLOCKED:
        return self._matches_blocked(all_category_ids, preference, all_recipe_category_ids)
    
    # ALLOWED mode
    return self._matches_allowed(all_product_ids, all_category_ids, preference, has_uncategorized, all_recipe_category_ids)
```

## Слой приложения

### Расширение PreferenceData

**Файл:** `backend/application/use_cases/manage_preference.py`

```python
@dataclass
class PreferenceData:
    name: str
    type: PreferenceType
    mode: PreferenceMode
    category_ids: list[ProductCategoryId] = field(default_factory=list)
    product_ids: list[ProductId] = field(default_factory=list)
    recipe_category_ids: list[RecipeCategoryId] = field(default_factory=list)  # НОВОЕ
```

**Новое поле:**
- `recipe_category_ids` — список ID категорий рецептов из пользовательского ввода

### Обновленные Use Cases

**CreatePreference** и **UpdatePreference** передают `recipe_category_ids` при создании и обновлении:

```python
preference = Preference(
    id=PreferenceId(...),
    name=data.name,
    type=data.type,
    mode=data.mode,
    category_ids=data.category_ids,
    product_ids=data.product_ids,
    recipe_category_ids=data.recipe_category_ids,  # НОВОЕ
    user_id=user_id,
)
```

## Слой инфраструктуры

### Новая таблица базы данных

**Миграция:** `c2d3e4f5a6b7`

```sql
CREATE TABLE preference_recipe_categories (
    preference_id INTEGER NOT NULL,
    recipe_category_id INTEGER NOT NULL,
    PRIMARY KEY (preference_id, recipe_category_id),
    FOREIGN KEY (preference_id) REFERENCES preferences(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_category_id) REFERENCES recipe_categories(id) ON DELETE CASCADE
);
```

**Назначение:**
- Многие-ко-многим связь между предпочтениями и категориями рецептов
- CASCADE удаление: при удалении предпочтения или категории удаляются все связанные записи

### Обновленная ORM модель

**Файл:** `backend/infrastructure/orm/models.py`

```python
class PreferenceRecipeCategoryRow(Base):
    __tablename__ = "preference_recipe_categories"
    
    preference_id: Mapped[int] = mapped_column(
        ForeignKey("preferences.id", ondelete="CASCADE"), primary_key=True
    )
    recipe_category_id: Mapped[int] = mapped_column(
        ForeignKey("recipe_categories.id", ondelete="CASCADE"), primary_key=True
    )
```

### Обновленный репозиторий

**Файл:** `backend/infrastructure/repositories/sqlalchemy_preference_repository.py`

#### Метод `_make_new_row`

```python
def _make_new_row(self, preference: Preference) -> PreferenceRow:
    row = PreferenceRow(
        name=preference.name,
        type=preference.type.value,
        mode=preference.mode.value,
        user_id=preference.user_id,
    )
    # Добавление категорий продуктов
    for cat_id in preference.category_ids:
        pcat = PreferenceProductCategoryRow(product_category_id=cat_id)
        row.product_categories.append(pcat)
    
    # Добавление продуктов (только для ALLERGY)
    for prod_id in preference.product_ids:
        pprod = PreferenceProductRow(product_id=prod_id)
        row.products.append(pprod)
    
    # НОВОЕ: Добавление категорий рецептов
    for rec_cat_id in preference.recipe_category_ids:
        prcat = PreferenceRecipeCategoryRow(recipe_category_id=rec_cat_id)
        row.recipe_categories.append(prcat)
    
    return row
```

#### Метод `_update_row`

```python
def _update_row(self, row: PreferenceRow, preference: Preference) -> None:
    row.name = preference.name
    row.type = preference.type.value
    row.mode = preference.mode.value
    
    # Очистка и переиспользование категорий продуктов
    row.product_categories.clear()
    for cat_id in preference.category_ids:
        pcat = PreferenceProductCategoryRow(product_category_id=cat_id)
        row.product_categories.append(pcat)
    
    # Очистка и переиспользование продуктов
    row.products.clear()
    for prod_id in preference.product_ids:
        pprod = PreferenceProductRow(product_id=prod_id)
        row.products.append(pprod)
    
    # НОВОЕ: Очистка и переиспользование категорий рецептов
    row.recipe_categories.clear()
    for rec_cat_id in preference.recipe_category_ids:
        prcat = PreferenceRecipeCategoryRow(recipe_category_id=rec_cat_id)
        row.recipe_categories.append(prcat)
```

#### Метод `_row_to_entity`

```python
def _row_to_entity(self, row: PreferenceRow) -> Preference:
    category_ids = [
        ProductCategoryId(pcat.product_category_id)
        for pcat in row.product_categories
    ]
    product_ids = [ProductId(pprod.product_id) for pprod in row.products]
    
    # НОВОЕ: Сбор категорий рецептов из таблицы
    recipe_category_ids = [
        RecipeCategoryId(prcat.recipe_category_id)
        for prcat in row.recipe_categories
    ]
    
    return Preference(
        id=PreferenceId(row.id),
        name=row.name,
        type=PreferenceType(row.type),
        mode=PreferenceMode(row.mode),
        category_ids=category_ids,
        product_ids=product_ids,
        recipe_category_ids=recipe_category_ids,  # НОВОЕ
        user_id=UserId(row.user_id),
    )
```

## Слой API

### Расширение схем Pydantic

**Файл:** `backend/api/schemas/preference.py`

```python
class PreferenceCreate(BaseModel):
    name: str
    type: PreferenceType
    mode: PreferenceMode
    category_ids: list[int] = []
    recipe_category_ids: list[int] = []  # НОВОЕ
    product_ids: list[int] = []

class PreferenceResponse(BaseModel):
    id: int
    name: str
    type: PreferenceType
    mode: PreferenceMode
    category_ids: list[int]
    recipe_category_ids: list[int]  # НОВОЕ
    product_ids: list[int]

    model_config = ConfigDict(from_attributes=True)
```

### Обновленные конвертеры

**Файл:** `backend/api/converters.py`

```python
def preference_to_response(preference: Preference) -> PreferenceResponse:
    return PreferenceResponse(
        id=preference.id,
        name=preference.name,
        type=preference.type,
        mode=preference.mode,
        category_ids=list(preference.category_ids),
        recipe_category_ids=list(preference.recipe_category_ids),  # НОВОЕ
        product_ids=list(preference.product_ids),
    )

def schema_to_preference_data(schema: PreferenceCreate) -> PreferenceData:
    return PreferenceData(
        name=schema.name,
        type=schema.type,
        mode=schema.mode,
        category_ids=[ProductCategoryId(cid) for cid in schema.category_ids],
        product_ids=[ProductId(pid) for pid in schema.product_ids],
        recipe_category_ids=[RecipeCategoryId(rcid) for rcid in schema.recipe_category_ids],  # НОВОЕ
    )
```

## Фронтенд

### Расширение TypeScript интерфейсов

**Файл:** `frontend/src/api/types.ts`

```typescript
export interface PreferenceCreate {
  name: string;
  type: "CATEGORY_BASED" | "ALLERGY";
  mode: "BLOCKED" | "ALLOWED";
  category_ids: number[];
  recipe_category_ids: number[];  // НОВОЕ
  product_ids: number[];
}

export interface Preference {
  id: number;
  name: string;
  type: "CATEGORY_BASED" | "ALLERGY";
  mode: "BLOCKED" | "ALLOWED";
  category_ids: number[];
  recipe_category_ids: number[];  // НОВОЕ
  product_ids: number[];
}
```

### Обновленный компонент PreferenceForm

**Файл:** `frontend/src/components/settings/PreferenceForm.vue`

**Добавлены:**
- При монтировании загружаются категории рецептов: `categoryStore.load('recipe')`
- Новая секция "Категории рецептов" после "Категории продуктов" и перед "Продукты"
- Чекбоксы для выбора категорий рецептов
- Отображается для обоих типов предпочтений (CATEGORY_BASED и ALLERGY)

```vue
<template>
  <!-- Существующий контент для названия, типа, режима, категорий продуктов -->
  
  <!-- НОВОЕ: Секция категорий рецептов -->
  <div class="section-recipe-categories">
    <label>Категории рецептов:</label>
    <div class="checkbox-group">
      <label v-for="cat in recipeCategories" :key="cat.id" class="checkbox-item">
        <input
          type="checkbox"
          :value="cat.id"
          v-model="form.recipe_category_ids"
        />
        {{ cat.name }}
      </label>
    </div>
  </div>
  
  <!-- Существующий контент для продуктов (если ALLERGY) -->
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { categoryStore } from '@/stores/categoryStore';

const form = ref({
  name: '',
  type: 'CATEGORY_BASED',
  mode: 'BLOCKED',
  category_ids: [] as number[],
  recipe_category_ids: [] as number[],  // НОВОЕ
  product_ids: [] as number[],
});

const recipeCategories = ref([]);

onMounted(async () => {
  // Существующая логика загрузки категорий продуктов
  
  // НОВОЕ: Загрузка категорий рецептов
  await categoryStore.load('recipe');
  recipeCategories.value = categoryStore.recipeCategories;
});
</script>
```

### Обновленный composable usePreferenceFilter

**Файл:** `frontend/src/composables/usePreferenceFilter.ts`

**Новая функция:**

```typescript
function resolveRecipeCategoryIds(recipe: Recipe, visited: Set<number> = new Set()): number[] {
  /**
   * Рекурсивно собирает все ID категорий рецептов из рецепта и подрецептов.
   * Использует visited set для защиты от циклических зависимостей.
   */
  if (visited.has(recipe.id)) {
    return [];
  }
  
  visited.add(recipe.id);
  let categoryIds: number[] = [];
  
  if (recipe.category_id && recipe.category_id !== 0) {
    categoryIds.push(recipe.category_id);
  }
  
  for (const ingredient of recipe.ingredients) {
    if (ingredient.is_recipe && ingredient.recipe_id) {
      const subRecipe = recipeStore.getById(ingredient.recipe_id);
      if (subRecipe) {
        categoryIds = categoryIds.concat(resolveRecipeCategoryIds(subRecipe, visited));
      }
    }
  }
  
  return [...new Set(categoryIds)];
}
```

**Обновленная функция `recipeViolatesPref`:**

```typescript
function recipeViolatesPref(recipe: Recipe, preference: Preference): boolean {
  /**
   * Проверяет, нарушает ли рецепт предпочтение.
   * Возвращает true если рецепт НЕ совместим с предпочтением.
   */
  
  const allProductIds = resolveAllProductIds(recipe);
  const allCategoryIds = resolveProductCategoryIds(allProductIds);
  const allRecipeCategoryIds = resolveRecipeCategoryIds(recipe);  // НОВОЕ
  
  // Если в предпочтении указаны категории рецептов
  if (preference.recipe_category_ids && preference.recipe_category_ids.length > 0) {
    const hasMatchingRecipeCategory = allRecipeCategoryIds.some(id =>
      preference.recipe_category_ids.includes(id)
    );
    
    // Если ни одна категория рецепта не совпадает — рецепт не подходит
    if (!hasMatchingRecipeCategory) {
      return true;  // нарушает (не соответствует категориям рецептов)
    }
  }
  
  // Проверка по типу предпочтения (существующая логика для ALLERGY и CATEGORY_BASED)
  if (preference.type === 'ALLERGY') {
    return violatesAllergy(allProductIds, allCategoryIds, preference);
  }
  
  if (preference.mode === 'BLOCKED') {
    return violatesBlocked(allCategoryIds, preference);
  }
  
  // ALLOWED mode
  return violatesAllowed(allProductIds, allCategoryIds, preference);
}
```

**Логика проверки:**
1. Если `preference.recipe_category_ids` не пусто:
   - Собрать все категории рецептов из рецепта и подрецептов
   - Проверить пересечение с `preference.recipe_category_ids`
   - Если пересечение пусто — рецепт не подходит (возвращает `true`)
2. Если пересечение есть — продолжить проверку по категориям продуктов и продуктам

## Примеры использования

### Пример 1: Предпочтение "Без молочных в супах"

**Backend:**
- `type = CATEGORY_BASED`
- `mode = BLOCKED`
- `category_ids = [1]` (Молочные)
- `recipe_category_ids = [10]` (Суп)

**Поведение:**
- Рецепт "Борщ со сметаной" (категория: Суп, содержит молочные) → `False` (нарушает)
- Рецепт "Молочный десерт" (категория: Десерт, содержит молочные) → `True` (совместим, т.к. категория не Суп)
- Рецепт "Крем-суп из грибов" (категория: Суп, только овощи) → `True` (совместим)

### Пример 2: Предпочтение "Аллергия на арахис в десертах"

**Backend:**
- `type = ALLERGY`
- `mode = BLOCKED` (автоматически)
- `product_ids = [20]` (Арахис)
- `recipe_category_ids = [11]` (Десерт)

**Поведение:**
- Рецепт "Арахисовое печенье" (категория: Десерт, содержит арахис) → `False` (нарушает)
- Рецепт "Салат с арахисом" (категория: Закуска, содержит арахис) → `True` (совместим, т.к. категория не Десерт)
- Рецепт "Шоколадный мусс" (категория: Десерт, без арахиса) → `True` (совместим)

### Пример 3: Предпочтение "Только каши на завтрак"

**Backend:**
- `type = CATEGORY_BASED`
- `mode = ALLOWED`
- `category_ids = [5]` (Крупы)
- `recipe_category_ids = [9]` (Завтрак)

**Поведение:**
- Рецепт "Гречневая каша" (категория: Завтрак, только крупы) → `True` (совместим)
- Рецепт "Омлет с гречкой" (категория: Завтрак, содержит яйца + крупы) → `False` (нарушает, т.к. есть не-крупа ингредиент)
- Рецепт "Рисовая каша" (категория: Обед, только крупы) → `False` (нарушает, т.к. категория Обед, а не Завтрак)

## Обратная совместимость

- Существующие предпочтения без категорий рецептов (созданные в v0.13.0) продолжают работать без изменений
- Для таких предпочтений `recipe_category_ids = []` (пусто), поэтому они применяются ко всем рецептам
- Миграция БД добавляет пустую таблицу `preference_recipe_categories` без изменения существующих данных в таблице `preferences`
