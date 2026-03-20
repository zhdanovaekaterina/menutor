# Architecture — Clean Architecture + API Adapter

## Overview

Menu Planner uses **Clean Architecture** with a 4-layer design plus API and frontend adapters. The core principle is **dependency inversion**: business logic is completely decoupled from frameworks, databases, and UI technologies.

```
┌───────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 SPA)                │
└───────────────────────────────────────────────────────┘
                          ↓ (HTTP)
┌───────────────────────────────────────────────────────┐
│              API Adapter Layer (FastAPI)               │
│  Routers, Pydantic Schemas, Converters, Auth Middleware │
└───────────────────────────────────────────────────────┘
                          ↓ (Use Case)
┌───────────────────────────────────────────────────────┐
│            Application Layer (Use Cases)              │
│      Orchestration, DTOs, Transaction Boundaries      │
└───────────────────────────────────────────────────────┘
                          ↓ (Domain Objects)
┌───────────────────────────────────────────────────────┐
│      Domain Layer (Entities, Value Objects, Ports)    │
│          Business Rules, No Framework Code            │
└───────────────────────────────────────────────────────┘
                          ↓ (Ports)
┌───────────────────────────────────────────────────────┐
│         Infrastructure Layer (Repositories, Auth)      │
│     Database, File I/O, External Services             │
└───────────────────────────────────────────────────────┘
```

## Dependency Rule

Dependencies always point **inward** toward Domain:

```
Frontend → API → Application → Domain ← Infrastructure
                                ↑
                                │ (implements)
                                │
                          Infrastructure
```

- **Domain** depends on nothing
- **Application** depends only on Domain
- **Infrastructure** depends on Domain ports (interfaces)
- **API** depends on Application and Domain
- **Frontend** depends on API via HTTP calls

This allows:
- Domain logic can be tested without mocks
- Frameworks can be swapped without business logic changes
- Easy to understand data flow

## Layer Responsibilities

| Layer | Knows About | Ignorant Of | Responsibility |
|-------|------------|------------|-----------------|
| **Domain** | Entities, Value Objects, Ports | FastAPI, SQLAlchemy, Vue | Business rules, validations, calculations |
| **Application** | Domain, Use Case patterns | Databases, HTTP, UI | Orchestrate domain logic, manage transactions |
| **Infrastructure** | Domain ports, SQLAlchemy, bcrypt | Use cases, routers | Implement repositories, persistence, auth |
| **API** | Routes, Pydantic, Domain entities | Business logic | Accept HTTP requests, convert to/from domain |
| **Frontend** | Vue 3, Pinia, axios | Database, domain logic | User interface, state management, events |

---

## 1. Domain Layer (`backend/domain/`)

**No external dependencies. Pure Python business logic.**

### Entities

Entities have identity (ID) and mutable state. They contain business rules about valid states.

#### Recipe

File: `backend/domain/entities/recipe.py`

```python
@dataclass
class Recipe:
    id: RecipeId
    name: str
    servings: int
    ingredients: list[RecipeIngredient]     # Value objects
    steps: list[CookingStep]                 # Value objects
    category_id: RecipeCategoryId
    weight: int                              # grams, optional
    user_id: UserId                          # Multi-tenancy scoping
    total_pieces: int | None = None          # For pieces-based recipes
    pieces_per_portion: int | None = None
```

**Key method:** `scale_to(target_servings: float) → Recipe`

Scales ingredient quantities while preserving immutability (returns new Recipe).

**Invariants:**
- `total_pieces` and `pieces_per_portion` must both be set or both None
- If set: `pieces_per_portion ≤ total_pieces` and both ≥ 1

#### Product

File: `backend/domain/entities/product.py`

```python
@dataclass
class Product:
    id: ProductId
    name: str
    category_id: ProductCategoryId
    recipe_unit: str                        # "g", "kg", "ml", "l", "pcs", etc.
    purchase_unit: str                      # Unit in which product is typically bought
    price_per_purchase_unit: Money          # Value object
    conversion_factor: float                 # e.g., 1000 to convert g → kg
    user_id: UserId
```

#### Menu & MenuSlot

Menu = a named collection of slots. Slot = recipe/product + quantity + meal type + day.

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
    recipe_id: RecipeId | None              # Either recipe XOR product
    product_id: ProductId | None
    quantity: Quantity | None                # For products
    servings: int | None                     # For recipes
    meal_type: str                          # "завтрак", "обед", "ужин"
    day_of_week: int                        # 0=Mon, 6=Sun
    position: int                           # Ordering within same (day, meal_type)
```

#### ShoppingList & ShoppingListItem

Result of aggregating recipes by user's menu + family members.

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
    purchased: bool = False                 # Track check-off state
```

#### User & RefreshToken

Auth entities:

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
    token_hash: str                         # Hash of JWT (not stored plaintext)
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
    portion_multiplier: float               # e.g., 0.5 for child, 1.0 for adult
    dietary_restrictions: str | None        # e.g., "vegetarian, nut allergy"
    user_id: UserId
```

### Value Objects

Value objects are immutable, have no identity, and are identified by their attributes. Central to domain logic.

#### Quantity

File: `backend/domain/value_objects/quantity.py`

**Most complex value object.** Handles unit conversion and arithmetic.

```python
@dataclass(frozen=True)
class Quantity:
    amount: float
    unit: str                               # "g", "kg", "ml", "l", "pcs", etc.

    def __add__(self, other: "Quantity") -> "Quantity":
        """Add quantities with auto-conversion (e.g., 200g + 1kg = 1200g)."""
        if same_group(self.unit, other.unit):
            # Convert to common unit, add, return
            ...
        raise IncompatibleUnitsError(...)

    def to_unit(self, target_unit: str) -> "Quantity":
        """Convert to different unit within same group."""
        ...
```

**Unit groups:**
- **Weight:** g ↔ kg (1000)
- **Volume:** ml ↔ l (1000)
- **Count:** pcs (no conversion)
- **Dry:** tsp ↔ tbsp (3)

#### Money

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal                         # Precise currency arithmetic
    currency: str = "RUB"
```

#### RecipeIngredient

Links a product to a recipe with a quantity.

```python
@dataclass(frozen=True)
class RecipeIngredient:
    product_id: ProductId
    sub_recipe_id: RecipeId | None          # For nested recipes
    quantity: Quantity
    order: int                              # Ordering within ingredient list
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
    type: str                               # "product" or "recipe"
    active: bool = True
```

### Typed IDs

File: `backend/domain/value_objects/types.py`

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

**Why?** Prevents passing wrong ID types. Caught by mypy at static analysis time:

```python
def get_recipe(recipe_id: RecipeId, user_id: UserId) -> Recipe:
    ...

get_recipe(ProductId(5), UserId(1))   # ✓ mypy error: incompatible types
get_recipe(RecipeId(5), UserId(1))    # ✓ OK
```

### Domain Services

Stateless logic that doesn't fit a single entity.

#### ShoppingListBuilder

File: `backend/domain/services/shopping_list_builder.py`

Most complex domain service. Orchestrates:

1. Get all recipes from menu slots (filtered by day + meal type)
2. For each recipe, scale ingredients by family members' portion multipliers
3. Aggregate quantities (sum all flour needed, accounting for unit conversion)
4. Convert to purchase units (e.g., g → kg)
5. Look up prices from products
6. Calculate total cost

```python
class ShoppingListBuilder:
    def build(
        self,
        menu: Menu,
        family_members: list[FamilyMember],
        products: dict[ProductId, Product],
        recipes: dict[RecipeId, Recipe],
    ) -> ShoppingList:
        """Build shopping list from menu + family profiles."""
```

#### PortionCalculator

Calculates total servings needed based on family members.

```python
def calculate_total_servings(family_members: list[FamilyMember]) -> float:
    """1.0 + 1.0 + 0.5 = 2.5 for a 3-person family (2 adults, 1 child)."""
    return sum(fm.portion_multiplier for fm in family_members)
```

#### UnitConverter

Converts between compatible units (g ↔ kg, ml ↔ l, tsp ↔ tbsp).

```python
def convert(quantity: Quantity, target_unit: str) -> Quantity:
    """200g to kg → 0.2 kg"""
```

### Ports (Interfaces)

Abstract interfaces implemented by Infrastructure layer. Defined in `backend/domain/ports/`.

```python
# RecipeRepository port (ABC)
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

Other ports:
- `ProductRepository`
- `MenuRepository`
- `FamilyMemberRepository`
- `UserRepository`
- `RefreshTokenRepository`
- `RecipeCategoryRepository`
- `ProductCategoryRepository`

### Exceptions

File: `backend/domain/exceptions.py`

Domain-specific exceptions (base: `DomainError`):

- `InvalidEntityError` — Entity invariant violated
- `EntityNotFoundError` — Requested entity not found
- `AuthenticationError` — Invalid credentials
- `CircularDependencyError` — Sub-recipe forms a cycle
- `NestingDepthExceededError` — Sub-recipe nesting too deep
- `SubRecipeWeightError` — Sub-recipe missing weight for flattening

---

## 2. Application Layer (`backend/application/use_cases/`)

**Orchestrates domain logic. One class = one user operation.**

### Pattern: Use Case (Interactor)

Each use case is a class with an `execute()` method. Handles:
- Input validation (via DTOs)
- Transaction boundaries
- Error handling
- Repository calls (dependency injection)

### Example: CreateRecipe

```python
class CreateRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self, user_id: UserId, name: str, servings: int,
        category_id: RecipeCategoryId, ingredients: list[...], steps: list[...]
    ) -> RecipeId:
        # Validate input
        if not name.strip():
            raise DomainError("Recipe name is required")

        # Create domain entity
        recipe = Recipe(
            id=RecipeId(0),  # Placeholder; DB assigns real ID
            name=name,
            servings=servings,
            category_id=category_id,
            ingredients=ingredients,
            steps=steps,
            user_id=user_id,
        )

        # Persist
        return self.recipe_repo.save(recipe)
```

### Use Case Inventory

| File | Use Cases |
|------|-----------|
| `auth.py` | `RegisterUser`, `LoginUser`, `RefreshAccessToken`, `GetCurrentUser` |
| `manage_recipe.py` | `GetRecipe`, `ListRecipes`, `CreateRecipe`, `UpdateRecipe`, `DeleteRecipe` |
| `manage_product.py` | `GetProduct`, `ListProducts`, `CreateProduct`, `UpdateProduct`, `DeleteProduct` |
| `manage_family.py` | `CreateFamilyMember`, `UpdateFamilyMember`, `DeleteFamilyMember`, `ListFamilyMembers` |
| `plan_menu.py` | `CreateMenu`, `LoadMenu`, `AddMenuSlot`, `UpdateMenuSlot`, `DeleteMenuSlot`, `ClearMenu` |
| `generate_shopping_list.py` | `GenerateShoppingList` (calls ShoppingListBuilder) |
| `flatten_recipe_products.py` | `FlattenRecipeProducts` (expands sub-recipes) |
| `preview_flattened_products.py` | `PreviewFlattenedProducts` (dry-run flattening) |
| `validate_sub_recipe.py` | `ValidateSubRecipe` (detects cycles, nesting depth) |
| `export_shopping_list.py` | `ExportShoppingList` (CSV/JSON/text) |
| `export_entities.py` | `ExportEntities` (recipes, products as JSON) |
| `import_entities.py` | `ImportEntities` (recipes, products from JSON) |

---

## 3. Infrastructure Layer (`backend/infrastructure/`)

**Implements domain ports. Database, auth, file I/O.**

### Repository Implementations

File: `backend/infrastructure/repositories/sqlalchemy_*.py`

Uses SQLAlchemy ORM to map domain entities to database rows.

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

### Auth Services

#### BcryptPasswordHasher

File: `backend/infrastructure/auth/bcrypt_password_hasher.py`

Implements `PasswordHasher` port:

```python
class BcryptPasswordHasher(PasswordHasher):
    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), hash.encode())
```

#### JwtTokenService

File: `backend/infrastructure/auth/jwt_token_service.py`

Implements `TokenService` port:

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
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
```

### Database Setup

#### SQLAlchemy Models

File: `backend/infrastructure/database/models.py`

ORM models mapping to database tables:

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

#### Alembic Migrations

File: `backend/infrastructure/database/migrations/versions/`

Each migration is a timestamped Python file:

```python
# Example: add_ingredient_order.py
def upgrade() -> None:
    op.add_column('recipe_ingredients',
                  sa.Column('order', sa.Integer(), nullable=False, server_default='0'))

def downgrade() -> None:
    op.drop_column('recipe_ingredients', 'order')
```

Run: `alembic upgrade head`

#### Engine & Session

File: `backend/infrastructure/database/__init__.py`

```python
def get_engine(db_url: str | None = None) -> Engine:
    url = db_url or os.environ.get("DATABASE_URL", "sqlite:///test.db")
    return create_engine(url, echo=False)

def get_session(engine: Engine) -> Session:
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
```

### Exporters

Strategy pattern for format-agnostic export.

```python
class ShoppingListExporter(ABC):
    @abstractmethod
    def export(self, shopping_list: ShoppingList) -> str:
        pass

class CsvExporter(ShoppingListExporter):
    def export(self, shopping_list: ShoppingList) -> str:
        # Generate CSV with headers, category grouping, costs
        ...

class JsonExporter(ShoppingListExporter):
    def export(self, shopping_list: ShoppingList) -> str:
        # Generate JSON structure
        ...
```

---

## 4. API Layer (`backend/api/`)

**HTTP adapter. Routers, schemas, converters, auth middleware.**

### FastAPI App Setup

File: `backend/api/main.py`

```python
app = FastAPI(
    title="Menutor API",
    lifespan=lifespan,  # Creates ApplicationContainer at startup
)

# Middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Exception handlers (map domain errors to HTTP responses)
@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(products.router, prefix="/api")
# ... etc
```

### Authentication Middleware

File: `backend/api/auth.py`

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

All protected endpoints:

```python
@router.get("/recipes")
def list_recipes(
    user: User = Depends(get_current_user),  # Extracts + validates JWT
    container: ApplicationContainer = Depends(get_container),
) -> list[RecipeResponse]:
    recipes = container.list_recipes.execute(user.id)
    return [recipe_to_response(r) for r in recipes]
```

### Pydantic Schemas

File: `backend/api/schemas/recipe.py`

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

### Converters

File: `backend/api/converters.py`

Converts between Pydantic schemas and domain entities:

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

### Router Endpoints

File: `backend/api/routers/recipes.py`

Each router handles CRUD for one domain entity:

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

**Routers (7 total):**
- `auth.py` — login, register, refresh, me, logout
- `recipes.py` — CRUD recipes, list by category
- `products.py` — CRUD products
- `menus.py` — CRUD menus, manage slots
- `family.py` — CRUD family members
- `categories.py` — CRUD categories (product + recipe)
- `shopping_list.py` — generate, export (CSV/JSON/text)
- `import_export.py` — import/export recipes and products
- `system.py` — health check, version

---

## 5. Frontend Layer (`frontend/src/`)

**Vue 3 SPA with Pinia state management and Tailwind CSS.**

### Project Structure

```
frontend/src/
├── main.ts                       # Vue app init + plugin setup
├── App.vue                       # Root layout (AppSidebar + router-view)
├── router/index.ts              # Vue Router config (6 routes + nested /settings)
├── stores/                       # Pinia stores (7 core + 1 toast)
│   ├── auth.ts                  # User, access/refresh tokens
│   ├── recipes.ts               # Recipe list, CRUD operations
│   ├── products.ts              # Product list, CRUD operations
│   ├── menus.ts                 # Menu state, slot management
│   ├── family.ts                # Family members
│   ├── categories.ts            # Product/recipe categories
│   ├── shoppingList.ts          # Shopping list, item state
│   ├── toast.ts                 # Toast notifications queue
│   └── crud-factory.ts          # Generic CRUD store generator
├── api/
│   ├── client.ts                # axios instance with JWT interceptor
│   ├── auth.ts                  # API calls: register, login, refresh
│   └── types.ts                 # TypeScript interfaces (match Pydantic)
├── views/
│   ├── AuthView.vue             # Login/register page
│   ├── MenuPlannerView.vue      # 7-day meal planner
│   ├── ShoppingListView.vue     # Aggregated shopping list
│   ├── RecipeListView.vue       # Recipe table + form
│   ├── ProductListView.vue      # Product table + form
│   └── SettingsView.vue         # Settings container (family, categories, about)
├── components/
│   ├── layout/                  # AppSidebar, MobileBottomNav
│   ├── planner/                 # PlannerGrid, GridCell, SourcePanel
│   ├── shopping/                # ShoppingTable, ShoppingSummary
│   ├── recipes/                 # RecipeTable, RecipeForm
│   ├── products/                # ProductTable, ProductForm
│   ├── settings/                # FamilyPanel, CategoryPanel, AboutPanel
│   └── ui/                      # ConfirmDialog, ToastNotification, etc.
├── composables/                 # useSelection, useDropdown, etc.
├── utils/                       # Unit conversion, formatting
└── assets/                      # Tailwind CSS, global styles
```

### Pinia Stores

**Pattern:** Each store manages one domain concept. Actions call API client. State is reactive.

```typescript
// stores/recipes.ts
import { defineStore } from 'pinia'

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

### API Client with JWT

File: `frontend/src/api/client.ts`

```typescript
import axios, { AxiosInstance } from 'axios'
import { useAuthStore } from '@/stores/auth'

const client: AxiosInstance = axios.create({
  baseURL: '/api',
})

// Request interceptor: add JWT token
client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// Response interceptor: auto-refresh on 401
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    if (error.response?.status === 401 && auth.refreshToken) {
      try {
        const { access_token } = await refresh()
        auth.setAccessToken(access_token)
        // Retry original request
        return client(error.config)
      } catch {
        auth.logout()
      }
    }
    return Promise.reject(error)
  }
)
```

### Vue Router

File: `frontend/src/router/index.ts`

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

### Component Example: RecipeForm

```vue
<template>
  <form @submit.prevent="submit">
    <input v-model="form.name" placeholder="Recipe name" required />
    <select v-model="form.category_id" required>
      <option v-for="cat in categories" :value="cat.id">{{ cat.name }}</option>
    </select>
    <input v-model.number="form.servings" type="number" min="1" />

    <fieldset>
      <legend>Ingredients</legend>
      <div v-for="(ing, i) in form.ingredients" :key="i">
        <select v-model="ing.product_id">
          <option v-for="p in products" :value="p.id">{{ p.name }}</option>
        </select>
        <input v-model.number="ing.quantity_amount" type="number" step="0.01" />
        <span>{{ unitFor(ing.product_id) }}</span>
      </div>
      <button @click="addIngredient" type="button">+ Add</button>
    </fieldset>

    <button type="submit">Save</button>
    <button @click="reset" type="button">Clear</button>
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
  // ...
}
</script>
```

---

## 6. Composition Root (`backend/composition/`)

**Dependency injection orchestration. Creates the object graph.**

File: `backend/composition/container.py`

```python
class ApplicationContainer:
    """Created once at startup. Holds all use cases and repositories."""

    def __init__(self, db_url: str | None = None) -> None:
        # 1. Create infrastructure (DB, auth services)
        infra = _create_infrastructure(db_url)

        # 2. Wire each domain module (auth, recipes, products, etc.)
        for name, obj in _wire_auth(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_recipes(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_products(infra).items():
            setattr(self, name, obj)
        # ... etc

        # 3. Store DB connection
        self._engine = infra.engine
        self._session = infra.session
```

Example wiring (one module):

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

## Design Patterns Used

| Pattern | Applied To | Purpose |
|---------|-----------|---------|
| **Clean Architecture** | Entire codebase | Layers, dependency inversion, testability |
| **Repository** | All entities | Abstract persistence; swappable backends |
| **Use Case (Interactor)** | Application layer | One class = one operation, isolated, testable |
| **Value Object** | Quantity, Money, Category | Immutable, no identity, safe arithmetic |
| **Domain Service** | ShoppingListBuilder, UnitConverter | Logic that doesn't fit a single entity |
| **Dependency Injection** | Composition Root | Explicit wiring, no Service Locator anti-pattern |
| **Strategy** | Exporters (CSV, JSON, Text) | Interchangeable algorithms |
| **Adapter** | API layer | Translate HTTP ↔ domain entities |
| **Facade** | Pinia stores | Simplified API client interface |
| **Observer** | Vue reactivity | State changes trigger component re-renders |
| **Interceptor** | axios + FastAPI middleware | Cross-cutting concerns (JWT, CORS) |

---

## Testing Strategy

```
                  Testing Pyramid

                       /\
                      /  \        E2E / Smoke tests (minimal)
                     /────\       App launches, core workflows
                    /      \
                   /Integration\  Repository tests vs real DB
                  /──────────────\  Export/import tests
                 /                \
                /    Unit Tests    \  Domain: zero mocks
               /                    \ App: mock repos only
              /──────────────────────\
```

| Test Type | Location | Mocking | Coverage |
|-----------|----------|---------|----------|
| **Domain unit** | `tests/unit/domain/` | None (pure functions) | 95%+ |
| **App unit** | `tests/unit/application/` | Mock repositories | 80%+ |
| **API unit** | `tests/unit/api/` | Mock container, TestClient | 70%+ |
| **Integration** | `tests/integration/repositories/` | Real SQLite `:memory:` | 60%+ |

**Total coverage:** 490+ tests passing

---

**Next:** See [backend-domain.md](03-backend-domain.md) for detailed entity specifications.
