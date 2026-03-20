# Архитектура — Чистая архитектура + API адаптер

## Обзор

Menu Planner использует **Чистую архитектуру** с 4-слойным дизайном плюс API и фронтенд адаптеры. Основной принцип — **инверсия зависимостей**: бизнес-логика полностью развязана от фреймворков, БД и UI технологий.

```
┌───────────────────────────────────────────────────────┐
│                    Фронтенд (Vue 3 SPA)                │
└───────────────────────────────────────────────────────┘
                          ↓ (HTTP)
┌───────────────────────────────────────────────────────┐
│              API адаптер слой (FastAPI)                │
│  Маршрутизаторы, Pydantic схемы, Конвертеры, Auth    │
└───────────────────────────────────────────────────────┘
                          ↓ (Use Case)
┌───────────────────────────────────────────────────────┐
│            Слой приложения (Use Cases)                │
│      Оркестрация, DTO, границы транзакции            │
└───────────────────────────────────────────────────────┘
                          ↓ (Доменные объекты)
┌───────────────────────────────────────────────────────┐
│      Доменный слой (Сущности, Объекты-значения)      │
│          Бизнес-правила, Ноль кода фреймворка        │
└───────────────────────────────────────────────────────┘
                          ↓ (Порты)
┌───────────────────────────────────────────────────────┐
│         Инфраструктурный слой (Репозитории, Auth)     │
│     База данных, File I/O, Внешние сервисы           │
└───────────────────────────────────────────────────────┘
```

## Правило зависимостей

Зависимости всегда указывают **внутрь** в сторону домена:

```
Фронтенд → API → Приложение → Доменный слой ← Инфраструктура
                                ↑
                                │ (реализует)
                                │
                          Инфраструктура
```

- **Доменный слой** не зависит от чего-либо
- **Приложение** зависит только от домена
- **Инфраструктура** зависит от портов доменного слоя (интерфейсов)
- **API** зависит от приложения и домена
- **Фронтенд** зависит от API через HTTP вызовы

Это позволяет:
- Тестировать логику доменного слоя без мокирования
- Менять фреймворки без изменения бизнес-логики
- Легко понять поток данных

## Ответственность слоев

| Слой | Знает о | Невежественна о | Ответственность |
|-------|------------|------------|-----------------|
| **Доменный** | Сущности, Объекты-значения, Порты | FastAPI, SQLAlchemy, Vue | Бизнес-правила, валидации, вычисления |
| **Приложение** | Доменный слой, Use case паттерны | БД, HTTP, UI | Оркестрировать логику домена, управлять транзакции |
| **Инфраструктура** | Порты домена, SQLAlchemy, bcrypt | Use cases, маршрутизаторы | Реализовать репозитории, персистентность, аутентификация |
| **API** | Маршруты, Pydantic, Доменные сущности | Бизнес-логика | Принять HTTP запросы, конвертировать в/из домена |
| **Фронтенд** | Vue 3, Pinia, axios | База данных, логика домена | Пользовательский интерфейс, управление состояния, события |

---

## 1. Доменный слой (`backend/domain/`)

**Ноль внешних зависимостей. Чистая Python бизнес-логика.**

### Сущности

Сущности имеют идентичность (ID) и изменяемое состояние. Они содержат бизнес-правила о допустимых состояниях.

#### Recipe

Файл: `backend/domain/entities/recipe.py`

```python
@dataclass
class Recipe:
    id: RecipeId
    name: str
    servings: int
    ingredients: list[RecipeIngredient]     # Объекты-значения
    steps: list[CookingStep]                 # Объекты-значения
    category_id: RecipeCategoryId
    weight: int                              # граммы, опционально
    user_id: UserId                          # Многопользовательское ограничение области
    total_pieces: int | None = None          # Для рецептов на основе штук
    pieces_per_portion: int | None = None
```

**Ключевой метод:** `scale_to(target_servings: float) → Recipe`

Масштабирует количества ингредиентов при сохранении неизменяемости (возвращает новый рецепт).

**Инварианты:**
- `total_pieces` и `pieces_per_portion` должны оба быть установлены или оба None
- Если установлены: `pieces_per_portion ≤ total_pieces` и оба ≥ 1

#### Product

Файл: `backend/domain/entities/product.py`

```python
@dataclass
class Product:
    id: ProductId
    name: str
    category_id: ProductCategoryId
    recipe_unit: str                        # "g", "kg", "ml", "l", "pcs", и т.д.
    purchase_unit: str                      # Единица, в которой обычно покупается
    price_per_purchase_unit: Money          # Объект-значение
    conversion_factor: float                 # например, 1000 для преобразования g → kg
    user_id: UserId
```

#### Menu & MenuSlot

Меню = именованная коллекция слотов. Слот = рецепт/продукт + количество + тип приема пищи + день.

```python
@dataclass
class Menu:
    id: MenuId
    name: str
    created_at: datetime
    user_id: UserId
    slots: list[MenuSlot] = field(default_factory=list)

@dataclass
class MenuSlot:
    id: MenuSlotId
    recipe_id: RecipeId | None              # Либо рецепт XOR продукт
    product_id: ProductId | None
    quantity: Quantity | None                # Для продуктов
    servings: int | None                     # Для рецептов
    meal_type: str                          # "завтрак", "обед", "ужин"
    day_of_week: int                        # 0=Пн, 6=Вс
    position: int                           # Упорядочение внутри одинакового (день, meal_type)
```

#### ShoppingList & ShoppingListItem

Результат агрегирования рецептов по меню пользователя + члены семьи.

```python
@dataclass
class ShoppingList:
    items: list[ShoppingListItem]
    total_cost: Money

@dataclass
class ShoppingListItem:
    product_id: ProductId
    name: str
    quantity: Quantity
    price_per_unit: Money
    total_cost: Money
    category_id: ProductCategoryId
    purchased: bool = False                 # Отслеживание состояния check-off
```

#### User & RefreshToken

Сущности аутентификации:

```python
@dataclass
class User:
    id: UserId
    email: str
    nickname: str
    password_hash: str
    created_at: datetime

@dataclass
class RefreshToken:
    id: RefreshTokenId
    user_id: UserId
    token_hash: str                         # Хеш JWT (не хранится открытым текстом)
    expires_at: datetime
    created_at: datetime
    revoked: bool = False
```

#### FamilyMember

```python
@dataclass
class FamilyMember:
    id: FamilyMemberId
    name: str
    portion_multiplier: float               # например, 0.5 для ребенка, 1.0 для взрослого
    dietary_restrictions: str | None        # например, "vegetarian, nut allergy"
    user_id: UserId
```

### Объекты-значения

Объекты-значения неизменяемы, не имеют идентичности и идентифицируются их атрибутами. Центральны к логике домена.

#### Quantity

Файл: `backend/domain/value_objects/quantity.py`

**Наиболее сложный объект-значение.** Обрабатывает преобразование единиц и арифметику.

```python
@dataclass(frozen=True)
class Quantity:
    amount: float
    unit: str                               # "g", "kg", "ml", "l", "pcs", и т.д.

    def __add__(self, other: "Quantity") -> "Quantity":
        """Добавить количества с автоматическим преобразованием (например, 200g + 1kg = 1200g)."""
        if same_group(self.unit, other.unit):
            # Преобразовать в общую единицу, добавить, вернуть
            ...
        raise IncompatibleUnitsError(...)

    def to_unit(self, target_unit: str) -> "Quantity":
        """Преобразовать в другую единицу в той же группе."""
        ...
```

**Группы единиц:**
- **Вес:** g ↔ kg (1000)
- **Объем:** ml ↔ l (1000)
- **Подсчет:** pcs (без преобразования)
- **Сухое:** tsp ↔ tbsp (3)

#### Money

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal                         # Точная валютная арифметика
    currency: str = "RUB"
```

#### RecipeIngredient

Связывает продукт с рецептом количеством.

```python
@dataclass(frozen=True)
class RecipeIngredient:
    product_id: ProductId
    sub_recipe_id: RecipeId | None          # Для вложенных рецептов
    quantity: Quantity
    order: int                              # Упорядочение внутри списка ингредиентов
```

#### CookingStep

```python
@dataclass(frozen=True)
class CookingStep:
    description: str
    order: int
```

#### Category

```python
@dataclass(frozen=True)
class Category:
    id: int
    name: str
    type: str                               # "product" или "recipe"
    active: bool = True
```

### Типизированные ID

Файл: `backend/domain/value_objects/types.py`

```python
RecipeId = NewType("RecipeId", int)
ProductId = NewType("ProductId", int)
MenuId = NewType("MenuId", int)
FamilyMemberId = NewType("FamilyMemberId", int)
ProductCategoryId = NewType("ProductCategoryId", int)
RecipeCategoryId = NewType("RecipeCategoryId", int)
UserId = NewType("UserId", int)
RefreshTokenId = NewType("RefreshTokenId", int)
```

**Почему?** mypy применяет корректные типы ID во время статического анализа:

```python
def get_recipe(recipe_id: RecipeId, user_id: UserId) -> Recipe:
    ...

get_recipe(ProductId(5), UserId(1))   # ✓ ошибка mypy: несовместимые типы
get_recipe(RecipeId(5), UserId(1))    # ✓ OK
```

Во время выполнения `RecipeId` — это просто `int`, поэтому нет затрат на производительность.

### Доменные сервисы

Логика без состояния, которая не подходит отдельной сущности.

#### ShoppingListBuilder

Файл: `backend/domain/services/shopping_list_builder.py`

Наиболее сложный доменный сервис. Оркестрирует:

1. Получить все рецепты из слотов меню (отфильтровано по дню + тип приема пищи)
2. Для каждого рецепта, масштабировать ингредиенты по множителям порции членов семьи
3. Агрегировать количества (сумма всей муки нужной, учитывая преобразование единиц)
4. Преобразовать в единицы покупки (например, g → kg)
5. Найти цены из продуктов
6. Рассчитать полную стоимость

```python
class ShoppingListBuilder:
    def build(
        self,
        menu: Menu,
        family_members: list[FamilyMember],
        products: dict[ProductId, Product],
        recipes: dict[RecipeId, Recipe],
    ) -> ShoppingList:
        """Построить список покупок из меню + семейные профили."""
```

#### PortionCalculator

Рассчитывает полное количество порций на основе членов семьи.

```python
def calculate_total_servings(family_members: list[FamilyMember]) -> float:
    """1.0 + 1.0 + 0.5 = 2.5 для 3-человечной семьи (2 взрослых, 1 ребенок)."""
    return sum(fm.portion_multiplier for fm in family_members)
```

#### UnitConverter

Преобразует между совместимыми единицами (g ↔ kg, ml ↔ l, tsp ↔ tbsp).

```python
def convert(quantity: Quantity, target_unit: str) -> Quantity:
    """200g to kg → 0.2 kg"""
```

### Порты (интерфейсы)

Абстрактные интерфейсы, реализованные слоем инфраструктуры. Определены в `backend/domain/ports/`.

```python
# Порт RecipeRepository (ABC)
class RecipeRepository(ABC):
    @abstractmethod
    def get_by_id(self, recipe_id: RecipeId, user_id: UserId) -> Recipe | None:
        ...

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> list[Recipe]:
        ...

    @abstractmethod
    def save(self, recipe: Recipe) -> RecipeId:
        ...

    @abstractmethod
    def delete(self, recipe_id: RecipeId, user_id: UserId) -> None:
        ...
```

Другие порты:
- `ProductRepository`
- `MenuRepository`
- `FamilyMemberRepository`
- `UserRepository`
- `RefreshTokenRepository`
- `RecipeCategoryRepository`
- `ProductCategoryRepository`

### Исключения

Файл: `backend/domain/exceptions.py`

Доменные исключения (база: `DomainError`):

- `InvalidEntityError` — Нарушение инварианта сущности
- `EntityNotFoundError` — Запрошенная сущность не найдена
- `AuthenticationError` — Неверные учетные данные
- `CircularDependencyError` — Sub-recipe образует цикл
- `NestingDepthExceededError` — Глубина вложения sub-recipe слишком велика
- `SubRecipeWeightError` — Sub-recipe без веса для выравнивания

---

## 2. Слой приложения (`backend/application/use_cases/`)

**Оркестрирует логику домена. Один класс = одна пользовательская операция.**

### Паттерн: Use case (Interactor)

Каждый use case — это класс с методом `execute()`. Обрабатывает:
- Валидацию входных данных (через DTO)
- Границы транзакции
- Обработку ошибок
- Вызовы репозитория (внедрение зависимостей)

### Пример: CreateRecipe

```python
class CreateRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self, user_id: UserId, name: str, servings: int,
        category_id: RecipeCategoryId, ingredients: list[...], steps: list[...]
    ) -> RecipeId:
        # Валидировать входные данные
        if not name.strip():
            raise DomainError("Требуется имя рецепта")

        # Создать доменную сущность
        recipe = Recipe(
            id=RecipeId(0),  # БД присвоит реальный ID
            name=name,
            servings=servings,
            category_id=category_id,
            ingredients=ingredients,
            steps=steps,
            user_id=user_id,
        )

        # Персистировать
        return self.recipe_repo.save(recipe)
```

### Инвентарь use case

| Файл | Use cases |
|------|-----------|
| `auth.py` | `RegisterUser`, `LoginUser`, `RefreshAccessToken`, `GetCurrentUser` |
| `manage_recipe.py` | `GetRecipe`, `ListRecipes`, `CreateRecipe`, `UpdateRecipe`, `DeleteRecipe` |
| `manage_product.py` | `GetProduct`, `ListProducts`, `CreateProduct`, `UpdateProduct`, `DeleteProduct` |
| `manage_family.py` | `CreateFamilyMember`, `UpdateFamilyMember`, `DeleteFamilyMember`, `ListFamilyMembers` |
| `plan_menu.py` | `CreateMenu`, `LoadMenu`, `AddMenuSlot`, `UpdateMenuSlot`, `DeleteMenuSlot`, `ClearMenu` |
| `generate_shopping_list.py` | `GenerateShoppingList` (вызывает ShoppingListBuilder) |
| `flatten_recipe_products.py` | `FlattenRecipeProducts` (разворачивает sub-recipes) |
| `preview_flattened_products.py` | `PreviewFlattenedProducts` (dry-run выравнивания) |
| `validate_sub_recipe.py` | `ValidateSubRecipe` (обнаруживает циклы, глубину вложения) |
| `export_shopping_list.py` | `ExportShoppingList` (CSV/JSON/текст) |
| `export_entities.py` | `ExportEntities` (рецепты, продукты как JSON) |
| `import_entities.py` | `ImportEntities` (рецепты, продукты из JSON) |

---

## 3. Инфраструктурный слой (`backend/infrastructure/`)

**Реализует порты домена. БД, аутентификация, file I/O.**

### Реализация репозиториев

Файл: `backend/infrastructure/repositories/sqlalchemy_*.py`

Использует SQLAlchemy ORM для маппинга доменных сущностей в строки БД.

```python
class SqlalchemyRecipeRepository(RecipeRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, recipe_id: RecipeId, user_id: UserId) -> Recipe | None:
        row = self.session.query(RecipeRow).filter(
            RecipeRow.id == recipe_id,
            RecipeRow.user_id == user_id
        ).first()
        return recipe_row_to_domain(row) if row else None

    def save(self, recipe: Recipe) -> RecipeId:
        row = recipe_domain_to_row(recipe)
        self.session.add(row)
        self.session.flush()
        return RecipeId(row.id)
```

### Сервисы аутентификации

#### BcryptPasswordHasher

Файл: `backend/infrastructure/auth/bcrypt_password_hasher.py`

Реализует порт `PasswordHasher`:

```python
class BcryptPasswordHasher(PasswordHasher):
    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), hash.encode())
```

#### JwtTokenService

Файл: `backend/infrastructure/auth/jwt_token_service.py`

Реализует порт `TokenService`:

```python
class JwtTokenService(TokenService):
    def create_access_token(self, user_id: UserId, expires_in_minutes: int) -> str:
        payload = {
            "user_id": int(user_id),
            "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            "type": "access"
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def create_refresh_token(self, user_id: UserId, expires_in_days: int) -> str:
        payload = {
            "user_id": int(user_id),
            "exp": datetime.utcnow() + timedelta(days=expires_in_days),
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Токен истек")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Неверный токен")
```

### Настройка БД

#### ORM модели SQLAlchemy

Файл: `backend/infrastructure/database/models.py`

ORM модели маппинга в таблицы БД:

```python
class RecipeRow(Base):
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str]
    servings: Mapped[int]
    category_id: Mapped[int] = mapped_column(ForeignKey("recipe_categories.id"))
    weight: Mapped[int] = mapped_column(default=0)
    total_pieces: Mapped[int | None]
    pieces_per_portion: Mapped[int | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    ingredients: Mapped[list["RecipeIngredientRow"]] = relationship(back_populates="recipe")
    steps: Mapped[list["CookingStepRow"]] = relationship(back_populates="recipe")
    user: Mapped["UserRow"] = relationship(back_populates="recipes")
```

#### Миграции Alembic

Файл: `backend/infrastructure/database/migrations/versions/`

Каждая миграция — это timestamped Python файл:

```python
# Пример: add_ingredient_order.py
def upgrade() -> None:
    op.add_column('recipe_ingredients',
                  sa.Column('order', sa.Integer(), nullable=False, server_default='0'))

def downgrade() -> None:
    op.drop_column('recipe_ingredients', 'order')
```

Запустить: `alembic upgrade head`

#### Engine & Session

Файл: `backend/infrastructure/database/__init__.py`

```python
def get_engine(db_url: str | None = None) -> Engine:
    url = db_url or os.environ.get("DATABASE_URL", "sqlite:///test.db")
    return create_engine(url, echo=False)

def get_session(engine: Engine) -> Session:
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
```

### Экспортеры

Паттерн Strategy для экспорта без привязки к формату.

```python
class ShoppingListExporter(ABC):
    @abstractmethod
    def export(self, shopping_list: ShoppingList) -> str:
        pass

class CsvExporter(ShoppingListExporter):
    def export(self, shopping_list: ShoppingList) -> str:
        # Генерировать CSV с заголовками, группировкой категорий, затратами
        ...

class JsonExporter(ShoppingListExporter):
    def export(self, shopping_list: ShoppingList) -> str:
        # Генерировать JSON структуру
        ...
```

---

## 4. API слой (`backend/api/`)

**HTTP адаптер. Маршрутизаторы, схемы, конвертеры, auth middleware.**

### Настройка FastAPI приложения

Файл: `backend/api/main.py`

```python
app = FastAPI(
    title="Menutor API",
    lifespan=lifespan,  # Создает ApplicationContainer при запуске
)

# Middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Обработчики исключений (маппируют доменные ошибки HTTP ответам)
@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

# Маршрутизаторы
app.include_router(auth.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(products.router, prefix="/api")
# ... и т.д
```

### Аутентификационное middleware

Файл: `backend/api/auth.py`

```python
def get_current_user(
    request: Request,
    container: ApplicationContainer = Depends(get_container),
) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    token = auth_header.removeprefix("Bearer ")
    try:
        return container.get_current_user.execute(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
```

Все защищенные эндпоинты:

```python
@router.get("/recipes")
def list_recipes(
    user: User = Depends(get_current_user),  # Извлекает + валидирует JWT
    container: ApplicationContainer = Depends(get_container),
) -> list[RecipeResponse]:
    recipes = container.list_recipes.execute(user.id)
    return [recipe_to_response(r) for r in recipes]
```

### Pydantic схемы

Файл: `backend/api/schemas/recipe.py`

```python
class RecipeCreate(BaseModel):
    name: str
    servings: int
    category_id: int
    ingredients: list[RecipeIngredientCreate]
    steps: list[CookingStepCreate]

class RecipeResponse(BaseModel):
    id: int
    name: str
    servings: int
    category_id: int
    ingredients: list[RecipeIngredientResponse]
    steps: list[CookingStepResponse]
    weight: int
    total_pieces: int | None
    pieces_per_portion: int | None
```

### Конвертеры

Файл: `backend/api/converters.py`

Преобразует между Pydantic схемами и доменными сущностями:

```python
def recipe_to_response(recipe: Recipe, name_lookup) -> RecipeResponse:
    return RecipeResponse(
        id=int(recipe.id),
        name=recipe.name,
        servings=recipe.servings,
        category_id=int(recipe.category_id),
        ingredients=[
            RecipeIngredientResponse(
                product_id=int(ing.product_id),
                sub_recipe_id=int(ing.sub_recipe_id) if ing.sub_recipe_id else None,
                quantity_amount=ing.quantity.amount,
                quantity_unit=ing.quantity.unit,
                sub_recipe_name=name_lookup(ing.sub_recipe_id) if ing.sub_recipe_id else None,
            )
            for ing in recipe.ingredients
        ],
        steps=[...],
        weight=recipe.weight,
        total_pieces=recipe.total_pieces,
        pieces_per_portion=recipe.pieces_per_portion,
    )
```

### Эндпоинты маршрутизатора

Файл: `backend/api/routers/recipes.py`

Каждый маршрутизатор обрабатывает CRUD для одной доменной сущности:

```python
@router.get("", response_model=list[RecipeResponse])
def list_recipes(
    category_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
):
    recipes = container.list_recipes.execute(user.id, category_id)
    return [recipe_to_response(r) for r in recipes]

@router.post("", response_model=RecipeResponse, status_code=201)
def create_recipe(
    body: RecipeCreate,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
):
    recipe_id = container.create_recipe.execute(
        user_id=user.id,
        name=body.name,
        servings=body.servings,
        ...
    )
    recipe = container.get_recipe.execute(recipe_id, user.id)
    return recipe_to_response(recipe)

@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, body: RecipeUpdate, ...):
    ...

@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, ...):
    ...
```

**Маршрутизаторы (7 всего):**
- `auth.py` — вход, регистрация, обновление, меня, выход
- `recipes.py` — CRUD рецептов, список по категориям
- `products.py` — CRUD продуктов
- `menus.py` — CRUD меню, управление слотами
- `family.py` — CRUD членов семьи
- `categories.py` — CRUD категорий (продукта + рецепта)
- `shopping_list.py` — генерировать, экспортировать (CSV/JSON/текст)
- `import_export.py` — импорт/экспорт рецептов и продуктов
- `system.py` — проверка здоровья, версия

---

## 5. Фронтенд слой (`frontend/src/`)

**Vue 3 SPA с управлением состояния Pinia и стилем Tailwind CSS.**

### Структура проекта

```
frontend/src/
├── main.ts                       # Инициализация Vue приложения
├── App.vue                       # Root layout компонент (AppSidebar + router-view)
├── router/index.ts              # Конфигурация Vue Router (6 маршрутов + вложенные /settings)
├── stores/                       # Хранилища Pinia (реактивное состояние)
│   ├── auth.ts                  # Пользователь, токены доступа/обновления
│   ├── recipes.ts               # Список рецептов, CRUD операции
│   ├── products.ts              # Список продуктов, CRUD операции
│   ├── menus.ts                 # Состояние меню, управление слотом
│   ├── family.ts                # Члены семьи
│   ├── categories.ts            # Категории продукта/рецепта
│   ├── shoppingList.ts          # Состояние списка покупок, отслеживание затрат
│   ├── toast.ts                 # Очередь push-уведомлений
│   └── crud-factory.ts          # Генератор универсального CRUD хранилища
├── api/
│   ├── client.ts                # axios экземпляр с JWT перехватчиком
│   ├── auth.ts                  # Вызовы Auth API (register, login, refresh)
│   └── types.ts                 # TypeScript интерфейсы (совпадают с Pydantic)
├── views/                        # Компоненты уровня страницы
│   ├── AuthView.vue             # Страница входа/регистрации
│   ├── MenuPlannerView.vue      # Планировщик меню 7-дневный × 3-приема пищи
│   ├── ShoppingListView.vue     # Агрегированный список покупок
│   ├── RecipeListView.vue       # CRUD таблица рецептов + форма
│   ├── ProductListView.vue      # CRUD таблица продуктов + форма
│   └── SettingsView.vue         # Контейнер настроек (семья, категории, о программе)
├── components/                   # Переиспользуемые компоненты
│   ├── layout/                  # AppSidebar, MobileBottomNav
│   ├── planner/                 # PlannerGrid, GridCell, SourcePanel
│   ├── shopping/                # ShoppingTable, ShoppingSummary
│   ├── recipes/                 # RecipeTable, RecipeForm
│   ├── products/                # ProductTable, ProductForm
│   ├── settings/                # FamilyPanel, CategoryPanel, AboutPanel
│   └── ui/                      # ConfirmDialog, ToastNotification, и т.д.
├── composables/                  # Переиспользуемые функции компоновки
│   ├── useSelection.ts          # Логика многострочного выбора
│   ├── useDropdown.ts           # Состояние открытия/закрытия выпадающего списка
│   ├── useCategoryFilter.ts     # Логика фильтрации категорий
│   ├── useContextMenu.ts        # Контекстное меню правого клика
│   └── useFileDownload.ts       # Утилита загрузки blob/CSV экспорта
└── utils/                        # Функции утилиты
    └── units.ts                 # Преобразование единиц, форматирование
```

### Хранилища Pinia

**Паттерн:** Каждое хранилище управляет одним доменным понятием. Действия вызывают API-клиента. Состояние реактивно.

```typescript
export const useRecipeStore = defineStore('recipes', {
  state: () => ({
    recipes: [] as Recipe[],
    selectedRecipeId: null as RecipeId | null,
    loading: false,
    error: null as string | null,
  }),

  getters: {
    selectedRecipe(): Recipe | null {
      return this.recipes.find(r => r.id === this.selectedRecipeId) || null
    },
  },

  actions: {
    async loadRecipes() {
      this.loading = true
      try {
        this.recipes = await listRecipes()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async createRecipe(data: RecipeCreate) {
      const recipe = await createRecipe(data)
      this.recipes.push(recipe)
      return recipe
    },

    async updateRecipe(id: RecipeId, data: RecipeUpdate) {
      const recipe = await updateRecipe(id, data)
      const idx = this.recipes.findIndex(r => r.id === id)
      if (idx >= 0) this.recipes[idx] = recipe
      return recipe
    },

    async deleteRecipe(id: RecipeId) {
      await deleteRecipe(id)
      this.recipes = this.recipes.filter(r => r.id !== id)
    },
  },
})
```

### API клиент с JWT

Файл: `frontend/src/api/client.ts`

```typescript
const client: AxiosInstance = axios.create({
  baseURL: '/api',
})

// Перехватчик запроса: добавить JWT токен
client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// Перехватчик ответа: auto-refresh на 401
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    if (error.response?.status === 401 && auth.refreshToken) {
      try {
        const { access_token } = await refresh()
        auth.setAccessToken(access_token)
        // Повторить исходный запрос
        return client(error.config)
      } catch {
        auth.logout()
      }
    }
    return Promise.reject(error)
  }
)
```

### Vue router

Файл: `frontend/src/router/index.ts`

```typescript
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/planner',
  },
  {
    path: '/auth',
    component: AuthView,
    meta: { requiresAuth: false },
  },
  {
    path: '/planner',
    component: MenuPlannerView,
    meta: { requiresAuth: true },
  },
  {
    path: '/shopping-list',
    component: ShoppingListView,
    meta: { requiresAuth: true },
  },
  {
    path: '/recipes',
    component: RecipeListView,
    meta: { requiresAuth: true },
  },
  {
    path: '/products',
    component: ProductListView,
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    component: SettingsView,
    meta: { requiresAuth: true },
    redirect: '/settings/family',
    children: [
      { path: 'family', component: FamilyPanel },
      { path: 'product-categories', component: CategoryPanel, props: { type: 'product' } },
      { path: 'recipe-categories', component: CategoryPanel, props: { type: 'recipe' } },
      { path: 'about', component: AboutPanel },
    ],
  },
]

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/auth')
  } else {
    next()
  }
})
```

### Пример компонента: RecipeForm

```vue
<template>
  <form @submit.prevent="submit">
    <input v-model="form.name" placeholder="Имя рецепта" required />
    <select v-model="form.category_id" required>
      <option v-for="cat in categories" :value="cat.id">{{ cat.name }}</option>
    </select>
    <input v-model.number="form.servings" type="number" min="1" />

    <fieldset>
      <legend>Ингредиенты</legend>
      <div v-for="(ing, i) in form.ingredients" :key="i">
        <select v-model="ing.product_id">
          <option v-for="p in products" :value="p.id">{{ p.name }}</option>
        </select>
        <input v-model.number="ing.quantity_amount" type="number" step="0.01" />
        <span>{{ unitFor(ing.product_id) }}</span>
      </div>
      <button @click="addIngredient" type="button">+ Добавить</button>
    </fieldset>

    <button type="submit">Сохранить</button>
    <button @click="reset" type="button">Очистить</button>
  </form>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRecipeStore } from '@/stores/recipes'
import { useProductStore } from '@/stores/products'

const recipeStore = useRecipeStore()
const productStore = useProductStore()

const form = reactive({
  name: '',
  servings: 4,
  category_id: 0,
  ingredients: [],
  steps: [],
})

const submit = async () => {
  await recipeStore.createRecipe(form)
  reset()
}

const reset = () => {
  form.name = ''
  form.ingredients = []
}
</script>
```

---

## 6. Composition root (`backend/composition/`)

**Оркестрация внедрения зависимостей. Создает граф объектов.**

Файл: `backend/composition/container.py`

```python
class ApplicationContainer:
    """Создается один раз при запуске. Держит все use cases и репозитории."""

    def __init__(self, db_url: str | None = None) -> None:
        # 1. Создать инфраструктуру (БД, сервисы аутентификации)
        infra = _create_infrastructure(db_url)

        # 2. Подключить каждый доменный модуль (auth, рецепты, продукты, и т.д.)
        for name, obj in _wire_auth(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_recipes(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_products(infra).items():
            setattr(self, name, obj)
        # ... и т.д

        # 3. Сохранить подключение БД
        self._engine = infra.engine
        self._session = infra.session
```

Пример подключение (один модуль):

```python
# backend/composition/_recipes.py
def _wire_recipes(infra: Infrastructure) -> dict[str, Any]:
    recipe_repo = SqlalchemyRecipeRepository(infra.session)
    recipe_category_repo = SqlalchemyRecipeCategoryRepository(infra.session)

    list_recipes = ListRecipes(recipe_repo)
    get_recipe = GetRecipe(recipe_repo)
    create_recipe = CreateRecipe(recipe_repo)
    update_recipe = UpdateRecipe(recipe_repo)
    delete_recipe = DeleteRecipe(recipe_repo)
    flatten_recipe_products = FlattenRecipeProducts(recipe_repo)
    validate_sub_recipe = ValidateSubRecipe(recipe_repo)

    return {
        'list_recipes': list_recipes,
        'get_recipe': get_recipe,
        'create_recipe': create_recipe,
        'update_recipe': update_recipe,
        'delete_recipe': delete_recipe,
        'flatten_recipe_products': flatten_recipe_products,
        'validate_sub_recipe': validate_sub_recipe,
    }
```

---

## Используемые паттерны проектирования

| Паттерн | Применено к | Назначение |
|---------|-----------|---------|
| **Чистая архитектура** | Вся кодовая база | Слои, инверсия зависимостей, тестируемость |
| **Repository** | Все сущности | Абстрактный доступ к персистентности; заменяемые бэкенды |
| **Use case (Interactor)** | Слой приложения | Один класс = одна операция, изолированная, тестируемая |
| **Value object** | Quantity, Money, Category | Неизменяемо, нет идентичности, безопасная арифметика |
| **Domain service** | ShoppingListBuilder, UnitConverter | Логика, не подходящая отдельной сущности |
| **Dependency injection** | Composition root | Явное подключение, нет Service locator анти-паттерна |
| **Strategy** | Экспортеры (CSV, JSON, Text) | Взаимозаменяемые алгоритмы |
| **Adapter** | API слой | Преобразование HTTP ↔ доменные сущности |
| **Facade** | Хранилища Pinia | Упрощенный интерфейс API-клиента |
| **Observer** | Vue реактивность | Изменения состояния запускают переотрисовку компонента |
| **Interceptor** | axios + FastAPI middleware | Cross-cutting concerns (JWT, CORS) |

---

## Стратегия тестирования

```
                  Пирамида тестирования

                       /\
                      /  \        E2E / Smoke тесты (минимально)
                     /────\       Приложение запускается, основные рабочие процессы
                    /      \
                   /Integration\ Репозиторий тесты против реальной БД
                  /──────────────\  Экспорт/импорт тесты
                 /                \
                /    Unit тесты    \  Доменный слой: ноль мокирования
               /                    \ Приложение: моки только репо
              /──────────────────────\
```

| Тип теста | Расположение | Мокирование | Охват |
|-----------|----------|---------|----------|
| **Доменный unit** | `tests/unit/domain/` | Нет (чистые функции) | 95%+ |
| **Приложение unit** | `tests/unit/application/` | Моки репозиториев | 80%+ |
| **API unit** | `tests/unit/api/` | Моки контейнера, TestClient | 70%+ |
| **Интеграция** | `tests/integration/repositories/` | Реальный SQLite `:memory:` | 60%+ |

**Полный охват:** 490+ тестов проходят

---

**Далее:** См. [backend-domain.md](03-backend-domain.md) для подробных спецификаций сущности.
