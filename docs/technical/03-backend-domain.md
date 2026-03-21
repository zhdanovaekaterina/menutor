# Доменный слой — Сущности, Объекты-значения, Сервисы, Порты

Расположение файла: `backend/domain/`

Доменный слой содержит всю бизнес-логику и полностью независим от фреймворков. Он имеет **ноль зависимостей** от FastAPI, SQLAlchemy, Vue или любой внешней библиотеки.

---

## Сущности

Сущности имеют **идентичность** (ID) и изменяемое состояние. Они применяют бизнес-инварианты.

### Recipe

**Файл:** `backend/domain/entities/recipe.py`

```python
@dataclass
class Recipe:
    id: RecipeId
    name: str
    servings: int                          # Базовый размер порции
    ingredients: list[RecipeIngredient]    # Объекты-значения
    steps: list[CookingStep]               # Объекты-значения
    category_id: RecipeCategoryId
    weight: int = 0                        # Вес готового блюда в граммах (опционально)
    user_id: UserId = UserId(0)            # Многопользовательское ограничение
    total_pieces: int | None = None        # Для рецептов на основе штук (например, 12 печений)
    pieces_per_portion: int | None = None  # например, 3 печенья на порцию
```

**Инварианты (применяются в `__post_init__`):**
- Если `total_pieces` установлен, `pieces_per_portion` должен также быть установлен (и наоборот)
- Оба должны быть ≥ 1
- `pieces_per_portion ≤ total_pieces`

**Ключевые свойства:**

```python
@property
def is_pieces_mode(self) -> bool:
    """Возвращает True если рецепт использует масштабирование на основе штук."""
    return self.total_pieces is not None and self.pieces_per_portion is not None

@property
def computed_servings(self) -> int:
    """Вычисляет эффективные порции из штук если в штучном режиме, иначе использует servings."""
    if self.is_pieces_mode:
        return self.total_pieces // self.pieces_per_portion
    return self.servings
```

**Ключевой метод:**

```python
def scale_to(self, target_servings: float) -> Recipe:
    """
    Возвращает новый Recipe масштабированный к целевым порциям.
    Неизменяемость: исходный рецепт не изменяется.

    Пример:
        recipe.scale_to(6)  # Масштабировать с 4 порций на 6
    """
    factor = target_servings / self.servings
    scaled_ingredients = [
        RecipeIngredient(
            product_id=ing.product_id,
            sub_recipe_id=ing.sub_recipe_id,
            quantity=Quantity(ing.quantity.amount * factor, ing.quantity.unit),
            order=ing.order,
        )
        for ing in self.ingredients
    ]
    # Пересчитать total_pieces если в штучном режиме
    new_total_pieces = None
    if self.is_pieces_mode:
        assert self.total_pieces is not None
        new_total_pieces = max(1, round(self.total_pieces * factor))

    return Recipe(
        id=self.id,
        name=self.name,
        servings=round(target_servings),
        ingredients=scaled_ingredients,
        steps=list(self.steps),
        category_id=self.category_id,
        weight=self.weight,
        user_id=self.user_id,
        total_pieces=new_total_pieces,
        pieces_per_portion=self.pieces_per_portion,
    )
```

**Пример use case:**

```python
# Планировщик меню масштабирует рецепт на основе семьи
menu_recipe = recipe.scale_to(4)  # 2 взрослых (×1.0 каждый) + 1 ребенок (×0.5) = 2.5 → округлить на 4
ingredients_needed = menu_recipe.ingredients  # Количества уже масштабированы
```

### Product

**Файл:** `backend/domain/entities/product.py`

```python
@dataclass
class Product:
    id: ProductId
    name: str
    category_id: ProductCategoryId
    recipe_unit: str                       # Единица используемая в рецептах (например, "g", "ml", "pcs")
    purchase_unit: str                     # Единица для покупки (например, "kg", "l", "box")
    price_per_purchase_unit: Money         # Объект-значение: цена в RUB
    conversion_factor: float               # например, 1000 (для преобразования g → kg)
    user_id: UserId = UserId(0)
    brand: str = ""                        # Опционально: марка продукта
    supplier: str = ""                     # Опционально: типичный поставщик/розница
```

**Пример:**
```python
flour = Product(
    id=ProductId(1),
    name="Мука пшеничная",
    recipe_unit="g",
    purchase_unit="kg",
    price_per_purchase_unit=Money(Decimal("80.00")),
    conversion_factor=1000,
)
# В рецепте: 200g → стоимость = (200 / 1000) * 80.00 = 16.00 RUB
```

### Menu & MenuSlot

**Файл:** `backend/domain/entities/menu.py`

Меню — это именованная коллекция слотов приема пищи на неделю.

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
    menu_id: MenuId
    recipe_id: RecipeId | None = None              # Либо рецепт ИЛИ продукт (XOR)
    product_id: ProductId | None = None
    quantity: Quantity | None = None               # Для продуктов
    servings: int | None = None                    # Для рецептов
    meal_type: str = "обед"                        # "завтрак", "обед", "ужин"
    day_of_week: int = 0                           # 0=Пн, ..., 6=Вс
    position: int = 0                              # Упорядочение внутри (день, meal_type)
```

**Инвариант:** `(recipe_id is None) XOR (product_id is None)` — либо рецепт, либо продукт, никогда оба.

**Use case:**
```python
# Планирование недели для 2.5 эффективных порций (2 взрослых × 1.0 + 1 ребенок × 0.5)
menu_slot = MenuSlot(
    recipe_id=RecipeId(5),  # "Блины" (блины)
    servings=4,             # Масштабировать на 4 порции
    meal_type="завтрак",
    day_of_week=0,          # Понедельник
)

recipe = get_recipe(menu_slot.recipe_id)  # "Блины" с 4 порциями базовой
scaled = recipe.scale_to(menu_slot.servings * 2.5 / recipe.computed_servings)  # Масштабировать на семью
ingredients = scaled.ingredients  # Использовать для списка покупок
```

### ShoppingList & ShoppingListItem

**Файл:** `backend/domain/entities/shopping_list.py`

Результат агрегирования рецептов по меню пользователя + члены семьи. Содержит итоговый, дедублированный список продуктов с затратами.

```python
@dataclass
class ShoppingList:
    items: list[ShoppingListItem]
    total_cost: Money

@dataclass
class ShoppingListItem:
    id: ShoppingListItemId = field(default_factory=lambda: ShoppingListItemId(0))
    product_id: ProductId = ProductId(0)
    name: str = ""
    quantity: Quantity = field(default_factory=lambda: Quantity(0, "g"))
    price_per_unit: Money = field(default_factory=lambda: Money(Decimal("0.00")))
    total_cost: Money = field(default_factory=lambda: Money(Decimal("0.00")))
    category_id: ProductCategoryId = ProductCategoryId(0)
    purchased: bool = False                        # Отслеживание состояния check-off
```

**Пример:**
```python
item = ShoppingListItem(
    product_id=ProductId(1),
    name="Мука",
    quantity=Quantity(1.2, "kg"),        # 200g из блинов + 400g из хлеба + 600g из торта
    price_per_unit=Money(Decimal("80")),
    total_cost=Money(Decimal("96.00")),  # 1.2 * 80
    category_id=ProductCategoryId(2),    # "Сыпучие" (сухие товары)
)
```

### User & RefreshToken

**Файл:** `backend/domain/entities/user.py` и `refresh_token.py`

```python
@dataclass
class User:
    id: UserId
    email: str
    nickname: str
    password_hash: str                     # bcrypt хеш (никогда открытый текст)
    created_at: datetime

@dataclass
class RefreshToken:
    id: RefreshTokenId
    user_id: UserId
    token_hash: str                        # Хеш JWT токена (не хранится открытым)
    expires_at: datetime
    created_at: datetime
    revoked: bool = False                  # Мягкая отмена (выход)
```

### FamilyMember

**Файл:** `backend/domain/entities/family_member.py`

```python
@dataclass
class FamilyMember:
    id: FamilyMemberId
    name: str
    portion_multiplier: float = 1.0        # 1.0 = взрослый, 0.5 = ребенок
    dietary_restrictions: str = ""         # например, "vegetarian, nut allergy" (свободный текст)
    user_id: UserId = UserId(0)
    comment: str = ""                      # Опциональные примечания

    def effective_servings(self, base_servings: int) -> float:
        """Вычисляет порцию этого члена рецепта."""
        return base_servings * self.portion_multiplier
```

---

## Объекты-значения

Объекты-значения **неизменяемы**, идентифицируются их атрибутами (не ID), и не могут существовать независимо от сущности.

### Quantity

**Файл:** `backend/domain/value_objects/quantity.py`

Наиболее важный объект-значение. Обрабатывает преобразование единиц и арифметику.

```python
@dataclass(frozen=True)
class Quantity:
    amount: float
    unit: str  # "g", "kg", "ml", "l", "pcs", "tsp", "tbsp", и т.д.

    def to_unit(self, target_unit: str) -> "Quantity":
        """Преобразовать в другую единицу в той же группе."""
        if self.unit == target_unit:
            return self
        factor = unit_conversion_factor(self.unit, target_unit)
        return Quantity(self.amount * factor, target_unit)

    def __add__(self, other: "Quantity") -> "Quantity":
        """Добавить количества с автоматическим преобразованием."""
        if self.unit == other.unit:
            return Quantity(self.amount + other.amount, self.unit)

        # Попытаться найти общую единицу
        if are_compatible(self.unit, other.unit):
            other_converted = other.to_unit(self.unit)
            return Quantity(self.amount + other_converted.amount, self.unit)

        raise IncompatibleUnitsError(f"Не удается добавить {self.unit} + {other.unit}")
```

**Группы единиц:**
```
Вес:   g ↔ kg  (множитель: 1000)
Объем:   ml ↔ l  (множитель: 1000)
Кулинария:  tsp ↔ tbsp  (множитель: 3)
Подсчет:    pcs (без преобразования)
```

**Пример:**
```python
flour_1 = Quantity(200, "g")
flour_2 = Quantity(0.5, "kg")
total = flour_1 + flour_2  # Quantity(700, "g") или Quantity(0.7, "kg")

milk = Quantity(250, "ml")
milk_l = milk.to_unit("l")  # Quantity(0.25, "l")

apples = Quantity(5, "pcs")  # Штуки не преобразуются
```

### Money

**Файл:** `backend/domain/value_objects/money.py`

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal  # Используйте Decimal для точной валютной математики
    currency: str = "RUB"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Не удается добавить разные валюты")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: float) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)
```

**Пример:**
```python
price_per_kg = Money(Decimal("80.00"), "RUB")
quantity_kg = 1.2
total = price_per_kg.multiply(quantity_kg)  # Money(Decimal("96.00"), "RUB")

cost_1 = Money(Decimal("100"), "RUB")
cost_2 = Money(Decimal("50"), "RUB")
total_cost = cost_1 + cost_2  # Money(Decimal("150"), "RUB")
```

### RecipeIngredient

**Файл:** `backend/domain/value_objects/recipe_ingredient.py`

Связывает продукт с рецептом.

```python
@dataclass(frozen=True)
class RecipeIngredient:
    product_id: ProductId
    sub_recipe_id: RecipeId | None = None  # Для вложенных рецептов
    quantity: Quantity = field(default_factory=lambda: Quantity(0, "g"))
    order: int = 0                         # Позиция в списке ингредиентов

    def is_sub_recipe(self) -> bool:
        return self.sub_recipe_id is not None

    def is_product(self) -> bool:
        return self.sub_recipe_id is None
```

**Пример:**
```python
# Рецепт "Борщ" включает свеклу (продукт) и "Овощной бульон" (sub-recipe)
ing_1 = RecipeIngredient(product_id=ProductId(5), quantity=Quantity(500, "g"), order=1)
ing_2 = RecipeIngredient(sub_recipe_id=RecipeId(3), quantity=Quantity(1, "l"), order=2)
```

### CookingStep

**Файл:** `backend/domain/value_objects/cooking_step.py`

```python
@dataclass(frozen=True)
class CookingStep:
    description: str
    order: int

    def __lt__(self, other: "CookingStep") -> bool:
        return self.order < other.order
```

### Category

**Файл:** `backend/domain/value_objects/category.py`

```python
@dataclass(frozen=True)
class Category:
    id: int
    name: str
    type: str  # "product" или "recipe"
    active: bool = True
```

### Типизированные ID

**Файл:** `backend/domain/value_objects/types.py`

Использование `NewType` предотвращает путаницу разных типов ID во время статического анализа:

```python
from typing import NewType

RecipeId = NewType("RecipeId", int)
ProductId = NewType("ProductId", int)
MenuId = NewType("MenuId", int)
FamilyMemberId = NewType("FamilyMemberId", int)
ProductCategoryId = NewType("ProductCategoryId", int)
RecipeCategoryId = NewType("RecipeCategoryId", int)
UserId = NewType("UserId", int)
RefreshTokenId = NewType("RefreshTokenId", int)
MenuSlotId = NewType("MenuSlotId", int)
ShoppingListItemId = NewType("ShoppingListItemId", int)
```

**Почему?** mypy применяет корректные типы ID во время компиляции:

```python
def get_recipe(recipe_id: RecipeId, user_id: UserId) -> Recipe:
    ...

# ✗ ошибка mypy: несовместимые типы в аргументе 1
get_recipe(ProductId(5), UserId(1))

# ✓ OK
get_recipe(RecipeId(5), UserId(1))
```

Во время выполнения `RecipeId` — это просто `int`, поэтому нет затрат на производительность.

---

## Доменные сервисы

Логика без состояния, которая не подходит отдельной сущности.

### ShoppingListBuilder

**Файл:** `backend/domain/services/shopping_list_builder.py`

Наиболее сложный доменный сервис. Преобразует меню + членов семьи в дедублированный, отслеживаемый по затратам список покупок.

```python
class ShoppingListBuilder:
    def build(
        self,
        menu: Menu,
        family_members: list[FamilyMember],
        products: dict[ProductId, Product],
        recipes: dict[RecipeId, Recipe],
    ) -> ShoppingList:
        """
        Построить список покупок из меню на основе:
        1. Получить все рецепты из слотов меню
        2. Масштабировать по множителям порции членов семьи
        3. Агрегировать количества (сумма + преобразование единиц)
        4. Преобразовать в единицы покупки
        5. Рассчитать затраты
        """
        # Рассчитать полные эффективные порции
        total_servings = sum(fm.portion_multiplier for fm in family_members)

        # Агрегировать количества продуктов
        product_quantities: dict[ProductId, Quantity] = {}
        for slot in menu.slots:
            if slot.recipe_id:
                recipe = recipes[slot.recipe_id]
                scaled_recipe = recipe.scale_to(slot.servings * total_servings / recipe.servings)
                for ingredient in scaled_recipe.ingredients:
                    if ingredient.product_id in product_quantities:
                        product_quantities[ingredient.product_id] += ingredient.quantity
                    else:
                        product_quantities[ingredient.product_id] = ingredient.quantity

        # Создать элементы списка покупок
        items = []
        total_cost = Money(Decimal("0.00"))
        for product_id, quantity in product_quantities.items():
            product = products[product_id]

            # Преобразовать в единицу покупки
            converted = quantity.to_unit(product.purchase_unit)

            # Рассчитать стоимость
            item_cost = product.price_per_purchase_unit.multiply(converted.amount)
            total_cost = total_cost + item_cost

            items.append(ShoppingListItem(
                product_id=product_id,
                name=product.name,
                quantity=converted,
                price_per_unit=product.price_per_purchase_unit,
                total_cost=item_cost,
                category_id=product.category_id,
            ))

        return ShoppingList(items=items, total_cost=total_cost)
```

**Пример:**
```python
menu = Menu(id=MenuId(1), ...)  # 7-дневный план питания
family = [
    FamilyMember(name="Мама", portion_multiplier=1.0),
    FamilyMember(name="Папа", portion_multiplier=1.0),
    FamilyMember(name="Сын", portion_multiplier=0.5),
]  # Итого: 2.5 порций

shopping_list = builder.build(menu, family, products, recipes)
# Результат: агрегированные продукты с затратами для 2.5 порций
```

### PortionCalculator

**Файл:** `backend/domain/services/portion_calculator.py`

```python
class PortionCalculator:
    @staticmethod
    def calculate_total_servings(family_members: list[FamilyMember]) -> float:
        """Сумма всех множителей порции."""
        return sum(fm.portion_multiplier for fm in family_members)

    @staticmethod
    def calculate_portions_per_member(
        base_servings: int,
        family_members: list[FamilyMember],
    ) -> dict[FamilyMemberId, float]:
        """Карта каждого члена семьи на их размер порции."""
        return {
            fm.id: base_servings * fm.portion_multiplier
            for fm in family_members
        }
```

### UnitConverter

**Файл:** `backend/domain/services/unit_converter.py`

```python
class UnitConverter:
    # Группы единиц и коэффициенты преобразования
    WEIGHT_UNITS = {"g": 1, "kg": 1000}
    VOLUME_UNITS = {"ml": 1, "l": 1000}
    COOKING_UNITS = {"tsp": 1, "tbsp": 3}

    @staticmethod
    def convert(quantity: Quantity, target_unit: str) -> Quantity:
        """Преобразовать в другую единицу в той же группе."""
        if quantity.unit == target_unit:
            return quantity
        return quantity.to_unit(target_unit)

    @staticmethod
    def get_unit_group(unit: str) -> str | None:
        """Возвращает имя группы или None если не преобразуемо."""
        if unit in UnitConverter.WEIGHT_UNITS:
            return "weight"
        elif unit in UnitConverter.VOLUME_UNITS:
            return "volume"
        elif unit in UnitConverter.COOKING_UNITS:
            return "cooking"
        return None
```

---

## Порты (абстрактные интерфейсы)

Порты определяют контракт между доменным слоем и инфраструктурой. Инфраструктура реализует эти порты.

**Расположение:** `backend/domain/ports/`

### RecipeRepository

```python
class RecipeRepository(ABC):
    @abstractmethod
    def get_by_id(self, recipe_id: RecipeId, user_id: UserId) -> Recipe | None:
        """Получить рецепт по ID, ограниченный пользователем."""
        pass

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> list[Recipe]:
        """Вывести все рецепты пользователя."""
        pass

    @abstractmethod
    def list_by_category(
        self, user_id: UserId, category_id: RecipeCategoryId
    ) -> list[Recipe]:
        """Вывести рецепты в категории."""
        pass

    @abstractmethod
    def save(self, recipe: Recipe) -> RecipeId:
        """Создать или обновить рецепт. Возвращает ID."""
        pass

    @abstractmethod
    def delete(self, recipe_id: RecipeId, user_id: UserId) -> None:
        """Мягкое или жесткое удаление."""
        pass
```

### ProductRepository

```python
class ProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, product_id: ProductId, user_id: UserId) -> Product | None:
        pass

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> list[Product]:
        pass

    @abstractmethod
    def list_by_category(
        self, user_id: UserId, category_id: ProductCategoryId
    ) -> list[Product]:
        pass

    @abstractmethod
    def save(self, product: Product) -> ProductId:
        pass

    @abstractmethod
    def delete(self, product_id: ProductId, user_id: UserId) -> None:
        pass
```

### MenuRepository

```python
class MenuRepository(ABC):
    @abstractmethod
    def get_by_id(self, menu_id: MenuId, user_id: UserId) -> Menu | None:
        pass

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> list[Menu]:
        pass

    @abstractmethod
    def save(self, menu: Menu) -> MenuId:
        pass

    @abstractmethod
    def delete(self, menu_id: MenuId, user_id: UserId) -> None:
        pass

    @abstractmethod
    def add_slot(self, menu_id: MenuId, slot: MenuSlot) -> MenuSlotId:
        pass

    @abstractmethod
    def update_slot(self, slot: MenuSlot) -> None:
        pass

    @abstractmethod
    def delete_slot(self, menu_id: MenuId, slot_id: MenuSlotId) -> None:
        pass
```

### Другие порты

- `FamilyMemberRepository` — CRUD членов семьи
- `UserRepository` — CRUD пользователей, поиск по email
- `RefreshTokenRepository` — CRUD refresh токенов
- `RecipeCategoryRepository` — CRUD категорий рецептов
- `ProductCategoryRepository` — CRUD категорий продуктов
- `PasswordHasher` — хеширование и проверка пароля
- `TokenService` — создание и валидация JWT

---

## Исключения

**Файл:** `backend/domain/exceptions.py`

Все доменные исключения наследуют от `DomainError`.

```python
class DomainError(Exception):
    """База для всех доменных ошибок."""
    pass

class InvalidEntityError(DomainError):
    """Нарушение инварианта сущности (например, servings < 1)."""
    pass

class EntityNotFoundError(DomainError):
    """Запрошенная сущность не найдена."""
    pass

class AuthenticationError(DomainError):
    """Неверные учетные данные или токен."""
    pass

class CircularDependencyError(DomainError):
    """Рецепт A включает рецепт B который включает рецепт A."""
    pass

class NestingDepthExceededError(DomainError):
    """Глубина вложения sub-recipe слишком велика (например, > 5 уровней)."""
    pass

class IncompatibleUnitsError(DomainError):
    """Не удается преобразовать между единицами (например, g + l)."""
    pass

class SubRecipeWeightError(DomainError):
    """Sub-recipe отсутствует вес для выравнивания."""
    pass
```

---

## Резюме

Доменный слой — это **автономная, свободная от фреймворка модель** бизнеса Menu Planner:
- **Сущности** захватывают основные концепции (Recipe, Product, Menu, User)
- **Объекты-значения** неизменяемы и безопасны (Quantity, Money, RecipeIngredient)
- **Сервисы** оркестрируют сложную логику (ShoppingListBuilder)
- **Порты** определяют контракты с внешним миром (репозитории, аутентификация)
- **Исключения** сообщают о нарушениях бизнес-правил

Все слои выше (приложение, API, фронтенд) зависят от этого ядра. Он может быть протестирован без мокирования или настройки фреймворка.

---

**Далее:** См. [backend-application.md](04-backend-application.md) для паттернов use case.
