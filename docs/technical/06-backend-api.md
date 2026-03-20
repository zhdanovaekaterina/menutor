# API Layer — FastAPI, Routers, Schemas, Auth

**File location:** `backend/api/`

The API layer is a thin HTTP adapter translating requests to domain operations and responses. It handles routing, validation (Pydantic schemas), authentication middleware, and error handling.

---

## FastAPI App Setup

**File:** `backend/api/main.py`

```python
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.composition_root import ApplicationContainer
from backend.domain.exceptions import (
    AppError, AuthenticationError, EntityNotFoundError, DomainError,
    CircularDependencyError, NestingDepthExceededError,
)

# ─── Lifespan: Create ApplicationContainer at startup ────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize dependencies when app starts."""
    app.state.container = ApplicationContainer()
    yield
    # Cleanup on shutdown (if needed)

# ─── Create FastAPI app ───────────────────────────────────────

app = FastAPI(
    title="Menutor API",
    description="API планировщика меню",
    version=os.environ.get("VERSION", "0.1.0"),
    lifespan=lifespan,
)

# ─── CORS Middleware ──────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ────────────────────────────────────────
# Map domain exceptions to HTTP responses

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(EntityNotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(CircularDependencyError)
async def circular_dep_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "error_type": "circular_dependency"},
    )

@app.exception_handler(DomainError)
async def domain_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

# ─── Router Registration ──────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(menus.router, prefix="/api")
app.include_router(family.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(shopping_list.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(system.router, prefix="/api")
```

**Run:**
```bash
uvicorn backend.api.main:app --reload
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
# OpenAPI JSON: http://localhost:8000/openapi.json
```

---

## Authentication Middleware

**File:** `backend/api/auth.py`

```python
from fastapi import Depends, HTTPException, Request, status
from backend.api.deps import get_container
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.exceptions import AuthenticationError

def get_current_user(
    request: Request,
    container: ApplicationContainer = Depends(get_container),
) -> User:
    """
    Extract and validate JWT from Authorization header.

    Expected header: Authorization: Bearer <jwt_token>

    Raises:
        HTTPException(401): No token, invalid token, or user not found
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.removeprefix("Bearer ")

    try:
        # Use GetCurrentUser use case to validate token and fetch user
        return container.get_current_user.execute(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
```

**Usage in routes:**

```python
@router.get("/recipes")
def list_recipes(
    user: User = Depends(get_current_user),  # ← Injected by FastAPI
    container: ApplicationContainer = Depends(get_container),
) -> list[RecipeResponse]:
    recipes = container.list_recipes.execute(user.id)
    return [recipe_to_response(r) for r in recipes]
```

---

## Dependency Injection

**File:** `backend/api/deps.py`

```python
from fastapi import Request
from backend.composition_root import ApplicationContainer

def get_container(request: Request) -> ApplicationContainer:
    """
    FastAPI dependency: retrieve ApplicationContainer from app.state.

    The container is created once during app startup (lifespan).
    It holds all use cases and repositories.
    """
    return request.app.state.container
```

---

## Pydantic Schemas

**File:** `backend/api/schemas/recipe.py`

Request/response models with validation.

```python
from pydantic import BaseModel, Field
from typing import Optional

# ─── Request Schemas ──────────────────────────────────────────

class RecipeIngredientCreate(BaseModel):
    product_id: int
    sub_recipe_id: Optional[int] = None
    quantity_amount: float = Field(..., gt=0)
    quantity_unit: str = Field(..., min_length=1, max_length=50)

class CookingStepCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=1000)
    order: int = Field(default=0, ge=0)

class RecipeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    servings: int = Field(..., gt=0)
    category_id: int
    ingredients: list[RecipeIngredientCreate]
    steps: list[CookingStepCreate]
    weight: int = Field(default=0, ge=0)
    total_pieces: Optional[int] = None
    pieces_per_portion: Optional[int] = None

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    servings: Optional[int] = None
    category_id: Optional[int] = None
    ingredients: Optional[list[RecipeIngredientCreate]] = None
    steps: Optional[list[CookingStepCreate]] = None
    weight: Optional[int] = None
    total_pieces: Optional[int] = None
    pieces_per_portion: Optional[int] = None

# ─── Response Schemas ─────────────────────────────────────────

class RecipeIngredientResponse(BaseModel):
    product_id: int
    sub_recipe_id: Optional[int]
    quantity_amount: float
    quantity_unit: str
    sub_recipe_name: Optional[str] = None  # Name of sub-recipe if present

class CookingStepResponse(BaseModel):
    description: str
    order: int

class RecipeResponse(BaseModel):
    id: int
    name: str
    servings: int
    category_id: int
    ingredients: list[RecipeIngredientResponse]
    steps: list[CookingStepResponse]
    weight: int
    total_pieces: Optional[int]
    pieces_per_portion: Optional[int]

    class Config:
        from_attributes = True  # Allow creating from ORM models
```

Other schema files:
- `backend/api/schemas/auth.py` — LoginRequest, RegisterRequest, TokenResponse
- `backend/api/schemas/product.py` — ProductCreate, ProductResponse
- `backend/api/schemas/menu.py` — MenuCreate, MenuSlotCreate, MenuResponse
- `backend/api/schemas/family.py` — FamilyMemberCreate, FamilyMemberResponse
- `backend/api/schemas/category.py` — CategoryCreate, CategoryResponse
- `backend/api/schemas/shopping_list.py` — ShoppingListResponse, ShoppingListItemResponse
- `backend/api/schemas/import_export.py` — ImportRequest, ExportRequest

---

## Converters

**File:** `backend/api/converters.py`

Convert domain entities ↔ Pydantic schemas.

```python
from backend.domain.entities.recipe import Recipe
from backend.api.schemas.recipe import RecipeResponse, RecipeIngredientResponse

def recipe_to_response(
    recipe: Recipe,
    name_lookup: callable = None,  # Function to get sub-recipe names
) -> RecipeResponse:
    """Convert domain Recipe to API response."""
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
                sub_recipe_name=name_lookup(ing.sub_recipe_id) if ing.sub_recipe_id and name_lookup else None,
            )
            for ing in recipe.ingredients
        ],
        steps=[
            CookingStepResponse(
                description=step.description,
                order=step.order,
            )
            for step in recipe.steps
        ],
        weight=recipe.weight,
        total_pieces=recipe.total_pieces,
        pieces_per_portion=recipe.pieces_per_portion,
    )

def schema_to_recipe_data(schema: RecipeCreate) -> dict:
    """Convert request schema to use-case parameters."""
    return {
        "name": schema.name,
        "servings": schema.servings,
        "category_id": RecipeCategoryId(schema.category_id),
        "ingredients": [
            RecipeIngredient(
                product_id=ProductId(ing.product_id),
                sub_recipe_id=RecipeId(ing.sub_recipe_id) if ing.sub_recipe_id else None,
                quantity=Quantity(ing.quantity_amount, ing.quantity_unit),
                order=i,
            )
            for i, ing in enumerate(schema.ingredients)
        ],
        "steps": [
            CookingStep(
                description=step.description,
                order=step.order,
            )
            for step in schema.steps
        ],
        "weight": schema.weight,
        "total_pieces": schema.total_pieces,
        "pieces_per_portion": schema.pieces_per_portion,
    }
```

---

## Router Endpoints

**File:** `backend/api/routers/recipes.py`

Each router handles one domain concept (recipes, products, menus, etc.).

```python
from fastapi import APIRouter, Depends, Query, status
from backend.api.auth import get_current_user
from backend.api.deps import get_container
from backend.api.schemas.recipe import RecipeCreate, RecipeResponse, RecipeUpdate
from backend.api.converters import recipe_to_response, schema_to_recipe_data
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import RecipeId, RecipeCategoryId

router = APIRouter(prefix="/recipes", tags=["recipes"])

# ─── GET / List recipes ───────────────────────────────────────

@router.get("", response_model=list[RecipeResponse])
def list_recipes(
    category_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> list[RecipeResponse]:
    """
    List all user's recipes, optionally filtered by category.

    Query Parameters:
        category_id (optional): Filter by recipe category
    """
    recipes = container.list_recipes.execute(
        user.id,
        RecipeCategoryId(category_id) if category_id else None
    )

    # Name lookup for sub-recipes
    def name_lookup(recipe_id):
        r = container.get_recipe.execute(recipe_id, user.id)
        return r.name if r else None

    return [recipe_to_response(r, name_lookup) for r in recipes]

# ─── GET /{id} Get one recipe ────────────────────────────────

@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    """Get recipe by ID."""
    recipe = container.get_recipe.execute(RecipeId(recipe_id), user.id)
    def name_lookup(rid):
        r = container.get_recipe.execute(rid, user.id)
        return r.name if r else None
    return recipe_to_response(recipe, name_lookup)

# ─── POST Create recipe ────────────────────────────────────────

@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    body: RecipeCreate,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    """
    Create a new recipe.

    Request Body:
        name: Recipe name (required)
        servings: Number of servings (required)
        category_id: Recipe category ID (required)
        ingredients: List of ingredients with quantities
        steps: Cooking instructions
        total_pieces: Optional, for pieces-based recipes
        pieces_per_portion: Optional, for pieces-based recipes
    """
    data = schema_to_recipe_data(body)

    recipe_id = container.create_recipe.execute(
        user_id=user.id,
        **data
    )

    recipe = container.get_recipe.execute(recipe_id, user.id)
    return recipe_to_response(recipe)

# ─── PUT Update recipe ─────────────────────────────────────────

@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    body: RecipeUpdate,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    """Update recipe fields."""
    data = {
        key: val for key, val in schema_to_recipe_data(body).items()
        if val is not None
    }

    container.update_recipe.execute(
        RecipeId(recipe_id),
        user_id=user.id,
        **data
    )

    recipe = container.get_recipe.execute(RecipeId(recipe_id), user.id)
    return recipe_to_response(recipe)

# ─── DELETE Delete recipe ──────────────────────────────────────

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> None:
    """Delete recipe."""
    container.delete_recipe.execute(RecipeId(recipe_id), user.id)
```

### Auth Router

**File:** `backend/api/routers/auth.py`

```python
from fastapi import APIRouter
from backend.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from backend.composition_root import ApplicationContainer

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    body: RegisterRequest,
    container: ApplicationContainer = Depends(get_container),
) -> TokenResponse:
    """Register new user."""
    user_id = container.register_user.execute(
        email=body.email,
        password=body.password,
        nickname=body.nickname,
    )

    # Auto-login after registration
    login_resp = container.login_user.execute(body.email, body.password)
    return login_resp

@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    container: ApplicationContainer = Depends(get_container),
) -> TokenResponse:
    """Login user and return tokens."""
    return container.login_user.execute(body.email, body.password)

@router.post("/refresh", response_model=str)
def refresh(
    refresh_token: str,
    container: ApplicationContainer = Depends(get_container),
) -> str:
    """Refresh access token using refresh token."""
    return container.refresh_access_token.execute(refresh_token)

@router.get("/me", response_model=UserResponse)
def get_me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user profile."""
    return UserResponse(
        id=int(user.id),
        email=user.email,
        nickname=user.nickname,
    )
```

### Other Routers

- `products.py` — CRUD products (similar to recipes)
- `menus.py` — Create, load, manage menu slots
- `family.py` — CRUD family members
- `categories.py` — CRUD product and recipe categories
- `shopping_list.py` — Generate and export shopping lists
- `import_export.py` — Import/export recipes and products
- `system.py` — Health check, version info

---

## Error Responses

All errors follow this JSON format:

```json
{
  "detail": "Human-readable error message"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**HTTP Status Codes:**

| Code | Exception | Use Case |
|------|-----------|----------|
| 201 | — | Resource created (POST) |
| 204 | — | Deleted successfully (DELETE) |
| 400 | `AppError` | Generic application error |
| 401 | `AuthenticationError` | Invalid token or credentials |
| 404 | `EntityNotFoundError` | Resource not found |
| 409 | `UserAlreadyExistsError` | Conflict (email already registered) |
| 422 | `DomainError`, `CircularDependencyError` | Business rule violation |
| 500 | `RepositoryError` | Database error |

---

## API Testing

**Pattern:** Use TestClient from `fastapi.testclient`.

```python
# tests/unit/api/test_recipes.py

from fastapi.testclient import TestClient
from backend.api.main import app
from unittest.mock import Mock, patch

def test_list_recipes():
    """Test GET /api/recipes"""
    client = TestClient(app)

    # Mock authentication
    with patch("backend.api.auth.get_current_user") as mock_auth:
        mock_auth.return_value = User(
            id=UserId(1),
            email="user@example.com",
            nickname="User",
            password_hash="...",
            created_at=datetime.utcnow(),
        )

        # Mock container
        with patch("backend.api.deps.get_container") as mock_container:
            mock_container.return_value.list_recipes.execute.return_value = [
                Recipe(id=RecipeId(1), name="Блины", ...),
                Recipe(id=RecipeId(2), name="Борщ", ...),
            ]

            response = client.get("/api/recipes")

            assert response.status_code == 200
            assert len(response.json()) == 2
            assert response.json()[0]["name"] == "Блины"

def test_create_recipe():
    """Test POST /api/recipes"""
    client = TestClient(app)

    body = {
        "name": "Новый рецепт",
        "servings": 4,
        "category_id": 1,
        "ingredients": [],
        "steps": [],
    }

    with patch("backend.api.auth.get_current_user"), \
         patch("backend.api.deps.get_container") as mock_container:

        mock_container.return_value.create_recipe.execute.return_value = RecipeId(1)
        mock_container.return_value.get_recipe.execute.return_value = Recipe(...)

        response = client.post("/api/recipes", json=body)

        assert response.status_code == 201
        assert response.json()["name"] == "Новый рецепт"

def test_auth_required():
    """Test that endpoints require authentication"""
    client = TestClient(app)

    response = client.get("/api/recipes")

    assert response.status_code == 401
    assert "Требуется авторизация" in response.json()["detail"]
```

---

## Summary

The API layer:
- **Accepts** HTTP requests and validates with Pydantic
- **Extracts** current user via JWT middleware
- **Calls** use cases via ApplicationContainer
- **Converts** domain entities to response schemas
- **Returns** JSON with appropriate status codes
- **Handles** errors via exception handlers

Key principles:
- Stateless (no session storage)
- Type-safe (Pydantic validation)
- Testable (via mocking)
- Clear error messages (for frontend)

All endpoints are documented in Swagger UI at `/docs`.

---

**Next:** See [frontend.md](07-frontend.md) for Vue 3 frontend architecture.
