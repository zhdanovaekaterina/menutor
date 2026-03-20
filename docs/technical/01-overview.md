# Menu Planner — Technical Overview

## Project Summary

**Menu Planner** (Menutor) is a family meal planning web application that helps families plan weekly menus, manage recipes and products, automatically generate shopping lists with cost tracking, and accommodate dietary preferences. The project is a full-stack application currently in active development.

**Status:** MVP with web migration complete (490+ unit tests passing)

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend Framework** | FastAPI | 0.100+ | HTTP API layer, request routing, dependency injection |
| **Python** | Python | 3.14 | Core runtime via venv at `.venv3-14/` |
| **Database** | PostgreSQL (prod) / SQLite (dev) | 15+ / 3.x | Persistent data storage |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction, model mapping |
| **Migrations** | Alembic | 1.12+ | Database schema versioning |
| **Password Hashing** | bcrypt | 4.0+ | Secure password storage |
| **JWT** | PyJWT | 2.8+ | Session token generation and validation |
| **HTTP Server** | uvicorn | 0.23+ | ASGI server for FastAPI |
| **Frontend Framework** | Vue 3 | 3.3+ | Reactive UI, component-based |
| **Frontend Language** | TypeScript | 5.0+ | Type-safe JavaScript for frontend |
| **State Management** | Pinia | 2.1+ | Centralized store (Vuex successor) |
| **Routing** | Vue Router | 4.2+ | Client-side SPA routing |
| **HTTP Client** | axios | 1.4+ | Frontend → backend API calls |
| **CSS Framework** | Tailwind CSS | 4.0+ | Utility-first styling |
| **Node.js** | Node.js | 24.x via nvm | JavaScript runtime, npm package manager |
| **Testing (Backend)** | pytest | 7.4+ | Unit and integration test framework |
| **Testing (Frontend)** | Vitest | 1.0+ | Vue component and TS unit tests |
| **Code Quality** | mypy, isort, pre-commit | Latest | Type checking, import sorting, git hooks |

## Quick Start

### Backend Setup

```bash
# Create and activate virtual environment
python3.14 -m venv .venv3-14
source .venv3-14/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start API server
uvicorn backend.api.main:app --reload
```

API runs at `http://localhost:8000/docs` (Swagger UI).

### Frontend Setup

```bash
# Ensure Node.js 24 is installed (via nvm)
nvm use 24

# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Run Tests

```bash
# Backend unit and integration tests
pytest tests/ -v

# Frontend component tests
cd frontend && npm run test

# Pre-commit checks (mypy, isort, pytest)
pre-commit run --all-files
```

## Project Structure

```
menu-planner/
├── backend/                            # Python backend (FastAPI + Clean Architecture)
│   ├── api/                            # HTTP layer: routers, schemas, auth
│   │   ├── main.py                     # FastAPI app, lifespan, exception handlers
│   │   ├── auth.py                     # JWT extraction (get_current_user dependency)
│   │   ├── deps.py                     # FastAPI dependency injection (get_container)
│   │   ├── converters.py               # Domain entity → Pydantic schema conversion
│   │   ├── routers/                    # 8 API routers (auth, recipes, products, menus, family, categories, shopping_list, import_export, system)
│   │   └── schemas/                    # Pydantic request/response models
│   ├── domain/                         # Core business logic (zero framework dependencies)
│   │   ├── entities/                   # Recipe, Product, Menu, ShoppingList, User, FamilyMember, RefreshToken
│   │   ├── value_objects/              # Quantity, Money, RecipeIngredient, CookingStep, Category
│   │   ├── services/                   # Domain services: ShoppingListBuilder, PortionCalculator, UnitConverter
│   │   ├── ports/                      # Abstract interfaces (repositories, services)
│   │   └── exceptions.py               # Custom domain exceptions
│   ├── application/                    # Use case orchestration layer
│   │   └── use_cases/                  # ~20 use case classes (1 class = 1 operation)
│   ├── infrastructure/                 # Implementation of domain ports
│   │   ├── repositories/               # SQLAlchemy-based ORM models and repository implementations
│   │   ├── auth/                       # BcryptPasswordHasher, JwtTokenService
│   │   ├── database/                   # SQLAlchemy engine, migrations (Alembic)
│   │   ├── export/                     # CSV/JSON exporters (Strategy pattern)
│   │   └── import_/                    # CSV/JSON importers
│   ├── composition/                    # Dependency injection container setup
│   │   ├── container.py                # ApplicationContainer orchestrator
│   │   ├── _auth.py, _recipes.py, etc. # Module-specific wiring
│   │   └── _infrastructure.py          # DB and auth service initialization
│   └── main.py                         # Entry point for desktop/CLI (if used)
│
├── frontend/                           # Vue 3 + TypeScript SPA
│   ├── src/
│   │   ├── main.ts                     # Vue app initialization
│   │   ├── App.vue                     # Root layout component (AppLayout + router-view)
│   │   ├── api/                        # HTTP client layer
│   │   │   ├── client.ts               # axios instance with interceptors (JWT, auto-refresh)
│   │   │   ├── auth.ts                 # Auth API calls (register, login, refresh)
│   │   │   └── types.ts                # TypeScript interfaces matching Pydantic schemas
│   │   ├── stores/                     # Pinia stores (reactive state)
│   │   │   ├── auth.ts                 # User, tokens, login/logout
│   │   │   ├── recipes.ts              # Recipe list, CRUD operations
│   │   │   ├── products.ts             # Product list, CRUD operations
│   │   │   ├── menus.ts                # Weekly menu state, slot management
│   │   │   ├── family.ts               # Family members, dietary restrictions
│   │   │   ├── categories.ts           # Product/recipe categories
│   │   │   ├── shoppingList.ts         # Shopping list state, cost tracking
│   │   │   ├── toast.ts                # Toast notification queue
│   │   │   └── crud-factory.ts         # Generic CRUD store factory
│   │   ├── router/                     # Vue Router configuration
│   │   │   └── index.ts                # 6 main routes + nested /settings children
│   │   ├── views/                      # Page-level components
│   │   │   ├── MenuPlannerView.vue     # 7-day × 3-meal grid planner
│   │   │   ├── ShoppingListView.vue    # Aggregated shopping list with cost tracking
│   │   │   ├── RecipeListView.vue      # Recipe CRUD table + form
│   │   │   ├── ProductListView.vue     # Product CRUD table + form
│   │   │   ├── SettingsView.vue        # Settings container (family, categories, about)
│   │   │   └── AuthView.vue            # Login/register page
│   │   ├── components/                 # Reusable components
│   │   │   ├── layout/                 # AppSidebar, MobileBottomNav
│   │   │   ├── planner/                # PlannerGrid, GridCell, SourcePanel, SavedMenuList
│   │   │   ├── shopping/               # ShoppingTable, ShoppingSummary, AddProductForm
│   │   │   ├── recipes/                # RecipeTable, RecipeForm
│   │   │   ├── products/               # ProductTable, ProductForm
│   │   │   ├── settings/               # FamilyPanel, CategoryPanel, AboutPanel
│   │   │   └── ui/                     # Reusable primitives (ConfirmDialog, InputDialog, ToastNotification, etc.)
│   │   ├── composables/                # Reusable composition functions
│   │   │   ├── useSelection.ts         # Multi-row selection logic
│   │   │   ├── useDropdown.ts          # Dropdown open/close state
│   │   │   ├── useCategoryFilter.ts    # Category filtering
│   │   │   ├── useContextMenu.ts       # Right-click context menu
│   │   │   └── useFileDownload.ts      # Download blob/CSV export
│   │   └── utils/                      # Utility functions
│   │       └── units.ts                # Unit conversion, label formatting
│   ├── public/                         # Static assets
│   └── vite.config.ts                  # Tailwind v4 plugin, API proxy to :8000
│
├── tests/                              # Comprehensive test suite
│   ├── unit/
│   │   ├── domain/                     # Domain logic tests (Quantity, Recipe, etc.)
│   │   ├── application/                # Use case tests
│   │   └── api/                        # Router endpoint tests
│   └── integration/
│       └── repositories/               # ORM repository tests against :memory: SQLite
│
├── alembic/                            # Database migrations (Alembic)
│   ├── env.py                          # Migration environment setup
│   └── versions/                       # Timestamped migration scripts
│
├── .config/
│   ├── .env                            # Environment variables (git-ignored)
│   └── git-hooks/
│       └── pre-commit                  # Runs pytest, isort, mypy before commit
│
├── docs/                               # User and technical documentation
│   ├── technical/                      # This directory (architecture, API, implementation guides)
│   └── ...                             # User guides, specifications (Russian)
│
├── requirements.txt                    # Python dependencies (backend + tests)
├── frontend/package.json               # Node dependencies (frontend)
├── pytest.ini                          # pytest configuration
├── pyproject.toml                      # Python project config (mypy, isort)
└── VERSION                             # API version string
```

## Environment Setup

### 1. Python Virtual Environment

```bash
python3.14 -m venv .venv3-14
source .venv3-14/bin/activate  # macOS/Linux
# or
.venv3-14\Scripts\activate     # Windows
```

### 2. Environment Variables

Create `.config/.env`:

```env
DATABASE_URL=sqlite:///./test.db     # Dev: SQLite; Prod: postgresql://user:pass@host/db
JWT_SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 3. Database Initialization

```bash
# Create/update schema
alembic upgrade head

# If migrations don't run automatically
python -c "from backend.infrastructure.database.seed_defaults import seed_defaults; seed_defaults()"
```

## Running the Application

### Development (FastAPI + Vue)

**Terminal 1 — Backend:**

```bash
source .venv3-14/bin/activate
uvicorn backend.api.main:app --reload
# Swagger API docs: http://localhost:8000/docs
# OpenAPI JSON: http://localhost:8000/openapi.json
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
# Frontend: http://localhost:5173
```

The frontend's `vite.config.ts` proxies API calls from `http://localhost:5173/api/*` to `http://localhost:8000/api/*`.

### Database Management

```bash
# Create migration (auto-detect changes)
alembic revision --autogenerate -m "Describe changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history
```

## Key Design Decisions

### 1. Clean Architecture (4 Layers + API Adapter)

- **Domain:** Business logic, zero framework dependencies
- **Application:** Use cases, orchestration, DTOs
- **Infrastructure:** Persistence, auth, file I/O
- **API:** FastAPI routers, Pydantic schemas, converters
- **Frontend:** Vue 3 SPA with Pinia stores

**Why:** Maximum testability, framework independence, clear separation of concerns.

### 2. Typed IDs via `NewType`

```python
RecipeId = NewType("RecipeId", int)
ProductId = NewType("ProductId", int)
```

Prevents accidental ID mix-ups (e.g., passing `ProductId` to a method expecting `RecipeId`). Enforced by mypy at compile time.

### 3. SQLAlchemy + Alembic

- **SQLAlchemy:** ORM layer between domain and database
- **Alembic:** Version-controlled migrations
- **Why:** Easy multi-database support (SQLite ↔ PostgreSQL), schema evolution safety, data integrity

### 4. Pinia for Frontend State

- Centralized, reactive state management
- Less boilerplate than Vuex
- Works seamlessly with Vue 3 Composition API

### 5. Tailwind CSS v4

- Utility-first, responsive design
- Zero CSS file management
- Built into Vite build pipeline

## Docker Setup (Optional)

For containerized deployment:

```yaml
# docker-compose.yml structure
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: menutor
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/menutor
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE: http://api:8000
```

## Health & Monitoring Endpoints

- `GET /api/system/health` — Health check (no auth required)
- `GET /api/system/version` — API version
- `GET /docs` — Swagger UI with all endpoints
- `GET /openapi.json` — OpenAPI/Swagger spec

## Common Development Tasks

| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -v --cov=backend` |
| Run tests matching pattern | `pytest tests/ -k "test_recipe" -v` |
| Format imports | `isort backend/ tests/` |
| Type check | `mypy backend/ tests/` |
| Pre-commit check | `pre-commit run --all-files` |
| Build frontend | `cd frontend && npm run build` |
| Serve frontend built assets | `cd frontend && npm run preview` |

---

**Next:** See [architecture.md](02-architecture.md) for detailed layer descriptions and design patterns.
