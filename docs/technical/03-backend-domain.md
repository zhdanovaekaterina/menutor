# Domain Layer — Entities, Value Objects, Services, Ports

File location: `backend/domain/`

The Domain layer contains all business logic and is completely independent of frameworks. It has **zero dependencies** on FastAPI, SQLAlchemy, Vue, or any external library.

---

## Entities

Entities have **identity** (ID) and mutable state. They enforce business invariants.

### Recipe

**File:** `backend/domain/entities/recipe.py`

```python
@dataclass
class Recipe:
    id: RecipeId
    name: str
    servings: int                          # Base servings (default portion size)
    ingredients: list[RecipeIngredient]    # Value objects
    steps: list[CookingStep]               # Value objects
    category_id: RecipeCategoryId
    weight: int = 0                        # Finished dish weight in grams (optional)
    user_id: UserId = UserId(0)            # Multi-tenancy scoping
    total_pieces: int | None = None        # For pieces-based recipes (e.g., 12 cookies)
    pieces_per_portion: int | None = None  # e.g., 3 cookies per portion
```

**Invariants (enforced in `__post_init__`):**
- If `total_pieces` is set, `pieces_per_portion` must also be set (and vice versa)
- Both must be ≥ 1
- `pieces_per_portion ≤ total_pieces`

**Key properties:**

```python
@property
def is_pieces_mode(self) -> bool:
    """Returns True if recipe uses pieces-based scaling."""
    return self.total_pieces is not None and self.pieces_per_portion is not None

@property
def computed_servings(self) -> int:
    """Calculates effective servings from pieces if in pieces mode, else uses servings."""
    if self.is_pieces_mode:
        return self.total_pieces // self.pieces_per_portion
    return self.servings
```

**Key method:**

```python
def scale_to(self, target_servings: float) -> Recipe:
    """
    Returns a new Recipe scaled to target servings.
    Immutable: original recipe unchanged.

    Example:
        recipe.scale_to(6)  # Scale from 4 servings to 6
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
    # Recalculate total_pieces if in pieces mode
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

**Use case example:**

```python
# Menu planner scales recipe based on family
menu_recipe = recipe.scale_to(4)  # 2 adults (×1.0 each) + 1 child (×0.5) = 2.5 → round to 4
ingredients_needed = menu_recipe.ingredients  # Quantities already scaled
```

### Product

**File:** `backend/domain/entities/product.py`

```python
@dataclass
class Product:
    id: ProductId
    name: str
    category_id: ProductCategoryId
    recipe_unit: str                       # Unit used in recipes (e.g., "g", "ml", "pcs")
    purchase_unit: str                     # Unit for buying (e.g., "kg", "l", "box")
    price_per_purchase_unit: Money         # Value object: price in RUB
    conversion_factor: float               # e.g., 1000 (to convert g → kg)
    user_id: UserId = UserId(0)
    brand: str = ""                        # Optional: product brand
    supplier: str = ""                     # Optional: typical supplier/retailer
```

**Example:**
```python
flour = Product(
    id=ProductId(1),
    name="Мука пшеничная",
    recipe_unit="g",
    purchase_unit="kg",
    price_per_purchase_unit=Money(Decimal("80.00")),
    conversion_factor=1000,
)
# In recipe: 200g → cost = (200 / 1000) * 80.00 = 16.00 RUB
```

### Menu & MenuSlot

**File:** `backend/domain/entities/menu.py`

A Menu is a named collection of meal slots for a week.

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
    recipe_id: RecipeId | None = None              # Either recipe OR product (XOR)
    product_id: ProductId | None = None
    quantity: Quantity | None = None               # For products
    servings: int | None = None                    # For recipes
    meal_type: str = "обед"                        # "завтрак", "обед", "ужин"
    day_of_week: int = 0                           # 0=Mon, ..., 6=Sun
    position: int = 0                              # Ordering within (day, meal_type)
```

**Invariant:** `(recipe_id is None) XOR (product_id is None)` — either recipe or product, never both.

**Use case:**
```python
# Planning week for 2.5 effective servings (2 adults × 1.0 + 1 child × 0.5)
menu_slot = MenuSlot(
    recipe_id=RecipeId(5),  # "Блины" (pancakes)
    servings=4,             # Scale to 4 servings
    meal_type="завтрак",
    day_of_week=0,          # Monday
)

recipe = get_recipe(menu_slot.recipe_id)  # "Блины" with 4 servings base
scaled = recipe.scale_to(menu_slot.servings * 2.5 / recipe.computed_servings)  # Scale to family
ingredients = scaled.ingredients  # Use for shopping list
```

### ShoppingList & ShoppingListItem

**File:** `backend/domain/entities/shopping_list.py`

Result of aggregating recipes by menu + family members. Contains final, deduplicated product list with costs.

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
    purchased: bool = False                        # Track check-off state
```

**Example:**
```python
item = ShoppingListItem(
    product_id=ProductId(1),
    name="Мука",
    quantity=Quantity(1.2, "kg"),        # 200g from pancakes + 400g from bread + 600g from cake
    price_per_unit=Money(Decimal("80")),
    total_cost=Money(Decimal("96.00")),  # 1.2 * 80
    category_id=ProductCategoryId(2),    # "Сыпучие" (dry goods)
)
```

### User & RefreshToken

**File:** `backend/domain/entities/user.py` and `refresh_token.py`

```python
@dataclass
class User:
    id: UserId
    email: str
    nickname: str
    password_hash: str                     # bcrypt hash (never plaintext)
    created_at: datetime

@dataclass
class RefreshToken:
    id: RefreshTokenId
    user_id: UserId
    token_hash: str                        # Hash of JWT token (not stored plaintext)
    expires_at: datetime
    created_at: datetime
    revoked: bool = False                  # Soft revocation (logout)
```

### FamilyMember

**File:** `backend/domain/entities/family_member.py`

```python
@dataclass
class FamilyMember:
    id: FamilyMemberId
    name: str
    portion_multiplier: float = 1.0        # 1.0 = adult, 0.5 = child
    dietary_restrictions: str = ""         # e.g., "vegetarian, nut allergy" (free text)
    user_id: UserId = UserId(0)
    comment: str = ""                      # Optional notes

    def effective_servings(self, base_servings: int) -> float:
        """Calculates this member's portion of a recipe."""
        return base_servings * self.portion_multiplier
```

---

## Value Objects

Value objects are **immutable**, identified by their attributes (not by ID), and cannot exist independently of an entity.

### Quantity

**File:** `backend/domain/value_objects/quantity.py`

Most important value object. Handles unit conversion and arithmetic.

```python
@dataclass(frozen=True)
class Quantity:
    amount: float
    unit: str  # "g", "kg", "ml", "l", "pcs", "tsp", "tbsp", etc.

    def to_unit(self, target_unit: str) -> "Quantity":
        """Convert to different unit within same group."""
        if self.unit == target_unit:
            return self
        factor = unit_conversion_factor(self.unit, target_unit)
        return Quantity(self.amount * factor, target_unit)

    def __add__(self, other: "Quantity") -> "Quantity":
        """Add quantities with auto-conversion."""
        if self.unit == other.unit:
            return Quantity(self.amount + other.amount, self.unit)

        # Try to find common unit
        if are_compatible(self.unit, other.unit):
            other_converted = other.to_unit(self.unit)
            return Quantity(self.amount + other_converted.amount, self.unit)

        raise IncompatibleUnitsError(f"Cannot add {self.unit} + {other.unit}")
```

**Unit groups:**
```
Weight:   g ↔ kg  (factor: 1000)
Volume:   ml ↔ l  (factor: 1000)
Cooking:  tsp ↔ tbsp  (factor: 3)
Count:    pcs (no conversion)
```

**Example:**
```python
flour_1 = Quantity(200, "g")
flour_2 = Quantity(0.5, "kg")
total = flour_1 + flour_2  # Quantity(700, "g") or Quantity(0.7, "kg")

milk = Quantity(250, "ml")
milk_l = milk.to_unit("l")  # Quantity(0.25, "l")

apples = Quantity(5, "pcs")  # Pieces don't convert
```

### Money

**File:** `backend/domain/value_objects/money.py`

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal  # Use Decimal for exact currency math
    currency: str = "RUB"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: float) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)
```

**Example:**
```python
price_per_kg = Money(Decimal("80.00"), "RUB")
quantity_kg = 1.2
total = price_per_kg.multiply(quantity_kg)  # Money(Decimal("96.00"), "RUB")

cost_1 = Money(Decimal("100"), "RUB")
cost_2 = Money(Decimal("50"), "RUB")
total_cost = cost_1 + cost_2  # Money(Decimal("150"), "RUB")
```

### RecipeIngredient

**File:** `backend/domain/value_objects/recipe_ingredient.py`

Links a product to a recipe.

```python
@dataclass(frozen=True)
class RecipeIngredient:
    product_id: ProductId
    sub_recipe_id: RecipeId | None = None  # For nested recipes
    quantity: Quantity = field(default_factory=lambda: Quantity(0, "g"))
    order: int = 0                         # Position in ingredient list

    def is_sub_recipe(self) -> bool:
        return self.sub_recipe_id is not None

    def is_product(self) -> bool:
        return self.sub_recipe_id is None
```

**Example:**
```python
# Recipe "Борщ" includes beets (product) and "Вегетальный бульон" (sub-recipe)
ing_1 = RecipeIngredient(product_id=ProductId(5), quantity=Quantity(500, "g"), order=1)
ing_2 = RecipeIngredient(sub_recipe_id=RecipeId(3), quantity=Quantity(1, "l"), order=2)
```

### CookingStep

**File:** `backend/domain/value_objects/cooking_step.py`

```python
@dataclass(frozen=True)
class CookingStep:
    description: str
    order: int

    def __lt__(self, other: "CookingStep") -> bool:
        return self.order < other.order
```

### Category

**File:** `backend/domain/value_objects/category.py`

```python
@dataclass(frozen=True)
class Category:
    id: int
    name: str
    type: str  # "product" or "recipe"
    active: bool = True
```

### Typed IDs

**File:** `backend/domain/value_objects/types.py`

Using `NewType` prevents mixing up different ID types at static analysis time:

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

**Why?** mypy enforces correct ID types at compile time:

```python
def get_recipe(recipe_id: RecipeId, user_id: UserId) -> Recipe:
    ...

# ✗ mypy error: incompatible types in argument 1
get_recipe(ProductId(5), UserId(1))

# ✓ OK
get_recipe(RecipeId(5), UserId(1))
```

At runtime, `RecipeId` is just an `int`, so no performance cost.

---

## Domain Services

Stateless services encapsulating logic that doesn't belong to a single entity.

### ShoppingListBuilder

**File:** `backend/domain/services/shopping_list_builder.py`

Most complex domain service. Converts a menu + family members into a deduplicated, cost-tracked shopping list.

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
        Build shopping list from menu by:
        1. Get all recipes from menu slots
        2. Scale by family member portion multipliers
        3. Aggregate quantities (sum + convert units)
        4. Convert to purchase units
        5. Calculate costs
        """
        # Calculate total effective servings
        total_servings = sum(fm.portion_multiplier for fm in family_members)

        # Aggregate product quantities
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

        # Create shopping list items
        items = []
        total_cost = Money(Decimal("0.00"))
        for product_id, quantity in product_quantities.items():
            product = products[product_id]

            # Convert to purchase unit
            converted = quantity.to_unit(product.purchase_unit)

            # Calculate cost
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

**Example:**
```python
menu = Menu(id=MenuId(1), ...)  # 7-day meal plan
family = [
    FamilyMember(name="Мама", portion_multiplier=1.0),
    FamilyMember(name="Папа", portion_multiplier=1.0),
    FamilyMember(name="Сын", portion_multiplier=0.5),
]  # Total: 2.5 servings

shopping_list = builder.build(menu, family, products, recipes)
# Result: aggregated products with costs for 2.5 servings
```

### PortionCalculator

**File:** `backend/domain/services/portion_calculator.py`

```python
class PortionCalculator:
    @staticmethod
    def calculate_total_servings(family_members: list[FamilyMember]) -> float:
        """Sum all portion multipliers."""
        return sum(fm.portion_multiplier for fm in family_members)

    @staticmethod
    def calculate_portions_per_member(
        base_servings: int,
        family_members: list[FamilyMember],
    ) -> dict[FamilyMemberId, float]:
        """Map each member to their portion size."""
        return {
            fm.id: base_servings * fm.portion_multiplier
            for fm in family_members
        }
```

### UnitConverter

**File:** `backend/domain/services/unit_converter.py`

```python
class UnitConverter:
    # Unit groups and conversion factors
    WEIGHT_UNITS = {"g": 1, "kg": 1000}
    VOLUME_UNITS = {"ml": 1, "l": 1000}
    COOKING_UNITS = {"tsp": 1, "tbsp": 3}

    @staticmethod
    def convert(quantity: Quantity, target_unit: str) -> Quantity:
        """Convert to different unit within same group."""
        if quantity.unit == target_unit:
            return quantity
        return quantity.to_unit(target_unit)

    @staticmethod
    def get_unit_group(unit: str) -> str | None:
        """Return group name or None if not convertible."""
        if unit in UnitConverter.WEIGHT_UNITS:
            return "weight"
        elif unit in UnitConverter.VOLUME_UNITS:
            return "volume"
        elif unit in UnitConverter.COOKING_UNITS:
            return "cooking"
        return None
```

---

## Ports (Abstract Interfaces)

Ports define the contract between Domain and Infrastructure. Infrastructure implements these ports.

**Location:** `backend/domain/ports/`

### RecipeRepository

```python
class RecipeRepository(ABC):
    @abstractmethod
    def get_by_id(self, recipe_id: RecipeId, user_id: UserId) -> Recipe | None:
        """Get recipe by ID, scoped to user."""
        pass

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> list[Recipe]:
        """List all user's recipes."""
        pass

    @abstractmethod
    def list_by_category(
        self, user_id: UserId, category_id: RecipeCategoryId
    ) -> list[Recipe]:
        """List recipes in category."""
        pass

    @abstractmethod
    def save(self, recipe: Recipe) -> RecipeId:
        """Create or update recipe. Returns ID."""
        pass

    @abstractmethod
    def delete(self, recipe_id: RecipeId, user_id: UserId) -> None:
        """Soft or hard delete."""
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

### Other Ports

- `FamilyMemberRepository` — CRUD family members
- `UserRepository` — CRUD users, find by email
- `RefreshTokenRepository` — CRUD refresh tokens
- `RecipeCategoryRepository` — CRUD recipe categories
- `ProductCategoryRepository` — CRUD product categories
- `PasswordHasher` — hash and verify passwords
- `TokenService` — create and validate JWTs

---

## Exceptions

**File:** `backend/domain/exceptions.py`

All domain exceptions inherit from `DomainError`.

```python
class DomainError(Exception):
    """Base for all domain errors."""
    pass

class InvalidEntityError(DomainError):
    """Entity invariant violated (e.g., servings < 1)."""
    pass

class EntityNotFoundError(DomainError):
    """Requested entity not found."""
    pass

class AuthenticationError(DomainError):
    """Invalid credentials or token."""
    pass

class CircularDependencyError(DomainError):
    """Recipe A includes recipe B which includes recipe A."""
    pass

class NestingDepthExceededError(DomainError):
    """Sub-recipe nesting too deep (e.g., > 5 levels)."""
    pass

class IncompatibleUnitsError(DomainError):
    """Cannot convert between units (e.g., g + l)."""
    pass

class SubRecipeWeightError(DomainError):
    """Sub-recipe missing weight for flattening."""
    pass
```

---

## Summary

The Domain layer is a **self-contained, framework-free model** of Menu Planner's business:
- **Entities** capture core concepts (Recipe, Product, Menu, User)
- **Value objects** are immutable and safe (Quantity, Money, RecipeIngredient)
- **Services** orchestrate complex logic (ShoppingListBuilder)
- **Ports** define contracts with the outside world (repositories, auth)
- **Exceptions** communicate business rule violations

All layers above (Application, API, Frontend) depend on this core. It can be tested without any mocks or framework setup.

---

**Next:** See [backend-application.md](04-backend-application.md) for use case patterns.
