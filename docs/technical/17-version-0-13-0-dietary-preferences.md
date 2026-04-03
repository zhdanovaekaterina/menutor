# Версия 0.13.0 — Система пищевых предпочтений

Документация функций версии 0.13.0: полная система управления пищевыми предпочтениями с поддержкой двух типов (По категориям, Аллергия), двух режимов (Блокировать, Разрешать), назначения предпочтений членам семьи, валидации совместимости режимов (BR-3), рекурсивной проверки совместимости рецептов, интеграции с планировщиком меню (затемнение, значки-предупреждения, цветные активные предпочтения).

## Обзор

Система пищевых предпочтений позволяет пользователям управлять диетическими ограничениями членов семьи и автоматически фильтровать несовместимые рецепты в планировщике меню.

**Ключевые возможности:**
- CRUD операции для предпочтений (Create, Read, Update, Delete)
- Два типа предпочтений: По категориям и Аллергия
- Два режима для По категориям: Блокировать и Разрешать
- Назначение предпочтений членам семьи
- Валидация совместимости режимов (BR-3)
- Проверка совместимости рецептов с предпочтениями
- Фильтрация и сортировка в планировщике меню
- Отображение активных предпочтений в заголовке планировщика

## Доменный слой

### Сущность Preference

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
    user_id: UserId = field(default=UserId(0))
```

**Поля:**
- `id` — уникальный идентификатор предпочтения (типизированный NewType)
- `name` — наименование предпочтения (должно быть уникально в пределах пользователя)
- `type` — тип предпочтения (CATEGORY_BASED или ALLERGY)
- `mode` — режим (BLOCKED или ALLOWED; для ALLERGY всегда BLOCKED)
- `category_ids` — список ID категорий продуктов (для типа CATEGORY_BASED)
- `product_ids` — список ID конкретных продуктов (для типа ALLERGY)
- `user_id` — ID владельца (многопользовательская поддержка)

**Валидация (в `__post_init__`):**
- BR-1: Название не может быть пустым (только пробелы)
- BR-2: Если тип ALLERGY, режим обязательно BLOCKED
- BR-2a: Если тип CATEGORY_BASED, product_ids должны быть пусты (категории не содержат отдельные продукты)

### Перечисления PreferenceType и PreferenceMode

**Файл:** `backend/domain/value_objects/preference_enums.py`

```python
class PreferenceType(Enum):
    CATEGORY_BASED = "CATEGORY_BASED"  # По категориям продуктов
    ALLERGY = "ALLERGY"                 # Аллергия на продукты

class PreferenceMode(Enum):
    BLOCKED = "BLOCKED"    # Исключить из меню
    ALLOWED = "ALLOWED"    # Разрешить только
```

### Доменный сервис PreferenceMatcher

**Файл:** `backend/domain/services/preference_matcher.py`

Сервис для проверки совместимости рецепта с предпочтениями. Осуществляет чистые вычисления над данными ингредиентов, поддерживает рекурсивное разрешение вложенных рецептов.

#### Основной метод

```python
def matches_preference(self, recipe: Recipe, preference: Preference) -> bool:
    """Return True if the recipe satisfies (is compatible with) the given preference."""
    all_product_ids = self._resolve_all_product_ids(recipe, set())
    all_category_ids, has_uncategorized = self._resolve_category_ids(all_product_ids)
    
    if preference.type == PreferenceType.ALLERGY:
        return self._matches_allergy(all_product_ids, all_category_ids, preference)
    
    if preference.mode == PreferenceMode.BLOCKED:
        return self._matches_blocked(all_category_ids, preference)
    
    # ALLOWED mode
    return self._matches_allowed(all_product_ids, all_category_ids, preference, has_uncategorized)
```

#### Методы помощника

**`_resolve_all_product_ids(recipe, visited)`**
- Рекурсивно собирает все ID продуктов из рецепта и его подрецептов
- Использует `visited` set для предотвращения бесконечных циклов
- Для каждого ингредиента: если это продукт, добавляет его ID; если это подрецепт, рекурсивно разрешает его

**`_resolve_category_ids(product_ids)`**
- Ищет категории для набора ID продуктов через ProductRepository
- Возвращает кортеж `(category_ids, has_uncategorized)`
- `has_uncategorized = True`, если хотя бы один продукт имеет `category_id == 0` (BR-9)

**`_matches_allergy(product_ids, category_ids, preference)`**
- Возвращает `True`, если рецепт НЕ содержит ни одного продукта/категории из preference.product_ids или preference.category_ids
- Если пересечение не пусто — возвращает `False`

**`_matches_blocked(category_ids, preference)`**
- Возвращает `True`, если рецепт НЕ содержит ни одну категорию из preference.category_ids
- Если пересечение не пусто — возвращает `False`

**`_matches_allowed(product_ids, category_ids, preference, has_uncategorized)`**
- Возвращает `True` только если ВСЕ категории рецепта содержатся в preference.category_ids
- Специальные случаи:
  - EC-1: Пустой рецепт (без ингредиентов) возвращает `False`
  - BR-9: Если есть некатегоризированные продукты — возвращает `False` (невозможно гарантировать совместимость)

#### Пакетный метод

```python
def match_all(self, recipe: Recipe, preferences: list[Preference]) -> list[Preference]:
    """Return the subset of preferences that the recipe satisfies."""
    return [p for p in preferences if self.matches_preference(recipe, p)]
```

## Слой приложения

### Use Case: CreatePreference

**Файл:** `backend/application/use_cases/manage_preference.py`

```python
@dataclass
class PreferenceData:
    name: str
    type: PreferenceType
    mode: PreferenceMode
    category_ids: list[ProductCategoryId] = field(default_factory=list)
    product_ids: list[ProductId] = field(default_factory=list)

class CreatePreference:
    def __init__(self, repo: PreferenceRepository) -> None:
        self._repo = repo
    
    def execute(self, data: PreferenceData, user_id: UserId) -> Preference:
        existing = self._repo.find_by_name(data.name, user_id)
        if existing is not None:
            raise DuplicateNameError("предпочтение")  # BR-1
        preference = Preference(
            id=PreferenceId(0),
            name=data.name,
            type=data.type,
            mode=data.mode,
            category_ids=data.category_ids,
            product_ids=data.product_ids,
            user_id=user_id,
        )
        return self._repo.save(preference)
```

**Логика:**
1. Проверяет уникальность названия в пределах пользователя (BR-1)
2. Создаёт объект Preference (который валидирует себя в `__post_init__`)
3. Сохраняет через репозиторий и возвращает с установленным ID

### Use Case: UpdatePreference

```python
class UpdatePreference:
    def execute(
        self, preference_id: PreferenceId, data: PreferenceData, user_id: UserId
    ) -> Preference:
        load_owned(self._repo, preference_id, user_id, "Предпочтение")
        existing = self._repo.find_by_name(data.name, user_id)
        if existing is not None and existing.id != preference_id:
            raise DuplicateNameError("предпочтение")
        preference = Preference(
            id=preference_id,
            name=data.name,
            type=data.type,
            mode=data.mode,
            category_ids=data.category_ids,
            product_ids=data.product_ids,
            user_id=user_id,
        )
        return self._repo.save(preference)
```

**Логика:**
1. Проверяет, что предпочтение принадлежит пользователю
2. Проверяет уникальность нового названия (исключая текущее предпочтение)
3. Создаёт обновлённый объект и сохраняет

### Use Case: DeletePreference

```python
class DeletePreference:
    def __init__(
        self,
        preference_repo: PreferenceRepository,
        family_repo: FamilyMemberRepository,
    ) -> None:
        self._preference_repo = preference_repo
        self._family_repo = family_repo
    
    def execute(self, preference_id: PreferenceId, user_id: UserId) -> None:
        existing = self._preference_repo.get_by_id(preference_id)
        if existing is None or existing.user_id != user_id:
            return  # silently ignore
        
        # Удалить из всех членов семьи
        members = self._family_repo.find_all(user_id)
        for member in members:
            if preference_id in member.preference_ids:
                member.preference_ids.remove(preference_id)
                self._family_repo.save(member)
        
        self._preference_repo.delete([preference_id])
```

**Логика:**
1. Находит предпочтение и проверяет принадлежность пользователю
2. Удаляет предпочтение из всех членов семьи (cascade-удаление на уровне приложения)
3. Удаляет само предпочтение

### Use Case: AssignPreferencesToMember

**Файл:** `backend/application/use_cases/assign_preferences.py`

```python
class AssignPreferencesToMember:
    """Replaces all preference assignments on a family member.
    
    Validates BR-3: all preferences must share the same effective mode
    (all BLOCKED-family or all ALLOWED-family).
    """
    
    def execute(
        self,
        member_id: FamilyMemberId,
        preference_ids: list[PreferenceId],
        user_id: UserId,
    ) -> FamilyMember:
        member = self._family_repo.get_by_id(member_id)
        if member is None or member.user_id != user_id:
            raise EntityNotFoundError(f"Член семьи {member_id} не найден")
        
        if preference_ids:
            preferences = self._preference_repo.find_by_ids(preference_ids, user_id)
            found_ids = {p.id for p in preferences}
            for pid in preference_ids:
                if pid not in found_ids:
                    raise EntityNotFoundError(f"Предпочтение {pid} не найдено")
            self._validate_mode_compatibility(preferences)
        
        member.preference_ids = preference_ids
        return self._family_repo.save(member)
    
    @staticmethod
    def _validate_mode_compatibility(preferences: list) -> None:
        """Ensure all preferences have compatible modes (BR-3)."""
        has_blocked = False
        has_allowed = False
        for p in preferences:
            effective_mode = (
                PreferenceMode.BLOCKED
                if p.type == PreferenceType.ALLERGY
                else p.mode
            )
            if effective_mode == PreferenceMode.BLOCKED:
                has_blocked = True
            else:
                has_allowed = True
        if has_blocked and has_allowed:
            raise IncompatiblePreferenceModesError(
                "Нельзя назначить одному члену семьи предпочтения "
                "с режимами BLOCKED и ALLOWED одновременно"
            )
```

**Логика:**
1. Проверяет наличие и принадлежность члена семьи
2. Проверяет, что все запрошенные предпочтения существуют и принадлежат пользователю
3. **BR-3: Валидирует совместимость режимов** — все предпочтения должны быть либо все BLOCKED (включая аллергии), либо все ALLOWED
4. Назначает предпочтения члену и сохраняет

### Use Case: MatchRecipePreferences

**Файл:** `backend/application/use_cases/match_recipe_preferences.py`

```python
class MatchRecipePreferences:
    """Returns all user preferences that a given recipe satisfies."""
    
    def __init__(
        self,
        recipe_repo: RecipeRepository,
        preference_repo: PreferenceRepository,
        matcher: PreferenceMatcher,
    ) -> None:
        self._recipe_repo = recipe_repo
        self._preference_repo = preference_repo
        self._matcher = matcher
    
    def execute(self, recipe_id: RecipeId, user_id: UserId) -> list[Preference]:
        recipe = self._recipe_repo.get_by_id(recipe_id)
        if recipe is None or recipe.user_id != user_id:
            return []
        all_prefs = self._preference_repo.find_all(user_id)
        return self._matcher.match_all(recipe, all_prefs)
```

**Логика:**
1. Находит рецепт, проверяет принадлежность пользователю (возвращает пустой список при отсутствии)
2. Получает все предпочтения пользователя
3. Возвращает подмножество предпочтений, которым рецепт соответствует

## Инфраструктурный слой

### ORM-модели

**Файл:** `backend/infrastructure/database/models.py`

```python
class PreferenceRow(Base):
    __tablename__ = "preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)   # "CATEGORY_BASED" или "ALLERGY"
    mode = Column(String, nullable=False)   # "BLOCKED" или "ALLOWED"
    
    categories = relationship(
        "PreferenceCategoryRow",
        back_populates="preference",
        cascade="all, delete-orphan",
    )
    products = relationship(
        "PreferenceProductRow",
        back_populates="preference",
        cascade="all, delete-orphan",
    )

class PreferenceCategoryRow(Base):
    __tablename__ = "preference_categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    preference_id = Column(
        Integer, ForeignKey("preferences.id", ondelete="CASCADE"), nullable=False
    )
    category_id = Column(
        Integer, ForeignKey("product_categories.id"), nullable=False
    )
    preference = relationship("PreferenceRow", back_populates="categories")

class PreferenceProductRow(Base):
    __tablename__ = "preference_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    preference_id = Column(
        Integer, ForeignKey("preferences.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    preference = relationship("PreferenceRow", back_populates="products")

class FamilyMemberPreferenceRow(Base):
    __tablename__ = "family_member_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    family_member_id = Column(
        Integer,
        ForeignKey("family_members.id", ondelete="CASCADE"),
        nullable=False,
    )
    preference_id = Column(
        Integer,
        ForeignKey("preferences.id", ondelete="CASCADE"),
        nullable=False,
    )
```

**Структура:**
- `preferences` — основная таблица с предпочтениями (id, user_id, name, type, mode)
- `preference_categories` — связь между предпочтением и категориями продуктов (M:N)
- `preference_products` — связь между предпочтением (тип ALLERGY) и продуктами (M:N)
- `family_member_preferences` — связь между членом семьи и предпочтениями (M:N)

Также к модели `FamilyMemberRow` добавлено поле `preference_links` и соответствующее отношение.

### Репозиторий OrmPreferenceRepository

**Файл:** `backend/infrastructure/repositories/orm_preference_repository.py`

```python
class OrmPreferenceRepository(PreferenceRepository):
    def __init__(self, session: Session) -> None:
        self._session = session
    
    def get_by_id(self, preference_id: PreferenceId) -> Preference | None:
        row = self._session.query(PreferenceRow).filter_by(id=int(preference_id)).first()
        if row is None:
            return None
        return self._row_to_domain(row)
    
    def find_by_name(self, name: str, user_id: UserId) -> Preference | None:
        row = self._session.query(PreferenceRow).filter_by(
            name=name, user_id=int(user_id)
        ).first()
        if row is None:
            return None
        return self._row_to_domain(row)
    
    def find_all(self, user_id: UserId) -> list[Preference]:
        rows = self._session.query(PreferenceRow).filter_by(
            user_id=int(user_id)
        ).all()
        return [self._row_to_domain(row) for row in rows]
    
    def find_by_ids(self, ids: list[PreferenceId], user_id: UserId) -> list[Preference]:
        rows = self._session.query(PreferenceRow).filter(
            PreferenceRow.id.in_([int(pid) for pid in ids]),
            PreferenceRow.user_id == int(user_id),
        ).all()
        return [self._row_to_domain(row) for row in rows]
    
    def save(self, preference: Preference) -> Preference:
        existing = None
        if preference.id != PreferenceId(0):
            existing = self._session.query(PreferenceRow).filter_by(
                id=int(preference.id)
            ).first()
        
        if existing is None:
            row = PreferenceRow(
                name=preference.name,
                type=preference.type.value,
                mode=preference.mode.value,
                user_id=int(preference.user_id),
            )
            self._session.add(row)
        else:
            existing.name = preference.name
            existing.type = preference.type.value
            existing.mode = preference.mode.value
        
        self._session.flush()
        
        # Обновить категории
        if existing is None:
            row = self._session.query(PreferenceRow).filter_by(
                name=preference.name, user_id=int(preference.user_id)
            ).first()
        else:
            row = existing
        
        # Удалить старые связи
        self._session.query(PreferenceCategoryRow).filter_by(
            preference_id=row.id
        ).delete()
        self._session.query(PreferenceProductRow).filter_by(
            preference_id=row.id
        ).delete()
        
        # Добавить новые связи
        for cat_id in preference.category_ids:
            self._session.add(PreferenceCategoryRow(
                preference_id=row.id,
                category_id=int(cat_id),
            ))
        for prod_id in preference.product_ids:
            self._session.add(PreferenceProductRow(
                preference_id=row.id,
                product_id=int(prod_id),
            ))
        
        self._session.commit()
        return self._row_to_domain(row)
    
    def delete(self, preference_ids: list[PreferenceId]) -> None:
        self._session.query(PreferenceRow).filter(
            PreferenceRow.id.in_([int(pid) for pid in preference_ids])
        ).delete()
        self._session.commit()
    
    @staticmethod
    def _row_to_domain(row: PreferenceRow) -> Preference:
        return Preference(
            id=PreferenceId(row.id),
            name=row.name,
            type=PreferenceType(row.type),
            mode=PreferenceMode(row.mode),
            category_ids=[ProductCategoryId(c.category_id) for c in row.categories],
            product_ids=[ProductId(p.product_id) for p in row.products],
            user_id=UserId(row.user_id),
        )
```

## API слой

### Маршрутизатор preferences

**Файл:** `backend/api/routers/preferences.py`

**Эндпоинты:**

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/preferences` | Список всех предпочтений пользователя |
| GET | `/preferences/{preference_id}` | Получить конкретное предпочтение |
| POST | `/preferences` | Создать новое предпочтение (201) |
| PUT | `/preferences/{preference_id}` | Обновить предпочтение |
| DELETE | `/preferences/{preference_id}` | Удалить предпочтение (204) |

```python
@router.get("", response_model=list[PreferenceResponse])
def list_preferences(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[PreferenceResponse]:
    prefs = container.list_preferences.execute(user.id)
    return [preference_to_response(p) for p in prefs]

@router.post("", response_model=PreferenceResponse, status_code=status.HTTP_201_CREATED)
def create_preference(
    body: PreferenceCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PreferenceResponse:
    data = schema_to_preference_data(body)
    pref = container.create_preference.execute(data, user.id)
    return preference_to_response(pref)

@router.put("/{preference_id}", response_model=PreferenceResponse)
def update_preference(
    preference_id: int,
    body: PreferenceUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PreferenceResponse:
    data = schema_to_preference_data(body)
    pref = container.update_preference.execute(
        PreferenceId(preference_id), data, user.id
    )
    return preference_to_response(pref)

@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preference(
    preference_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_preference.execute(PreferenceId(preference_id), user.id)
```

### Эндпоинт проверки совместимости в маршрутизаторе recipes

**Файл:** `backend/api/routers/recipes.py`

```python
@router.get(
    "/{recipe_id}/matching-preferences",
    response_model=PreferenceMatchResponse,
)
def get_matching_preferences(
    recipe_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PreferenceMatchResponse:
    matched = container.match_recipe_preferences.execute(RecipeId(recipe_id), user.id)
    return PreferenceMatchResponse(
        preferences=[preference_to_response(p) for p in matched]
    )
```

### Pydantic-схемы

**Файл:** `backend/api/schemas/preference.py`

```python
class PreferenceCreate(BaseModel):
    name: str
    type: str          # "CATEGORY_BASED" или "ALLERGY"
    mode: str          # "BLOCKED" или "ALLOWED"
    category_ids: list[int] = []
    product_ids: list[int] = []

PreferenceUpdate = PreferenceCreate

class PreferenceResponse(BaseModel):
    id: int
    name: str
    type: str
    mode: str
    category_ids: list[int]
    product_ids: list[int]

class PreferenceMatchResponse(BaseModel):
    """List of preferences that a recipe matches."""
    preferences: list[PreferenceResponse]
```

### Конвертеры

**Файл:** `backend/api/converters.py`

```python
def preference_to_response(pref: Preference) -> PreferenceResponse:
    return PreferenceResponse(
        id=int(pref.id),
        name=pref.name,
        type=pref.type.value,
        mode=pref.mode.value,
        category_ids=[int(cid) for cid in pref.category_ids],
        product_ids=[int(pid) for pid in pref.product_ids],
    )

def schema_to_preference_data(body: PreferenceCreate) -> PreferenceData:
    return PreferenceData(
        name=body.name,
        type=PreferenceType(body.type),
        mode=PreferenceMode(body.mode),
        category_ids=[ProductCategoryId(cid) for cid in body.category_ids],
        product_ids=[ProductId(pid) for pid in body.product_ids],
    )
```

## Фронтенд

### Хранилище usePreferencesStore

**Файл:** `frontend/src/stores/preferences.ts`

Pinia хранилище для управления состоянием предпочтений:
- `items: Preference[]` — список предпочтений
- `load()` — загрузить предпочтения с сервера
- `create(data: PreferenceCreate): Promise<Preference>` — создать
- `update(id: number, data: PreferenceUpdate): Promise<Preference>` — обновить
- `remove(id: number): Promise<void>` — удалить

### Компоненты настроек

**PreferencesSettings.vue** — таблица CRUD для предпочтений
- Отображает таблицу предпочтений с колонками: Название, Тип, Действие
- Кнопки: + Добавить, Редактировать (клик на строку), Удалить (иконка корзины)
- Открывает боковую панель формы (PreferenceForm.vue)
- На мобильных устройствах отображается как карточки вместо таблицы

**PreferenceForm.vue** — форма создания/редактирования
- Поле Название (обязательное)
- Выпадающий список Тип (CATEGORY_BASED / ALLERGY)
- Выпадающий список Действие (Блокировать / Разрешать) — скрывается для ALLERGY
- Выбор категорий (для CATEGORY_BASED) — мультиселект
- Выбор продуктов (для ALLERGY) — мультиселект
- Логика: смена типа очищает несовместимые поля

### Компонент значков предпочтений

**PreferenceBadges.vue** — отображение значков совместимости на странице рецепта
- Загружает список предпочтений, которым рецепт соответствует (GET `/recipes/{id}/matching-preferences`)
- Отображает цветные чипсы с названиями предпочтений
- Цвета:
  - **Красный** (bg-red-100 text-red-700) — для ALLERGY или BLOCKED
  - **Зелёный** (bg-green-100 text-green-700) — для ALLOWED
- Tooltip показывает тип предпочтения (при наведении)

### Компонуемая функция usePreferenceFilter

**Файл:** `frontend/src/composables/usePreferenceFilter.ts`

Composable для фильтрации рецептов и продуктов на основе активных предпочтений членов семьи.

**Входы:**
- `activeMemberIds: Ref<Set<number>>` — ID выбранных членов семьи
- `members: Ref<FamilyMember[]>` — список всех членов семьи
- `preferences: Ref<Preference[]>` — список всех предпочтений
- `recipes: Ref<Recipe[]>` — список всех рецептов
- `products: Ref<Product[]>` — список всех продуктов

**Выходы:**
- `blockedRecipeIds: Computed<Set<number>>` — ID несовместимых рецептов
- `blockedProductIds: Computed<Set<number>>` — ID несовместимых продуктов
- `activePreferences: Computed<Preference[]>` — активные предпочтения выбранных членов

**Алгоритм blockedRecipeIds:**
1. Собирает все preference_ids из выбранных членов семьи → `activePreferences`
2. Для каждого рецепта проверяет, нарушает ли он какое-либо активное предпочтение
3. Помечает как заблокированные рецепты, которые нарушают любое из активных предпочтений

**Функция recipeViolatesPref:**
- Рекурсивно разрешает все product_ids из рецепта (включая подрецепты)
- Преобразует product_ids в category_ids через `productCategoryMap`
- Проверяет соответствие предпочтению:
  - **ALLERGY:** нарушает если содержит ANY из blocked_products или blocked_categories
  - **BLOCKED:** нарушает если содержит ANY из blocked_categories
  - **ALLOWED:** нарушает если содержит ANY категорию вне allowed_categories OR есть uncategorized OR пусто

**Функция productViolatesPref:**
- Проверяет одиночный продукт (не рецепт) против предпочтения
- Использует категорию продукта для проверки

### Интеграция в планировщик меню

**SourcePanel.vue** — панель добавления рецептов и продуктов
- Принимает `blockedRecipeIds` и `blockedProductIds` как props
- Сортирует рецепты: совместимые первыми, затем заблокированные (opacity снижается)
- Сортирует продукты: совместимые первыми, затем заблокированные

**MenuPlannerView.vue** — основной экран планировщика
- Вызывает `usePreferenceFilter()` composable
- Отображает активные предпочтения над сеткой меню:
  ```vue
  <div v-if="activePreferences.length > 0" class="flex items-center gap-1.5 flex-wrap text-xs">
    <span class="text-gray-500 shrink-0">Предпочтения:</span>
    <span v-for="pref in activePreferences" :key="pref.id"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium"
          :class="colorClass(pref)">
      {{ pref.name }}
    </span>
  </div>
  ```
- Цвета чипс:
  - **Красный** (bg-red-100 text-red-700) — для ALLERGY
  - **Жёлтый** (bg-amber-100 text-amber-700) — для BLOCKED
  - **Зелёный** (bg-green-100 text-green-700) — для ALLOWED
- Передаёт `blockedRecipeIds` и `blockedProductIds` в SourcePanel для фильтрации

## Миграция базы данных

**Файл:** `backend/infrastructure/database/migrations/versions/b1c2d3e4f5a6_add_dietary_preferences.py`

Миграция создаёт четыре новые таблицы:

1. `preferences` (4 столбца):
   - id (PK, autoincrement)
   - user_id (FK → users.id, CASCADE)
   - name (String)
   - type (String: CATEGORY_BASED, ALLERGY)
   - mode (String: BLOCKED, ALLOWED)

2. `preference_categories` (3 столбца):
   - id (PK, autoincrement)
   - preference_id (FK → preferences.id, CASCADE)
   - category_id (FK → product_categories.id)

3. `preference_products` (3 столбца):
   - id (PK, autoincrement)
   - preference_id (FK → preferences.id, CASCADE)
   - product_id (FK → products.id, CASCADE)

4. `family_member_preferences` (3 столбца):
   - id (PK, autoincrement)
   - family_member_id (FK → family_members.id, CASCADE)
   - preference_id (FK → preferences.id, CASCADE)

**Также:**
- Удаляется столбец `dietary_restrictions` из `family_members`
- Его содержимое мигрируется в `comment` столбец перед удалением

## Бизнес-правила

| Код | Правило | Слой | Проверка |
|-----|---------|------|----------|
| BR-1 | Уникальность названия предпочтения в пределах пользователя | Приложение | CreatePreference, UpdatePreference |
| BR-2 | Если тип ALLERGY, режим обязательно BLOCKED | Доменный | Preference.__post_init__ |
| BR-2a | Если тип CATEGORY_BASED, product_ids должны быть пусты | Доменный | Preference.__post_init__ |
| BR-3 | На члене семьи не могут быть одновременно BLOCKED и ALLOWED предпочтения | Приложение | AssignPreferencesToMember._validate_mode_compatibility |
| BR-9 | Если продукт не категоризирован (category_id == 0), ALLOWED предпочтения не соответствуют | Доменный | PreferenceMatcher._matches_allowed |
| EC-1 | Пустой рецепт (без ингредиентов) не соответствует ALLOWED предпочтениям | Доменный | PreferenceMatcher._matches_allowed |

## Типичные сценарии использования

### Сценарий 1: Управление аллергией в семье

1. Пользователь создаёт предпочтение **«Аллергия на молоко»** (тип: ALLERGY)
   - Выбирает продукты: Молоко, Йогурт, Сыр
2. Назначает это предпочтение члену семьи (например, ребёнку)
3. При планировании меню: выбирает этого ребёнка
4. Система отображает красный чип **«Аллергия на молоко»** над сеткой
5. Рецепты, содержащие молочные продукты, затемняются и сортируются в конец
6. На странице таких рецептов показывается красный значок предпочтения

### Сценарий 2: Диета без глютена

1. Пользователь создаёт предпочтение **«Без глютена»** (тип: По категориям, режим: Блокировать)
   - Выбирает категории: Крупы, Хлеб, Макароны
2. Назначает предпочтение члену семьи
3. При планировании меню: выбирает этого члена
4. Система отображает жёлтый чип **«Без глютена»**
5. Рецепты с глютеном затемняются

### Сценарий 3: Вегетарианская диета (ALLOWED)

1. Пользователь создаёт предпочтение **«Только овощи»** (тип: По категориям, режим: Разрешать)
   - Выбирает категории: Овощи, Фрукты, Зелень, Бобовые
2. Назначает предпочтение члену семьи
3. При планировании меню: выбирает этого члена
4. Система отображает зелёный чип **«Только овощи»**
5. Только рецепты, содержащие ТОЛЬКО эти категории, совместимы
6. Все остальные рецепты (содержащие мясо, рыбу и т.д.) затемняются

### Сценарий 4: Рецепт с вложенными предпочтениями

1. Основной рецепт A содержит подрецепт B
2. Подрецепт B содержит молочные продукты
3. Предпочтение **«Аллергия на молоко»** активно
4. Система рекурсивно разрешает подрецепт B → находит молочные продукты
5. Помечает рецепт A как несовместимый
6. Рецепт A затемняется в списке

## Проверка совместимости (Matching)

### Алгоритм ALLERGY

```
matches_allergy(product_ids, category_ids, preference):
    if product_ids ∩ preference.product_ids != ∅: return false
    if category_ids ∩ preference.category_ids != ∅: return false
    return true
```

### Алгоритм BLOCKED

```
matches_blocked(category_ids, preference):
    if category_ids ∩ preference.category_ids != ∅: return false
    return true
```

### Алгоритм ALLOWED

```
matches_allowed(product_ids, category_ids, preference, has_uncategorized):
    if product_ids.empty(): return false              # EC-1
    if has_uncategorized: return false                # BR-9
    if category_ids ⊄ preference.category_ids: return false
    return true
```

Где ⊄ означает "не содержится в" (любая категория рецепта должна быть в allowed_categories).

## Интеграция в Composition Root

**Файл:** `backend/composition_root.py`

```python
class ApplicationContainer:
    def __init__(self, session: Session) -> None:
        # ... existing code ...
        
        # Preference repositories and services
        self._preference_repo = OrmPreferenceRepository(session)
        self._preference_matcher = PreferenceMatcher(self._recipe_repo, self._product_repo)
        
        # Preference use cases
        self.create_preference = CreatePreference(self._preference_repo)
        self.update_preference = UpdatePreference(self._preference_repo)
        self.delete_preference = DeletePreference(self._preference_repo, self._family_repo)
        self.list_preferences = ListPreferences(self._preference_repo)
        self.get_preference = GetPreference(self._preference_repo)
        self.assign_preferences = AssignPreferencesToMember(self._family_repo, self._preference_repo)
        self.match_recipe_preferences = MatchRecipePreferences(
            self._recipe_repo, self._preference_repo, self._preference_matcher
        )
```

## Примечания для разработчиков

1. **Типизированные ID:** PreferenceId, PreferenceType, PreferenceMode используют NewType для type-safety
2. **Многопользовательская поддержка:** Все операции фильтруются по user_id на уровне приложения и инфраструктуры
3. **Рекурсивное разрешение:** PreferenceMatcher поддерживает arbitrary глубину вложенных рецептов благодаря visited set
4. **Cascade удаление:** При удалении предпочтения оно автоматически удаляется из всех членов семьи на уровне приложения (cascade на БД для orphan-удаления)
5. **BR-3 валидация:** Выполняется на уровне применения при назначении предпочтений, использует эффективный режим (ALLERGY всегда считается BLOCKED)
6. **Состояние фронтенда:** usePreferenceFilter composable вычисляет в реальном времени на основе активных членов семьи, не требует синхронизации с бэкендом
