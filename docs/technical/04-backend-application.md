# Application Layer — Use Cases

**File location:** `backend/application/use_cases/`

The Application layer orchestrates Domain logic. **One class = one user operation.** Use cases are decoupled from HTTP, databases, and UI.

---

## Use Case Pattern

Each use case is a class with an `execute()` method. The pattern:

```python
class SomeUseCase:
    def __init__(self, repository: SomeRepository, other_service: OtherService):
        self.repository = repository
        self.other_service = other_service

    def execute(self, param1: str, param2: int, user_id: UserId) -> ResultType:
        # 1. Validate input
        if not param1.strip():
            raise DomainError("param1 is required")

        # 2. Fetch domain objects
        entity = self.repository.get_by_id(entity_id, user_id)
        if not entity:
            raise EntityNotFoundError("Entity not found")

        # 3. Apply business logic
        entity.some_property = param2
        modified = self.other_service.transform(entity)

        # 4. Persist
        result_id = self.repository.save(modified)

        # 5. Return value (typically ID or full entity)
        return result_id
```

**Benefits:**
- **Testable:** inject mock repositories
- **Reusable:** can be called from API, CLI, events
- **Isolated:** each operation is independent
- **Debuggable:** clear input → output flow

---

## Use Case Catalog

### Auth Module

**File:** `backend/application/use_cases/auth.py`

#### RegisterUser

Creates a new user account.

```python
class RegisterUser:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    def execute(self, email: str, password: str, nickname: str) -> UserId:
        """
        Register new user.

        Raises:
            UserAlreadyExistsError: Email already registered
            DomainError: Invalid email or password
        """
        # Check uniqueness
        existing = self.user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"Email {email} already registered")

        # Hash password
        password_hash = self.password_hasher.hash_password(password)

        # Create and save
        user = User(
            id=UserId(0),  # DB assigns
            email=email,
            nickname=nickname,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
        )
        return self.user_repo.save(user)
```

#### LoginUser

Validates credentials and returns tokens.

```python
class LoginUser:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.refresh_token_repo = refresh_token_repo

    def execute(self, email: str, password: str) -> LoginResponse:
        """
        Authenticate user and return JWT tokens.

        Returns:
            LoginResponse with access_token, refresh_token, token_type
        """
        user = self.user_repo.get_by_email(email)
        if not user or not self.password_hasher.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Create tokens
        access_token = self.token_service.create_access_token(
            user.id, expires_in_minutes=30
        )
        refresh_token = self.token_service.create_refresh_token(
            user.id, expires_in_days=30
        )

        # Store refresh token hash
        token_hash = hash_token(refresh_token)
        self.refresh_token_repo.save(RefreshToken(
            id=RefreshTokenId(0),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow(),
        ))

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
```

#### RefreshAccessToken

Issues a new access token using a refresh token.

```python
class RefreshAccessToken:
    def __init__(
        self,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository,
    ):
        self.token_service = token_service
        self.refresh_token_repo = refresh_token_repo

    def execute(self, refresh_token: str) -> str:
        """Validate refresh token and return new access token."""
        payload = self.token_service.validate_token(refresh_token)

        # Verify token not revoked
        token_hash = hash_token(refresh_token)
        stored = self.refresh_token_repo.get_by_hash(token_hash)
        if not stored or stored.revoked or stored.expires_at < datetime.utcnow():
            raise AuthenticationError("Refresh token invalid or expired")

        # Issue new access token
        new_access_token = self.token_service.create_access_token(
            stored.user_id, expires_in_minutes=30
        )
        return new_access_token
```

#### GetCurrentUser

Extracts and validates JWT token payload.

```python
class GetCurrentUser:
    def __init__(self, user_repo: UserRepository, token_service: TokenService):
        self.user_repo = user_repo
        self.token_service = token_service

    def execute(self, token: str) -> User:
        """Validate token and return current user."""
        payload = self.token_service.validate_token(token)
        user_id = UserId(payload.get("user_id"))

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        return user
```

### Recipe Management

**File:** `backend/application/use_cases/manage_recipe.py`

#### ListRecipes

```python
class ListRecipes:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self, user_id: UserId, category_id: RecipeCategoryId | None = None
    ) -> list[Recipe]:
        """List all user's recipes, optionally filtered by category."""
        if category_id:
            return self.recipe_repo.list_by_category(user_id, category_id)
        return self.recipe_repo.list_by_user(user_id)
```

#### GetRecipe

```python
class GetRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(self, recipe_id: RecipeId, user_id: UserId) -> Recipe:
        recipe = self.recipe_repo.get_by_id(recipe_id, user_id)
        if not recipe:
            raise EntityNotFoundError(f"Recipe {recipe_id} not found")
        return recipe
```

#### CreateRecipe

```python
class CreateRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self,
        user_id: UserId,
        name: str,
        servings: int,
        category_id: RecipeCategoryId,
        ingredients: list[RecipeIngredient],
        steps: list[CookingStep],
        weight: int = 0,
        total_pieces: int | None = None,
        pieces_per_portion: int | None = None,
    ) -> RecipeId:
        """Create a new recipe."""
        if not name.strip():
            raise DomainError("Recipe name is required")
        if servings < 1:
            raise DomainError("Servings must be >= 1")

        recipe = Recipe(
            id=RecipeId(0),
            name=name.strip(),
            servings=servings,
            category_id=category_id,
            ingredients=ingredients,
            steps=steps,
            weight=weight,
            user_id=user_id,
            total_pieces=total_pieces,
            pieces_per_portion=pieces_per_portion,
        )

        return self.recipe_repo.save(recipe)
```

#### UpdateRecipe

```python
class UpdateRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self,
        recipe_id: RecipeId,
        user_id: UserId,
        **kwargs,  # name, servings, category_id, ingredients, steps, etc.
    ) -> RecipeId:
        """Update recipe fields."""
        recipe = self.recipe_repo.get_by_id(recipe_id, user_id)
        if not recipe:
            raise EntityNotFoundError(f"Recipe {recipe_id} not found")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(recipe, key) and value is not None:
                setattr(recipe, key, value)

        return self.recipe_repo.save(recipe)
```

#### DeleteRecipe

```python
class DeleteRecipe:
    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(self, recipe_id: RecipeId, user_id: UserId) -> None:
        """Delete recipe."""
        recipe = self.recipe_repo.get_by_id(recipe_id, user_id)
        if not recipe:
            raise EntityNotFoundError(f"Recipe {recipe_id} not found")
        self.recipe_repo.delete(recipe_id, user_id)
```

### Menu Planning

**File:** `backend/application/use_cases/plan_menu.py`

#### CreateMenu

```python
class CreateMenu:
    def __init__(self, menu_repo: MenuRepository):
        self.menu_repo = menu_repo

    def execute(self, user_id: UserId, name: str) -> MenuId:
        """Create a new menu."""
        if not name.strip():
            raise DomainError("Menu name is required")

        menu = Menu(
            id=MenuId(0),
            name=name.strip(),
            created_at=datetime.utcnow(),
            user_id=user_id,
            slots=[],
        )
        return self.menu_repo.save(menu)
```

#### LoadMenu

```python
class LoadMenu:
    def __init__(self, menu_repo: MenuRepository):
        self.menu_repo = menu_repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> Menu:
        """Load menu with all slots."""
        menu = self.menu_repo.get_by_id(menu_id, user_id)
        if not menu:
            raise EntityNotFoundError(f"Menu {menu_id} not found")
        return menu
```

#### AddMenuSlot

```python
class AddMenuSlot:
    def __init__(self, menu_repo: MenuRepository, recipe_repo: RecipeRepository):
        self.menu_repo = menu_repo
        self.recipe_repo = recipe_repo

    def execute(
        self,
        menu_id: MenuId,
        user_id: UserId,
        recipe_id: RecipeId | None,
        product_id: ProductId | None,
        servings: int | None,
        quantity: Quantity | None,
        meal_type: str,
        day_of_week: int,
    ) -> MenuSlotId:
        """Add recipe or product to menu slot."""
        menu = self.menu_repo.get_by_id(menu_id, user_id)
        if not menu:
            raise EntityNotFoundError(f"Menu {menu_id} not found")

        if recipe_id:
            recipe = self.recipe_repo.get_by_id(recipe_id, user_id)
            if not recipe:
                raise EntityNotFoundError(f"Recipe {recipe_id} not found")

        slot = MenuSlot(
            id=MenuSlotId(0),
            menu_id=menu_id,
            recipe_id=recipe_id,
            product_id=product_id,
            servings=servings,
            quantity=quantity,
            meal_type=meal_type,
            day_of_week=day_of_week,
            position=len([s for s in menu.slots if s.day_of_week == day_of_week and s.meal_type == meal_type]),
        )
        return self.menu_repo.add_slot(menu_id, slot)
```

#### DeleteMenuSlot

```python
class DeleteMenuSlot:
    def __init__(self, menu_repo: MenuRepository):
        self.menu_repo = menu_repo

    def execute(self, menu_id: MenuId, slot_id: MenuSlotId, user_id: UserId) -> None:
        """Remove slot from menu."""
        menu = self.menu_repo.get_by_id(menu_id, user_id)
        if not menu:
            raise EntityNotFoundError(f"Menu {menu_id} not found")
        self.menu_repo.delete_slot(menu_id, slot_id)
```

#### ClearMenu

```python
class ClearMenu:
    def __init__(self, menu_repo: MenuRepository):
        self.menu_repo = menu_repo

    def execute(self, menu_id: MenuId, user_id: UserId) -> None:
        """Remove all slots from menu."""
        menu = self.menu_repo.get_by_id(menu_id, user_id)
        if not menu:
            raise EntityNotFoundError(f"Menu {menu_id} not found")

        for slot in menu.slots:
            self.menu_repo.delete_slot(menu_id, slot.id)
```

### Shopping List Generation

**File:** `backend/application/use_cases/generate_shopping_list.py`

#### GenerateShoppingList

Most important use case. Calls domain service to orchestrate the shopping list building.

```python
class GenerateShoppingList:
    def __init__(
        self,
        menu_repo: MenuRepository,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        family_member_repo: FamilyMemberRepository,
        shopping_list_builder: ShoppingListBuilder,
    ):
        self.menu_repo = menu_repo
        self.recipe_repo = recipe_repo
        self.product_repo = product_repo
        self.family_member_repo = family_member_repo
        self.shopping_list_builder = shopping_list_builder

    def execute(self, menu_id: MenuId, user_id: UserId) -> ShoppingList:
        """
        Generate shopping list from menu + family.

        Process:
        1. Load menu with slots
        2. Load all recipes referenced in slots
        3. Load all products
        4. Load family members
        5. Call ShoppingListBuilder to aggregate
        """
        menu = self.menu_repo.get_by_id(menu_id, user_id)
        if not menu:
            raise EntityNotFoundError(f"Menu {menu_id} not found")

        # Fetch all needed recipes
        recipe_ids = {s.recipe_id for s in menu.slots if s.recipe_id}
        recipes = {}
        for rid in recipe_ids:
            recipe = self.recipe_repo.get_by_id(rid, user_id)
            if recipe:
                recipes[rid] = recipe

        # Fetch all products
        products_list = self.product_repo.list_by_user(user_id)
        products = {p.id: p for p in products_list}

        # Fetch family members
        family = self.family_member_repo.list_by_user(user_id)

        # Build shopping list
        return self.shopping_list_builder.build(menu, family, products, recipes)
```

### Product Management

**File:** `backend/application/use_cases/manage_product.py`

Similar pattern to recipes: `ListProducts`, `GetProduct`, `CreateProduct`, `UpdateProduct`, `DeleteProduct`.

### Family Management

**File:** `backend/application/use_cases/manage_family.py`

`CreateFamilyMember`, `UpdateFamilyMember`, `DeleteFamilyMember`, `ListFamilyMembers`.

### Nested Recipes (Flattening)

**File:** `backend/application/use_cases/flatten_recipe_products.py`

Expands sub-recipes into leaf products.

```python
class FlattenRecipeProducts:
    """
    Convert recipe with sub-recipes into final product list.

    Example:
        Recipe "Борщ" includes:
        - Свёкла (product) 500g
        - "Овощной бульон" (sub-recipe) 1 liter

        Flattening expands "Овощной бульон" into its products:
        - Вода 1L
        - Морковь 200g
        - Сельдерей 100g

        Result: Свёкла + Вода + Морковь + Сельдерей
    """

    def __init__(self, recipe_repo: RecipeRepository):
        self.recipe_repo = recipe_repo

    def execute(
        self,
        recipe_id: RecipeId,
        user_id: UserId,
    ) -> list[FlattenedProduct]:
        """Recursively expand sub-recipes, detect cycles."""
        visited: set[RecipeId] = set()
        flattened: list[FlattenedProduct] = []

        def flatten_recursive(rid: RecipeId, factor: float, depth: int = 0) -> None:
            if depth > MAX_NESTING_DEPTH:
                raise NestingDepthExceededError(f"Nesting depth > {MAX_NESTING_DEPTH}")

            if rid in visited:
                raise CircularDependencyError(f"Circular dependency detected at {rid}")

            visited.add(rid)
            recipe = self.recipe_repo.get_by_id(rid, user_id)
            if not recipe:
                raise EntityNotFoundError(f"Recipe {rid} not found")

            for ing in recipe.ingredients:
                if ing.is_product():
                    scaled_qty = Quantity(ing.quantity.amount * factor, ing.quantity.unit)
                    flattened.append(FlattenedProduct(
                        product_id=ing.product_id,
                        quantity=scaled_qty,
                    ))
                else:
                    # Expand sub-recipe
                    flatten_recursive(ing.sub_recipe_id, ing.quantity.amount * factor, depth + 1)

            visited.discard(rid)

        flatten_recursive(recipe_id, 1.0)
        return flattened
```

### Export Operations

**File:** `backend/application/use_cases/export_shopping_list.py`

```python
class ExportShoppingList:
    def __init__(self, exporters: dict[str, ShoppingListExporter]):
        self.exporters = exporters  # "csv", "json", "text"

    def execute(self, shopping_list: ShoppingList, format: str) -> str:
        """Export shopping list to specified format."""
        if format not in self.exporters:
            raise DomainError(f"Unsupported format: {format}")

        exporter = self.exporters[format]
        return exporter.export(shopping_list)
```

### Import Operations

**File:** `backend/application/use_cases/import_entities.py`

```python
class ImportEntities:
    def __init__(
        self,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        importers: dict[str, EntityImporter],
    ):
        self.recipe_repo = recipe_repo
        self.product_repo = product_repo
        self.importers = importers

    def execute(
        self,
        user_id: UserId,
        entity_type: str,  # "recipe" or "product"
        format: str,       # "json" or "csv"
        data: str,
    ) -> ImportResult:
        """Import entities from file."""
        if format not in self.importers:
            raise DomainError(f"Unsupported format: {format}")

        importer = self.importers[format]
        entities = importer.import_entities(entity_type, data)

        # Save imported entities
        for entity in entities:
            entity.user_id = user_id
            if entity_type == "recipe":
                self.recipe_repo.save(entity)
            elif entity_type == "product":
                self.product_repo.save(entity)

        return ImportResult(
            total_imported=len(entities),
            errors=[],
        )
```

---

## Input/Output (DTO) Patterns

### Request DTOs

Input validation via dataclasses:

```python
@dataclass
class CreateRecipeRequest:
    name: str
    servings: int
    category_id: int
    ingredients: list[RecipeIngredientData]
    steps: list[CookingStepData]
    weight: int = 0
    total_pieces: int | None = None
    pieces_per_portion: int | None = None

    def validate(self) -> None:
        if not self.name.strip():
            raise DomainError("Name required")
        if self.servings < 1:
            raise DomainError("Servings >= 1")
```

### Response DTOs

Pydantic schemas in `backend/api/schemas/` map domain objects to HTTP responses:

```python
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

---

## Error Handling Conventions

1. **Validate input** → raise `DomainError` (400)
2. **Entity not found** → raise `EntityNotFoundError` (404)
3. **User conflict** → raise `UserAlreadyExistsError` (409)
4. **Auth failed** → raise `AuthenticationError` (401)
5. **Business rule violation** → raise domain-specific error (422)

All exceptions are caught by FastAPI's `@exception_handler` decorators in `backend/api/main.py` and converted to JSON responses.

---

## Testing Use Cases

**Pattern:** Mock repositories, call `execute()`, assert results.

```python
# tests/unit/application/test_manage_recipe.py

def test_create_recipe():
    # Mock repository
    repo = Mock(spec=RecipeRepository)
    repo.save.return_value = RecipeId(1)

    # Create use case
    uc = CreateRecipe(repo)

    # Execute
    result = uc.execute(
        user_id=UserId(1),
        name="Блины",
        servings=4,
        category_id=RecipeCategoryId(1),
        ingredients=[...],
        steps=[...],
    )

    # Assert
    assert result == RecipeId(1)
    repo.save.assert_called_once()

def test_create_recipe_validation():
    repo = Mock(spec=RecipeRepository)
    uc = CreateRecipe(repo)

    # Should raise DomainError on empty name
    with pytest.raises(DomainError):
        uc.execute(
            user_id=UserId(1),
            name="",  # Invalid
            servings=4,
            category_id=RecipeCategoryId(1),
            ingredients=[],
            steps=[],
        )
```

---

## Summary

The Application layer:
- **Orchestrates** domain logic and repositories
- **Validates** input and enforces business rules
- **Handles transactions** and persistence
- **Is testable** via dependency injection
- **Is reusable** from API, CLI, or events

Each use case represents a single user operation, making the codebase easy to understand and maintain.

---

**Next:** See [backend-infrastructure.md](05-backend-infrastructure.md) for repository and ORM details.
