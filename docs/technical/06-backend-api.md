# Слой API — FastAPI, маршруты, схемы, аутентификация

**Расположение:** `backend/api/`

Слой API является тонким HTTP-адаптером, преобразующим запросы в доменные операции и ответы. Он обрабатывает маршрутизацию, валидацию (схемы Pydantic), middleware аутентификации и обработку ошибок.

---

## Настройка FastAPI приложения

**Файл:** `backend/api/main.py`

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

# ─── Lifespan: Создание ApplicationContainer при запуске ────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация зависимостей при запуске приложения."""
    app.state.container = ApplicationContainer()
    yield
    # Очистка при завершении (если необходимо)

# ─── Создание FastAPI приложения ───────────────────────────────────────

app = FastAPI(
    title="Menutor API",
    description="API планировщика меню",
    version=os.environ.get("VERSION", "0.1.0"),
    lifespan=lifespan,
)

# ─── CORS Middleware ──────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Разрешить все источники в разработке
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Обработчики исключений ────────────────────────────────────────
# Преобразование доменных исключений в HTTP ответы

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

# ─── Регистрация маршрутизаторов ──────────────────────────────────────

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

**Запуск:**
```bash
uvicorn backend.api.main:app --reload
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
# OpenAPI JSON: http://localhost:8000/openapi.json
```

---

## Middleware аутентификации

**Файл:** `backend/api/auth.py`

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
    Извлечение и валидация JWT из заголовка Authorization.

    Ожидаемый заголовок: Authorization: Bearer <jwt_token>

    Вызывает исключение:
        HTTPException(401): Нет токена, неверный токен или пользователь не найден
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
        # Использование use case GetCurrentUser для валидации токена и получения пользователя
        return container.get_current_user.execute(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
```

**Использование в маршрутах:**

```python
@router.get("/recipes")
def list_recipes(
    user: User = Depends(get_current_user),  # ← Внедрено FastAPI
    container: ApplicationContainer = Depends(get_container),
) -> list[RecipeResponse]:
    recipes = container.list_recipes.execute(user.id)
    return [recipe_to_response(r) for r in recipes]
```

---

## Внедрение зависимостей

**Файл:** `backend/api/deps.py`

```python
from fastapi import Request
from backend.composition_root import ApplicationContainer

def get_container(request: Request) -> ApplicationContainer:
    """
    Зависимость FastAPI: получение ApplicationContainer из app.state.

    Контейнер создается один раз при запуске приложения (lifespan).
    Он содержит все use case и репозитории.
    """
    return request.app.state.container
```

---

## Схемы Pydantic

**Файл:** `backend/api/schemas/recipe.py`

Модели запроса/ответа с валидацией.

```python
from pydantic import BaseModel, Field
from typing import Optional

# ─── Схемы запроса ──────────────────────────────────────────

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

# ─── Схемы ответа ─────────────────────────────────────────

class RecipeIngredientResponse(BaseModel):
    product_id: int
    sub_recipe_id: Optional[int]
    quantity_amount: float
    quantity_unit: str
    sub_recipe_name: Optional[str] = None  # Имя под-рецепта если присутствует

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
        from_attributes = True  # Разрешить создание из ORM моделей
```

Другие файлы схем:
- `backend/api/schemas/auth.py` — LoginRequest, RegisterRequest, TokenResponse
- `backend/api/schemas/product.py` — ProductCreate, ProductResponse
- `backend/api/schemas/menu.py` — MenuCreate, MenuSlotCreate, MenuResponse
- `backend/api/schemas/family.py` — FamilyMemberCreate, FamilyMemberResponse
- `backend/api/schemas/category.py` — CategoryCreate, CategoryResponse
- `backend/api/schemas/shopping_list.py` — ShoppingListResponse, ShoppingListItemResponse
- `backend/api/schemas/import_export.py` — ImportRequest, ExportRequest

---

## Конвертеры

**Файл:** `backend/api/converters.py`

Преобразование доменных сущностей ↔ схемы Pydantic.

```python
from backend.domain.entities.recipe import Recipe
from backend.api.schemas.recipe import RecipeResponse, RecipeIngredientResponse

def recipe_to_response(
    recipe: Recipe,
    name_lookup: callable = None,  # Функция для получения имен под-рецептов
) -> RecipeResponse:
    """Преобразование доменного рецепта в API ответ."""
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
    """Преобразование схемы запроса в параметры use case."""
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

## Маршруты эндпоинтов

**Файл:** `backend/api/routers/recipes.py`

Каждый маршрутизатор обрабатывает одну доменную концепцию (рецепты, продукты, меню и т.д.).

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

# ─── GET / Список рецептов ───────────────────────────────────────

@router.get("", response_model=list[RecipeResponse])
def list_recipes(
    category_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> list[RecipeResponse]:
    """
    Получить все рецепты пользователя, опционально отфильтрованные по категории.

    Параметры запроса:
        category_id (опционально): Фильтр по категории рецепта
    """
    recipes = container.list_recipes.execute(
        user.id,
        RecipeCategoryId(category_id) if category_id else None
    )

    # Поиск имен для под-рецептов
    def name_lookup(recipe_id):
        r = container.get_recipe.execute(recipe_id, user.id)
        return r.name if r else None

    return [recipe_to_response(r, name_lookup) for r in recipes]

# ─── GET /{id} Получить один рецепт ────────────────────────────

@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    """Получить рецепт по ID."""
    recipe = container.get_recipe.execute(RecipeId(recipe_id), user.id)
    def name_lookup(rid):
        r = container.get_recipe.execute(rid, user.id)
        return r.name if r else None
    return recipe_to_response(recipe, name_lookup)

# ─── POST Создать рецепт ────────────────────────────────────────

@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    body: RecipeCreate,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    """
    Создать новый рецепт.

    Тело запроса:
        name: Название рецепта (обязательно)
        servings: Количество порций (обязательно)
        category_id: ID категории рецепта (обязательно)
        ingredients: Список ингредиентов с количеством
        steps: Инструкции приготовления
        total_pieces: Опционально, для штучных рецептов
        pieces_per_portion: Опционально, для штучных рецептов
    """
    data = schema_to_recipe_data(body)

    recipe_id = container.create_recipe.execute(
        user_id=user.id,
        **data
    )

    recipe = container.get_recipe.execute(recipe_id, user.id)
    return recipe_to_response(recipe)

# ─── PUT Обновить рецепт ─────────────────────────────────────────

@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    body: RecipeUpdate,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    """Обновить поля рецепта."""
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

# ─── DELETE Удалить рецепт ──────────────────────────────────────

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> None:
    """Удалить рецепт."""
    container.delete_recipe.execute(RecipeId(recipe_id), user.id)
```

### Маршрутизатор аутентификации

**Файл:** `backend/api/routers/auth.py`

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
    """Регистрация нового пользователя."""
    user_id = container.register_user.execute(
        email=body.email,
        password=body.password,
        nickname=body.nickname,
    )

    # Автоматический вход после регистрации
    login_resp = container.login_user.execute(body.email, body.password)
    return login_resp

@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    container: ApplicationContainer = Depends(get_container),
) -> TokenResponse:
    """Вход пользователя и возврат токенов."""
    return container.login_user.execute(body.email, body.password)

@router.post("/refresh", response_model=str)
def refresh(
    refresh_token: str,
    container: ApplicationContainer = Depends(get_container),
) -> str:
    """Обновить токен доступа используя refresh token."""
    return container.refresh_access_token.execute(refresh_token)

@router.get("/me", response_model=UserResponse)
def get_me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """Получить профиль текущего пользователя."""
    return UserResponse(
        id=int(user.id),
        email=user.email,
        nickname=user.nickname,
    )
```

### Другие маршрутизаторы

- `products.py` — CRUD продукты (аналогично рецептам)
- `menus.py` — Создание, загрузка, управление слотами меню
- `family.py` — CRUD члены семьи
- `categories.py` — CRUD категории продукты и рецепты
- `shopping_list.py` — Генерация и экспорт списков покупок
- `import_export.py` — Импорт/экспорт рецептов и продуктов
- `system.py` — Проверка здоровья, информация о версии

---

## Ответы об ошибках

Все ошибки следуют этому формату JSON:

```json
{
  "detail": "Понятное для человека сообщение об ошибке"
}
```

Или для ошибок валидации:

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

**HTTP коды состояния:**

| Код | Исключение | Случай использования |
|------|-----------|----------|
| 201 | — | Ресурс создан (POST) |
| 204 | — | Успешно удалено (DELETE) |
| 400 | `AppError` | Общая ошибка приложения |
| 401 | `AuthenticationError` | Неверный токен или учетные данные |
| 404 | `EntityNotFoundError` | Ресурс не найден |
| 409 | `UserAlreadyExistsError` | Конфликт (email уже зарегистрирован) |
| 422 | `DomainError`, `CircularDependencyError` | Нарушение бизнес-правила |
| 500 | `RepositoryError` | Ошибка базы данных |

---

## Тестирование API

**Паттерн:** Использование TestClient из `fastapi.testclient`.

```python
# tests/unit/api/test_recipes.py

from fastapi.testclient import TestClient
from backend.api.main import app
from unittest.mock import Mock, patch

def test_list_recipes():
    """Тест GET /api/recipes"""
    client = TestClient(app)

    # Мок аутентификации
    with patch("backend.api.auth.get_current_user") as mock_auth:
        mock_auth.return_value = User(
            id=UserId(1),
            email="user@example.com",
            nickname="User",
            password_hash="...",
            created_at=datetime.utcnow(),
        )

        # Мок контейнера
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
    """Тест POST /api/recipes"""
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
    """Тест что эндпоинты требуют аутентификацию"""
    client = TestClient(app)

    response = client.get("/api/recipes")

    assert response.status_code == 401
    assert "Требуется авторизация" in response.json()["detail"]
```

---

## Резюме

Слой API:
- **Принимает** HTTP запросы и валидирует с Pydantic
- **Извлекает** текущего пользователя через JWT middleware
- **Вызывает** use case через ApplicationContainer
- **Преобразует** доменные сущности в схемы ответов
- **Возвращает** JSON с соответствующими кодами состояния
- **Обрабатывает** ошибки через обработчики исключений

Ключевые принципы:
- Stateless (без хранилища сессий)
- Type-safe (валидация Pydantic)
- Testable (через моки)
- Clear error messages (для фронтенда)

Все эндпоинты документированы в Swagger UI по адресу `/docs`.

---

**Далее:** См. [frontend.md](07-frontend.md) для архитектуры Vue 3 фронтенда.
