# v0.9.1 — Kebab меню, группировка по поставщику и настройки списка покупок

**Дата:** 25.03.2026

Версия 0.9.1 добавляет kebab меню для мобильных устройств в планировщик и список покупок, функцию скрытия купленных товаров, группировку по поставщику, и новый раздел настроек списка покупок. Также добавлено сохранение времени последнего входа для каждого пользователя.

---

## Обзор функций

1. **Kebab меню в планировщике на мобильных устройствах** — кнопка с тремя точками в заголовке с быстрым доступом к действиям
2. **Kebab меню в списке покупок на мобильных устройствах** — кнопка с тремя точками в заголовке с действиями управления списком
3. **Скрытие купленных товаров** — переключатель для скрытия отмеченных товаров
4. **Купленные товары в отдельной секции** — группировка куплено в конце таблицы со светлым фоном
5. **Группировка по поставщику** — новая опция группировки (наряду с категориями)
6. **Настройки списка покупок** — новый подраздел в Настройках для управления скрытием и группировкой
7. **Сортировка от новых к старым** — меню и списки теперь сортируются в обратном хронологическом порядке
8. **Сохранение last_login_at** — бэкенд записывает время последнего входа пользователя
9. **Кнопка Сохранить всегда видима** — в списке покупок кнопка видна, но серая при отсутствии изменений

---

## Архитектура

### Слой представления (Vue 3 компоненты)

**Директория:** `frontend/src/components/` и `frontend/src/views/`

#### Новые и обновлённые компоненты

| Компонент | Файл | Изменение |
|-----------|------|-----------|
| **MenuPlannerView** | `views/MenuPlannerView.vue` | Добавлено kebab меню в заголовке для мобильных устройств |
| **ShoppingListView** | `views/ShoppingListView.vue` | Добавлено kebab меню, скрытие купленных товаров, группировка по поставщику |
| **ShoppingListSettingsPanel** | `components/shopping/ShoppingListSettingsPanel.vue` | Новый компонент для раздела настроек списка покупок |

#### Kebab меню в планировщике (MenuPlannerView)

**Мобильные устройства:**

```typescript
interface KebabMenuAction {
  label: string      // "Обзор блюд", "Сформировать список", и т.д.
  icon: string       // иконка SVG
  action: () => void // функция обработки
}

const kebabMenuActions: KebabMenuAction[] = [
  { label: "Обзор блюд", icon: "eye", action: () => goToSummary() },
  { label: "Сформировать список", action: () => generateShoppingList() },
  { label: "Очистить меню", action: () => clearMenu() },
  { label: "Импорт", action: () => importMenu() },
  { label: "Экспорт", action: () => exportMenu() }
]
```

**Логика:**
1. На мобильных устройствах в заголовке отображается кнопка с тремя точками **⋮**
2. При нажатии открывается dropdown меню с действиями
3. Кнопки внизу экрана скрываются на мобильных устройствах (видны только на десктопе)

#### Kebab меню в списке покупок (ShoppingListView)

```typescript
interface ShoppingListKebabAction {
  label: string
  icon?: string
  isToggle?: boolean           // для переключателя Скрыть/Показать
  isChecked?: boolean
  action: () => void
}

const kebabMenuActions: ShoppingListKebabAction[] = [
  { label: "Скрыть/Показать купленные", icon: "eye", isToggle: true, action: toggleHidePurchased },
  { label: "Выбрать", action: () => enableSelectionMode() },
  { label: "Удалить выбранные", action: () => deleteSelected() },
  { label: "Удалить все", action: () => deleteAll() }
]
```

#### Скрытие купленных товаров

**На десктопе:** кнопка-иконка глаза **👁** в панели действий заголовка

**На мобильных:** переключатель в kebab меню

**Логика:**
```typescript
const hidePurchased = ref<boolean>(false)

const visibleShoppingItems = computed(() => {
  if (!hidePurchased.value) return shoppingItems.value
  return shoppingItems.value.filter(item => !item.is_purchased)
})
```

**Состояние сохраняется** в localStorage через Pinia store `shoppingListSettings`:

```typescript
// frontend/src/stores/shoppingListSettings.ts
export const useShoppingListSettingsStore = defineStore('shoppingListSettings', () => {
  const hidePurchased = ref<boolean>(false)
  const groupingMode = ref<'category' | 'supplier'>('category')

  function loadSettings() {
    const saved = localStorage.getItem('shoppingListSettings')
    if (saved) {
      const settings = JSON.parse(saved)
      hidePurchased.value = settings.hidePurchased ?? false
      groupingMode.value = settings.groupingMode ?? 'category'
    }
  }

  function saveSettings() {
    localStorage.setItem('shoppingListSettings', JSON.stringify({
      hidePurchased: hidePurchased.value,
      groupingMode: groupingMode.value
    }))
  }

  return { hidePurchased, groupingMode, loadSettings, saveSettings }
})
```

#### Группировка товаров

**Логика в ShoppingListView:**

```typescript
const groupingMode = computed(() => shoppingListSettingsStore.groupingMode)

const groupedItems = computed(() => {
  if (groupingMode.value === 'category') {
    return groupByCategory(visibleShoppingItems.value)
  } else {
    return groupBySupplier(visibleShoppingItems.value)
  }
})

function groupByCategory(items: ShoppingItem[]): GroupedItems {
  return Object.groupBy(items, item => item.category_name ?? 'Без категории')
}

function groupBySupplier(items: ShoppingItem[]): GroupedItems {
  return Object.groupBy(items, item => item.supplier ?? 'Без поставщика')
}
```

#### Купленные товары в отдельной секции

**Логика отделения:**

```typescript
const purchasedItems = computed(() => {
  return shoppingItems.value.filter(item => item.is_purchased)
})

const unpurchasedItems = computed(() => {
  return shoppingItems.value.filter(item => !item.is_purchased)
})
```

**Структура таблицы:**

1. Непокупленные товары (сгруппированы по категориям или поставщикам)
2. Секция **«Куплено»** (только если есть купленные товары)
   - Визуально отделена (светлый фон, серый текст)
   - Заголовок с иконкой галочки ✓

#### Сортировка меню и списков

**В Pinia store `menus.ts`:**

```typescript
const sortedMenus = computed(() => {
  return [...menus.value].sort((a, b) => b.id - a.id)
})
```

**В Pinia store `shoppingList.ts`:**

```typescript
const sortedLists = computed(() => {
  return [...savedLists.value].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})
```

#### ShoppingListSettingsPanel компонент

**Расположение:** `frontend/src/components/settings/ShoppingListSettingsPanel.vue`

**Входные параметры (props):** нет (использует Pinia store)

**Содержимое:**

```vue
<template>
  <div class="shopping-list-settings">
    <!-- Переключатель скрытия -->
    <div class="setting-item">
      <label>Скрывать купленные товары</label>
      <ToggleSwitch v-model="hidePurchased" />
    </div>

    <!-- Выбор группировки -->
    <div class="setting-item">
      <label>Группировка товаров</label>
      <RadioGroup
        v-model="groupingMode"
        :options="[
          { label: 'По категории', value: 'category' },
          { label: 'По поставщику', value: 'supplier' }
        ]"
      />
    </div>
  </div>
</template>
```

**Логика:**

```typescript
const shoppingListSettings = useShoppingListSettingsStore()

const hidePurchased = computed({
  get: () => shoppingListSettings.hidePurchased,
  set: (value) => {
    shoppingListSettings.hidePurchased = value
    shoppingListSettings.saveSettings()
  }
})

const groupingMode = computed({
  get: () => shoppingListSettings.groupingMode,
  set: (value) => {
    shoppingListSettings.groupingMode = value
    shoppingListSettings.saveSettings()
  }
})
```

---

### Слой приложения (Use Cases)

**Директория:** `backend/application/use_cases/`

Нет новых use cases. Все изменения в приложении касаются фронтенда и сохранения `last_login_at` на бэкенде (см. ниже).

---

### Слой домена (Domain)

**Файл:** `backend/domain/entities/user.py`

#### Добавлено поле last_login_at

```python
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: UserId
    email: str
    name: str
    password_hash: str
    created_at: datetime
    last_login_at: Optional[datetime] = None  # НОВОЕ
```

---

### Слой инфраструктуры (Infrastructure)

**Файл:** `backend/infrastructure/persistence/sqlalchemy_user_repository.py`

#### Обновлена логика login

```python
async def login(self, user: User) -> None:
    """Обновить время последнего входа пользователя"""
    db_user = self.session.query(UserORM).filter(UserORM.id == user.id).first()
    if db_user:
        db_user.last_login_at = datetime.utcnow()  # НОВОЕ
        self.session.commit()
```

**Файл:** `backend/infrastructure/persistence/sqlalchemy_models.py`

```python
from sqlalchemy import Column, DateTime
from datetime import datetime

class UserORM(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)  # НОВОЕ
```

---

### API слой

**Директория:** `backend/api/`

#### Pydantic схемы

**Файл:** `backend/api/schemas.py`

```python
from datetime import datetime
from typing import Optional

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    last_login_at: Optional[datetime]  # НОВОЕ

    class Config:
        from_attributes = True
```

#### Обновление эндпоинта login

**Файл:** `backend/api/routers/auth.py`

```python
@router.post("/login")
async def login(
    request: LoginRequest,
    container: ApplicationContainer = Depends(get_container)
) -> TokenResponse:
    """
    Вход в систему.

    При успешном входе обновляется поле last_login_at пользователя.
    """
    use_case = container.login_user()
    result = await use_case(LoginUserRequest(
        email=request.email,
        password=request.password
    ))

    # После успешной аутентификации обновить last_login_at
    user_repo = container.user_repository()
    user = await user_repo.get_by_id(result.user_id)
    if user:
        user.last_login_at = datetime.utcnow()
        await user_repo.update(user)

    return result
```

---

### Миграции базы данных

**Файл:** `backend/alembic/versions/XXXX_add_last_login_at.py`

```python
"""Add last_login_at field to users table"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'last_login_at')
```

**Выполнить миграцию:**
```bash
alembic upgrade head
```

---

## LocalStorage персистентность

### Структура хранилища

**Ключ:** `shoppingListSettings`

**Значение:**
```json
{
  "hidePurchased": false,
  "groupingMode": "category"
}
```

### Инициализация при загрузке

При загрузке приложения (mounted) в `ShoppingListView` и `SettingsView`:

```typescript
onMounted(() => {
  shoppingListSettingsStore.loadSettings()
})
```

---

## Маршруты и навигация

### Vue Router

**Файл:** `frontend/src/router/index.ts`

Новый маршрут для настроек списка покупок:

```typescript
{
  path: '/settings/shopping-list',
  component: () => import('@/views/SettingsView.vue'),
  meta: { requiresAuth: true },
  props: { activeSection: 'shopping-list' }
}
```

---

## Тестирование

### Unit тесты

**Директория:** `tests/unit/`

#### test_shopping_list_settings_store.ts (Vue unit test)

```typescript
import { useShoppingListSettingsStore } from '@/stores/shoppingListSettings'

describe('ShoppingListSettingsStore', () => {
  it('should save and load settings from localStorage', () => {
    const store = useShoppingListSettingsStore()

    store.hidePurchased = true
    store.groupingMode = 'supplier'
    store.saveSettings()

    const store2 = useShoppingListSettingsStore()
    store2.loadSettings()

    expect(store2.hidePurchased).toBe(true)
    expect(store2.groupingMode).toBe('supplier')
  })

  it('should filter purchased items when hidePurchased is true', () => {
    // Тест логики фильтрации
  })

  it('should group items by supplier', () => {
    // Тест группировки по поставщику
  })
})
```

#### test_user_last_login.py (Python unit test)

```python
import pytest
from datetime import datetime
from backend.domain.entities.user import User
from backend.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository

@pytest.mark.asyncio
async def test_update_last_login_on_login(session):
    """Тест сохранения last_login_at при входе"""
    user_repo = SQLAlchemyUserRepository(session)

    user = User(id=UserId(1), email="test@example.com", name="Test")
    user.last_login_at = None

    await user_repo.login(user)

    updated_user = await user_repo.get_by_id(UserId(1))
    assert updated_user.last_login_at is not None
    assert isinstance(updated_user.last_login_at, datetime)
```

---

## Производительность

### Оптимизации

1. **Группировка на фронтенде** — логика группировки выполняется в computed properties (кеширование)
2. **LocalStorage кеш** — настройки загружаются один раз при инициализации store
3. **Ленивая загрузка ингредиентов** — в сводке компоненты раскрываются по требованию

### Сложность

- **Группировка товаров:** O(n) где n — количество товаров
- **Фильтрация по `hidePurchased`:** O(n)
- **Агрегированная сложность в ShoppingListView:** O(n × m) где n — товары, m — группы (категории или поставщики)

---

## Совместимость

### Версия 0.9.0

Все изменения полностью совместимы с v0.9.0:

- Экран сводки блюд работает без изменений
- API эндпоинты расширяются только добавлением нового поля `last_login_at` в `UserResponse`
- Старые клиенты могут игнорировать это поле

### Вложенные рецепты (v0.6.0)

Группировка по поставщику поддерживает вложенные рецепты:

- При развёртывании вложенных рецептов в список покупок продукты группируются с учётом поля `supplier`

### Штучный режим (v0.7.0)

Скрытие и группировка работают с штучным режимом без изменений.

---

## Будущие улучшения

1. **Статистика входов** — отображение истории входов пользователя в профиле
2. **Автоматическое скрытие купленных** — опция автоматического скрытия после отметки
3. **Экспорт с учётом группировки** — сохранение выбранного способа группировки при экспорте
4. **Кастомные группировки** — возможность группировать по бренду или другим полям
5. **Статусы товаров** — расширение статусов (куплено, в корзине, зарезервировано и т.д.)

---

**История версий:**

- **v0.9.1** (25.03.2026) — Kebab меню, скрытие купленных товаров, группировка по поставщику, настройки списка покупок, сохранение last_login_at
- **v0.9.0** (24.03.2026) — Экран сводки блюд, экспорт плана приготовления
