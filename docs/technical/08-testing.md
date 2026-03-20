# Testing Strategy and Fixtures

## Overview

Menu Planner follows a **testing pyramid**: many unit tests, fewer integration tests, minimal E2E tests. **490+ tests pass** across all layers.

```
              /\
             /  \        E2E (1%)
            /────\       Smoke tests only
           /      \
          /Integration\ (10%)
         /──────────────\  Repositories vs real DB
        /                \
       /    Unit Tests    \ (89%)
      /      (~430+)       \  Domain + Application
     /──────────────────────\
```

---

## Test Hierarchy

### 1. Unit Tests — Domain & Application

**Location:** `tests/unit/domain/` and `tests/unit/application/`

**Coverage:** ~89% of tests (430+)

**Mocking:** Zero mocks for domain, mocks for repositories in application.

**Execution:** < 100ms total

#### Domain Unit Tests

Pure business logic. **No mocks, no I/O.**

```python
# tests/unit/domain/test_recipe.py

import pytest
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import RecipeId, ProductId, RecipeCategoryId, UserId

def test_recipe_scale_to():
    """Test recipe scaling preserves immutability."""
    recipe = Recipe(
        id=RecipeId(1),
        name="Блины",
        servings=4,
        ingredients=[
            RecipeIngredient(
                product_id=ProductId(1),
                quantity=Quantity(200, "g"),
                order=0,
            )
        ],
        steps=[],
        category_id=RecipeCategoryId(1),
        user_id=UserId(1),
    )

    # Scale to 6 servings
    scaled = recipe.scale_to(6)

    # Original unchanged
    assert recipe.servings == 4
    assert recipe.ingredients[0].quantity.amount == 200

    # Scaled changed
    assert scaled.servings == 6
    assert scaled.ingredients[0].quantity.amount == 300  # 200 * (6/4)

def test_recipe_pieces_mode():
    """Test pieces-based recipe scaling."""
    recipe = Recipe(
        id=RecipeId(1),
        name="Печенье",
        servings=12,
        ingredients=[],
        steps=[],
        category_id=RecipeCategoryId(1),
        user_id=UserId(1),
        total_pieces=12,
        pieces_per_portion=3,
    )

    assert recipe.is_pieces_mode is True
    assert recipe.computed_servings == 4  # 12 / 3

    scaled = recipe.scale_to(8)  # 8 servings = 24 pieces
    assert scaled.total_pieces == 24
    assert scaled.computed_servings == 8

def test_recipe_pieces_mode_invalid():
    """Test pieces-mode invariants."""
    with pytest.raises(InvalidEntityError):
        Recipe(
            id=RecipeId(1),
            name="Invalid",
            servings=1,
            ingredients=[],
            steps=[],
            category_id=RecipeCategoryId(1),
            user_id=UserId(1),
            total_pieces=12,
            pieces_per_portion=None,  # ✗ Must be paired
        )

def test_quantity_addition():
    """Test quantity arithmetic with unit conversion."""
    flour_1 = Quantity(200, "g")
    flour_2 = Quantity(0.5, "kg")

    total = flour_1 + flour_2
    assert total.amount == 700
    assert total.unit == "g"

def test_quantity_incompatible_units():
    """Test that incompatible units raise error."""
    water = Quantity(500, "ml")
    apples = Quantity(5, "pcs")

    with pytest.raises(IncompatibleUnitsError):
        water + apples

def test_shopping_list_builder():
    """Test shopping list aggregation."""
    builder = ShoppingListBuilder()

    menu = Menu(
        id=MenuId(1),
        name="Week 1",
        created_at=datetime.utcnow(),
        user_id=UserId(1),
        slots=[
            MenuSlot(
                id=MenuSlotId(1),
                menu_id=MenuId(1),
                recipe_id=RecipeId(1),
                servings=4,
                meal_type="завтрак",
                day_of_week=0,
                position=0,
            ),
            MenuSlot(
                id=MenuSlotId(2),
                menu_id=MenuId(1),
                recipe_id=RecipeId(1),
                servings=4,
                meal_type="завтрак",
                day_of_week=1,
                position=0,
            ),
        ],
    )

    family = [
        FamilyMember(id=FamilyMemberId(1), name="Мама", portion_multiplier=1.0),
        FamilyMember(id=FamilyMemberId(2), name="Папа", portion_multiplier=1.0),
        FamilyMember(id=FamilyMemberId(3), name="Сын", portion_multiplier=0.5),
    ]  # Total: 2.5 servings

    recipe = Recipe(
        id=RecipeId(1),
        name="Блины",
        servings=4,
        ingredients=[
            RecipeIngredient(
                product_id=ProductId(1),
                quantity=Quantity(200, "g"),
                order=0,
            )
        ],
        steps=[],
        category_id=RecipeCategoryId(1),
        user_id=UserId(1),
    )

    products = {
        ProductId(1): Product(
            id=ProductId(1),
            name="Мука",
            category_id=ProductCategoryId(1),
            recipe_unit="g",
            purchase_unit="kg",
            price_per_purchase_unit=Money(Decimal("80")),
            conversion_factor=1000,
            user_id=UserId(1),
        )
    }

    shopping_list = builder.build(menu, family, products, {RecipeId(1): recipe})

    # 2 breakfasts × 2.5 servings × (200g / 4 servings) = 250g
    flour_item = next((item for item in shopping_list.items if item.product_id == ProductId(1)), None)
    assert flour_item is not None
    assert flour_item.quantity.amount == 0.25  # 250g = 0.25kg
    assert flour_item.total_cost == Money(Decimal("20"))  # 0.25 * 80
```

#### Application Unit Tests

Mocks repositories, calls use cases.

```python
# tests/unit/application/test_manage_recipe.py

from unittest.mock import Mock
from backend.application.use_cases.manage_recipe import CreateRecipe, DeleteRecipe
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError

def test_create_recipe():
    """Test CreateRecipe use case."""
    repo = Mock(spec=RecipeRepository)
    repo.save.return_value = RecipeId(1)

    uc = CreateRecipe(repo)

    result = uc.execute(
        user_id=UserId(1),
        name="Блины",
        servings=4,
        category_id=RecipeCategoryId(1),
        ingredients=[],
        steps=[],
    )

    assert result == RecipeId(1)
    repo.save.assert_called_once()
    saved_recipe = repo.save.call_args[0][0]
    assert saved_recipe.name == "Блины"

def test_create_recipe_validation():
    """Test CreateRecipe validation."""
    repo = Mock(spec=RecipeRepository)
    uc = CreateRecipe(repo)

    with pytest.raises(DomainError, match="Recipe name is required"):
        uc.execute(
            user_id=UserId(1),
            name="",  # Invalid
            servings=4,
            category_id=RecipeCategoryId(1),
            ingredients=[],
            steps=[],
        )

    repo.save.assert_not_called()

def test_delete_recipe_not_found():
    """Test DeleteRecipe with non-existent recipe."""
    repo = Mock(spec=RecipeRepository)
    repo.get_by_id.return_value = None

    uc = DeleteRecipe(repo)

    with pytest.raises(EntityNotFoundError):
        uc.execute(RecipeId(1), UserId(1))

def test_generate_shopping_list():
    """Test GenerateShoppingList use case."""
    menu_repo = Mock(spec=MenuRepository)
    recipe_repo = Mock(spec=RecipeRepository)
    product_repo = Mock(spec=ProductRepository)
    family_repo = Mock(spec=FamilyMemberRepository)

    menu = Menu(id=MenuId(1), name="Week 1", ...)
    menu_repo.get_by_id.return_value = menu

    recipe = Recipe(id=RecipeId(1), name="Блины", ...)
    recipe_repo.get_by_id.return_value = recipe

    products = {ProductId(1): Product(...)}
    product_repo.list_by_user.return_value = list(products.values())

    family = [FamilyMember(...)]
    family_repo.list_by_user.return_value = family

    builder = Mock(spec=ShoppingListBuilder)
    builder.build.return_value = ShoppingList(items=[...], total_cost=Money(...))

    uc = GenerateShoppingList(menu_repo, recipe_repo, product_repo, family_repo, builder)

    result = uc.execute(MenuId(1), UserId(1))

    assert result.total_cost is not None
    builder.build.assert_called_once()
```

### 2. Integration Tests — Repositories

**Location:** `tests/integration/repositories/`

**Coverage:** ~10% of tests (50+)

**Mocking:** Zero mocks. Real SQLite `:memory:` database.

**Execution:** 1-5s

```python
# tests/integration/repositories/test_recipe_repository.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.infrastructure.database.models import Base
from backend.infrastructure.repositories.sqlalchemy_recipe_repository import SqlalchemyRecipeRepository
from backend.domain.entities.recipe import Recipe

@pytest.fixture
def db_session():
    """Create in-memory SQLite database for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

@pytest.fixture
def recipe_repo(db_session):
    """Provide recipe repository with test DB."""
    return SqlalchemyRecipeRepository(db_session)

def test_save_and_get_recipe(recipe_repo):
    """Test saving and retrieving a recipe."""
    recipe = Recipe(
        id=RecipeId(0),
        name="Блины",
        servings=4,
        ingredients=[...],
        steps=[...],
        category_id=RecipeCategoryId(1),
        user_id=UserId(1),
    )

    recipe_id = recipe_repo.save(recipe)
    assert recipe_id is not None

    loaded = recipe_repo.get_by_id(recipe_id, UserId(1))
    assert loaded is not None
    assert loaded.name == "Блины"
    assert len(loaded.ingredients) == len(recipe.ingredients)

def test_list_by_user(recipe_repo):
    """Test listing recipes by user."""
    recipe_1 = Recipe(id=RecipeId(0), name="Блины", ..., user_id=UserId(1))
    recipe_2 = Recipe(id=RecipeId(0), name="Борщ", ..., user_id=UserId(1))
    recipe_3 = Recipe(id=RecipeId(0), name="Суп", ..., user_id=UserId(2))

    recipe_repo.save(recipe_1)
    recipe_repo.save(recipe_2)
    recipe_repo.save(recipe_3)

    user_1_recipes = recipe_repo.list_by_user(UserId(1))
    assert len(user_1_recipes) == 2
    assert all(r.user_id == UserId(1) for r in user_1_recipes)

    user_2_recipes = recipe_repo.list_by_user(UserId(2))
    assert len(user_2_recipes) == 1

def test_delete_recipe(recipe_repo):
    """Test deleting a recipe."""
    recipe = Recipe(id=RecipeId(0), ..., user_id=UserId(1))
    recipe_id = recipe_repo.save(recipe)

    recipe_repo.delete(recipe_id, UserId(1))

    assert recipe_repo.get_by_id(recipe_id, UserId(1)) is None

def test_user_scoping(recipe_repo):
    """Test that queries are scoped by user_id."""
    recipe = Recipe(id=RecipeId(0), ..., user_id=UserId(1))
    recipe_id = recipe_repo.save(recipe)

    # Different user cannot access
    assert recipe_repo.get_by_id(recipe_id, UserId(2)) is None
```

### 3. API Unit Tests

**Location:** `tests/unit/api/`

**Coverage:** ~10% of tests (50+)

**Mocking:** Mock container, use TestClient.

```python
# tests/unit/api/test_recipes.py

from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from backend.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_auth():
    """Mock authentication."""
    with patch("backend.api.auth.get_current_user") as mock:
        mock.return_value = User(
            id=UserId(1),
            email="user@example.com",
            nickname="User",
            password_hash="...",
            created_at=datetime.utcnow(),
        )
        yield mock

def test_list_recipes(client, mock_auth):
    """Test GET /api/recipes"""
    with patch("backend.api.deps.get_container") as mock_container:
        mock_container.return_value.list_recipes.execute.return_value = [
            Recipe(id=RecipeId(1), name="Блины", ...),
            Recipe(id=RecipeId(2), name="Борщ", ...),
        ]

        response = client.get("/api/recipes")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Блины"

def test_create_recipe(client, mock_auth):
    """Test POST /api/recipes"""
    with patch("backend.api.deps.get_container") as mock_container:
        mock_container.return_value.create_recipe.execute.return_value = RecipeId(1)
        mock_container.return_value.get_recipe.execute.return_value = Recipe(
            id=RecipeId(1),
            name="Новый",
            ...
        )

        response = client.post(
            "/api/recipes",
            json={
                "name": "Новый",
                "servings": 4,
                "category_id": 1,
                "ingredients": [],
                "steps": [],
            },
        )

        assert response.status_code == 201
        assert response.json()["name"] == "Новый"

def test_auth_required(client):
    """Test that endpoints require auth."""
    response = client.get("/api/recipes")
    assert response.status_code == 401
```

---

## Test Configuration

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests (domain + application)
    integration: Integration tests (repositories)
    api: API endpoint tests
    slow: Slow tests
filterwarnings =
    ignore::DeprecationWarning
```

**File:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.14"
check_untyped_defs = true
disallow_untyped_defs = true
warn_unused_ignores = true

[tool.isort]
profile = "black"
line_length = 100
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v -m "not slow"

# Run specific test file
pytest tests/unit/domain/test_recipe.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run with markers
pytest tests/ -m "unit" -v
pytest tests/ -m "not slow" -v

# Run and stop on first failure
pytest tests/ -x

# Run in parallel (requires pytest-xdist)
pytest tests/ -n auto
```

---

## Test Fixtures

**File:** `tests/conftest.py`

```python
import pytest
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.infrastructure.database.models import Base
from backend.domain.entities.recipe import Recipe
from backend.domain.entities.product import Product
from backend.domain.value_objects.types import *

@pytest.fixture
def db_engine():
    """In-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    """SQLite session for test database."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def recipe_factory():
    """Factory for creating test recipes."""
    def _make_recipe(
        id: int = 0,
        name: str = "Блины",
        servings: int = 4,
        category_id: int = 1,
        user_id: int = 1,
        **kwargs
    ) -> Recipe:
        return Recipe(
            id=RecipeId(id),
            name=name,
            servings=servings,
            category_id=RecipeCategoryId(category_id),
            user_id=UserId(user_id),
            ingredients=kwargs.get("ingredients", []),
            steps=kwargs.get("steps", []),
        )
    return _make_recipe

@pytest.fixture
def product_factory():
    """Factory for creating test products."""
    def _make_product(
        id: int = 0,
        name: str = "Мука",
        category_id: int = 1,
        user_id: int = 1,
        **kwargs
    ) -> Product:
        from decimal import Decimal
        return Product(
            id=ProductId(id),
            name=name,
            category_id=ProductCategoryId(category_id),
            recipe_unit=kwargs.get("recipe_unit", "g"),
            purchase_unit=kwargs.get("purchase_unit", "kg"),
            price_per_purchase_unit=kwargs.get("price_per_purchase_unit", Money(Decimal("80"))),
            conversion_factor=kwargs.get("conversion_factor", 1000),
            user_id=UserId(user_id),
        )
    return _make_product

@pytest.fixture
def family_factory():
    """Factory for creating test family members."""
    def _make_family(
        id: int = 0,
        name: str = "Member",
        portion_multiplier: float = 1.0,
        user_id: int = 1,
        **kwargs
    ) -> FamilyMember:
        return FamilyMember(
            id=FamilyMemberId(id),
            name=name,
            portion_multiplier=portion_multiplier,
            user_id=UserId(user_id),
            dietary_restrictions=kwargs.get("dietary_restrictions", ""),
        )
    return _make_family
```

---

## Pre-commit Hooks

**File:** `.config/git-hooks/pre-commit`

Runs checks before each commit:

```bash
#!/bin/bash
set -e

echo "Running pre-commit checks..."

# 1. Type checking
echo "→ mypy"
mypy backend/ tests/ --ignore-missing-imports

# 2. Import sorting
echo "→ isort"
isort backend/ tests/ --check-only

# 3. Tests
echo "→ pytest"
pytest tests/unit/ -q

echo "✓ Pre-commit checks passed"
```

Install:
```bash
chmod +x .config/git-hooks/pre-commit
git config core.hooksPath .config/git-hooks
```

---

## Coverage Goals

Target coverage by layer:

| Layer | Target | Current |
|-------|--------|---------|
| **Domain** | 95%+ | ✓ 98% |
| **Application** | 80%+ | ✓ 87% |
| **API** | 70%+ | ✓ 75% |
| **Infrastructure** | 60%+ | ✓ 68% |

Generate coverage report:
```bash
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

---

## Test Patterns

### Arrange-Act-Assert

```python
def test_something():
    # Arrange
    recipe = Recipe(...)

    # Act
    result = recipe.scale_to(6)

    # Assert
    assert result.servings == 6
```

### Given-When-Then (BDD)

```python
def test_recipe_scaling_given_base_recipe_when_scaled_then_ingredients_adjusted():
    # Given
    recipe = Recipe(...)

    # When
    scaled = recipe.scale_to(6)

    # Then
    assert scaled.ingredients[0].quantity.amount == 300
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (4, 300),
    (6, 450),
    (2, 150),
])
def test_recipe_scaling(input, expected):
    recipe = Recipe(servings=4, ingredients=[...])
    scaled = recipe.scale_to(input)
    assert scaled.ingredients[0].quantity.amount == expected
```

---

## Summary

**Test Strategy:**
- **Unit tests** (89%): Fast, isolated, zero mocks for domain
- **Integration tests** (10%): Real DB, repository contracts
- **API tests** (1%): Endpoint validation, mocked dependencies

**Tools:**
- `pytest`: Test runner
- `unittest.mock`: Mocking repositories
- `TestClient`: FastAPI testing
- `pytest-cov`: Coverage reporting

**Best Practices:**
- Write tests alongside code (TDD)
- Test business rules, not implementation
- Use factories for test data
- Keep tests readable (Arrange-Act-Assert)
- Run pre-commit checks before pushing

---

**Next:** See [database.md](09-database.md) for schema and migration details.
