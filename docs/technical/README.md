# Menu Planner — Technical Documentation

Complete technical documentation for Menu Planner developers and AI agents working with the codebase.

## Documentation Files

### 1. [Overview](01-overview.md)
Quick start guide, tech stack table, project structure, environment setup, running the app.

**Read this first** for a 5-minute orientation.

### 2. [Architecture](02-architecture.md)
Clean Architecture design (4 layers + API + frontend), dependency inversion principle, design patterns, testing pyramid.

**Foundation** for understanding the entire codebase.

### 3. [Domain Layer](03-backend-domain.md)
Entities (Recipe, Product, Menu, User), value objects (Quantity, Money), domain services, ports, typed IDs, exceptions.

**Business logic layer** — zero framework dependencies.

### 4. [Application Layer](04-backend-application.md)
Use case pattern, all ~20 use cases (auth, recipe CRUD, menu planning, shopping list generation, import/export), input/output DTOs, error handling.

**Orchestration layer** — connects domain and infrastructure.

### 5. [Infrastructure Layer](05-backend-infrastructure.md)
SQLAlchemy ORM models, repository implementations, bcrypt password hashing, JWT token service, Alembic migrations, exporters, multi-DB support.

**Persistence and auth layer** — framework-specific code.

### 6. [API Layer](06-backend-api.md)
FastAPI app setup, authentication middleware (Bearer token extraction), Pydantic schemas, converters (domain ↔ schema), all 8 routers, error responses, testing patterns.

**HTTP adapter layer** — translates requests to domain operations.

### 7. [Frontend](07-frontend.md)
Vue 3 + TypeScript architecture, Pinia stores (auth, recipes, products, menus, family, categories, shopping list), Vue Router, Tailwind CSS v4, composables, components, axios API client with JWT interceptor.

**Single-page application** — Vue 3 SPA.

### 8. [Testing](08-testing.md)
Testing pyramid, unit tests (domain + application), integration tests (repositories), API tests, fixtures, pytest configuration, running tests, coverage goals.

**490+ tests pass** — test fixtures included.

### 9. [Database](09-database.md)
Complete SQL schema, all tables with columns and constraints, Alembic migrations (create, apply, rollback), seed data, SQLite vs PostgreSQL, indexes, backup/recovery.

**Data persistence** — schema reference.

---

## Quick Navigation

### By Role

**Onboarding Developer:**
1. [Overview](01-overview.md) — 5 min
2. [Architecture](02-architecture.md) — 15 min
3. [Backend API](06-backend-api.md) — 10 min
4. [Testing](08-testing.md) — 10 min

Total: ~40 minutes to understand the full stack.

**Backend Engineer:**
1. [Architecture](02-architecture.md)
2. [Domain Layer](03-backend-domain.md)
3. [Application Layer](04-backend-application.md)
4. [Infrastructure Layer](05-backend-infrastructure.md)
5. [API Layer](06-backend-api.md)
6. [Testing](08-testing.md)
7. [Database](09-database.md)

**Frontend Engineer:**
1. [Overview](01-overview.md)
2. [Architecture](02-architecture.md)
3. [Frontend](07-frontend.md)
4. [API Layer](06-backend-api.md) — understand endpoints
5. [Testing](08-testing.md)

**DevOps / Database:**
1. [Overview](01-overview.md)
2. [Infrastructure Layer](05-backend-infrastructure.md)
3. [Database](09-database.md)

**AI Agent / Code Analyzer:**
1. [Architecture](02-architecture.md) — understand structure
2. [Domain Layer](03-backend-domain.md) — business rules
3. [Application Layer](04-backend-application.md) — use cases
4. [API Layer](06-backend-api.md) — endpoints
5. [Database](09-database.md) — schema

### By Topic

**Understand the Architecture:**
- [Architecture](02-architecture.md) — layers, dependency inversion, patterns
- [Domain Layer](03-backend-domain.md) — entities, value objects, business logic

**Add a New Feature:**
1. Define domain entity in [Domain Layer](03-backend-domain.md)
2. Create use case in [Application Layer](04-backend-application.md)
3. Implement repository in [Infrastructure Layer](05-backend-infrastructure.md)
4. Add API router in [API Layer](06-backend-api.md)
5. Create Vue component in [Frontend](07-frontend.md)
6. Write tests in [Testing](08-testing.md)
7. Add migrations in [Database](09-database.md)

**Debug a Bug:**
1. Check [API Layer](06-backend-api.md) if HTTP error
2. Check [Application Layer](04-backend-application.md) if logic error
3. Check [Domain Layer](03-backend-domain.md) if business rule violation
4. Check [Testing](08-testing.md) for similar test cases

**Understand Database Queries:**
- [Database](09-database.md) — schema and indexes
- [Infrastructure Layer](05-backend-infrastructure.md) — repository queries

**Set Up Local Development:**
- [Overview](01-overview.md) — quick start
- [Database](09-database.md) — Alembic migrations

---

## Key Concepts

### Clean Architecture

```
Frontend (Vue 3) → API (FastAPI) → Application → Domain ← Infrastructure
                                      ↑                      │
                                      └──────────────────────┘
                                   (implements ports)
```

- **Domain:** Business logic (zero framework code)
- **Application:** Orchestration (use cases)
- **Infrastructure:** Persistence (repositories, auth)
- **API:** HTTP adapter (routers, schemas)
- **Frontend:** Vue 3 SPA (components, stores)

### Key Patterns

| Pattern | Purpose | Location |
|---------|---------|----------|
| **Clean Architecture** | Decoupled layers | All |
| **Repository** | Abstract data access | Infrastructure |
| **Use Case** | One operation = one class | Application |
| **Value Object** | Immutable, no identity | Domain (Quantity, Money) |
| **Domain Service** | Complex logic | Domain (ShoppingListBuilder) |
| **Dependency Injection** | Explicit wiring | Composition Root |
| **Converter** | Domain ↔ Schema mapping | API |
| **Strategy** | Interchangeable algorithms | Exporters |
| **Pinia Store** | Centralized state | Frontend |

### Typed IDs

```python
RecipeId = NewType("RecipeId", int)  # Prevents ID mix-ups
ProductId = NewType("ProductId", int)
```

Caught by mypy at compile time. No runtime cost.

### Quantity Value Object

Central to shopping list logic:

```python
flour = Quantity(200, "g")
milk = Quantity(0.5, "l")

# Auto-converts units, sums
flour_total = flour + Quantity(0.3, "kg")  # 500g + 300g = 800g
```

### Multi-Tenancy

All data scoped by `user_id`:

```python
recipes = recipe_repo.list_by_user(UserId(1))  # Only user 1's recipes
```

---

## Common Tasks

### Add a New Recipe Field

1. **Domain:** Add field to `Recipe` entity in [Domain Layer](03-backend-domain.md#recipe)
2. **Database:** Add column via Alembic migration in [Database](09-database.md#creating-migrations)
3. **Infrastructure:** Update `RecipeRow` ORM model and repository mapper
4. **API:** Update `RecipeResponse` schema and converter
5. **Frontend:** Update `Recipe` interface and form component
6. **Tests:** Add test case in [Testing](08-testing.md#unit-tests--domain--application)

### Create a New Use Case

1. **Define:** Create class in `backend/application/use_cases/` following [Application Layer](04-backend-application.md#use-case-pattern) pattern
2. **Implement:** Input validation → fetch domain objects → apply logic → persist → return result
3. **Test:** Write unit test with mocked repository
4. **Wire:** Add to composition root in `backend/composition/`
5. **API:** Create endpoint in appropriate router

### Debug a Failing Test

1. Run single test: `pytest tests/unit/domain/test_recipe.py::test_recipe_scale_to -v`
2. Check error message and assertion
3. Review test fixture setup
4. Verify domain entity or mock setup
5. See [Testing](08-testing.md) for patterns

### Query Database Directly

```bash
# SQLite
sqlite3 menutor.db

# PostgreSQL
psql -U user -h localhost menutor_db

# View schema
.schema recipes

# Check data
SELECT * FROM recipes WHERE user_id = 1;
```

---

## API Reference

### Endpoints (All Require Auth)

| Method | Path | Purpose |
|--------|------|---------|
| **POST** | `/api/auth/register` | Create user account |
| **POST** | `/api/auth/login` | Login, get tokens |
| **POST** | `/api/auth/refresh` | Refresh access token |
| **GET** | `/api/auth/me` | Get current user |
| **GET** | `/api/recipes` | List recipes |
| **POST** | `/api/recipes` | Create recipe |
| **GET** | `/api/recipes/{id}` | Get recipe |
| **PUT** | `/api/recipes/{id}` | Update recipe |
| **DELETE** | `/api/recipes/{id}` | Delete recipe |
| **GET** | `/api/products` | List products |
| **POST** | `/api/products` | Create product |
| **GET** | `/api/menus` | List menus |
| **POST** | `/api/menus` | Create menu |
| **POST** | `/api/menus/{id}/shopping-list` | Generate shopping list |
| **GET** | `/api/menus/{id}/shopping-list/export` | Export (CSV/JSON/text) |

Full documentation: `/docs` (Swagger UI)

---

## Environment Variables

```env
DATABASE_URL=sqlite:///./menutor.db          # SQLite dev / PostgreSQL prod
JWT_SECRET_KEY=your-secret-key-here          # Generate: openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

---

## Running the App

```bash
# Backend
uvicorn backend.api.main:app --reload
# API docs: http://localhost:8000/docs

# Frontend
cd frontend && npm run dev
# Frontend: http://localhost:5173

# Tests
pytest tests/ -v
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/add-recipe-notes

# Make changes, commit
git add .
git commit -m "feat: add notes field to recipes"

# Pre-commit checks run automatically
# mypy, isort, pytest

# Push and create PR
git push origin feature/add-recipe-notes
```

---

## Performance Considerations

1. **Database Indexes:** Strategic on `user_id`, names, foreign keys
2. **Caching:** Implement in Pinia stores on frontend
3. **API:** Pagination for large lists
4. **Quantity Arithmetic:** Immutable value object (safe to cache)
5. **Shopping List Generation:** Aggregate in domain service (testable, reusable)

---

## Security

1. **Passwords:** Hashed with bcrypt (never plaintext)
2. **JWT:** Signed tokens, 30-min expiry, refresh token rotation
3. **CORS:** Configured in FastAPI (allow all origins in dev, restrict in prod)
4. **SQL Injection:** SQLAlchemy ORM prevents parameterized queries
5. **Multi-tenancy:** All queries filtered by `user_id`

---

## Version History

- **v0.6.0** — Nested recipes, pieces-based recipes, comprehensive testing
- **v0.5.0** — Web migration (FastAPI + Vue 3), authentication
- **v0.4.0** — Shopping list generation, exporters
- **v0.3.0** — Menu planning, family member profiles
- **v0.2.0** — Recipes and products management
- **v0.1.0** — MVP: project structure, core domain

---

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Vue 3 Docs](https://vuejs.org/)
- [Pinia Docs](https://pinia.vuejs.org/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [pytest Docs](https://docs.pytest.org/)

---

## Contributing

1. Read [Architecture](02-architecture.md) to understand structure
2. Follow Clean Architecture principles
3. Write tests for new code (see [Testing](08-testing.md))
4. Update database schema via Alembic migrations
5. Update this documentation for major changes

---

**For detailed information on any topic, see the corresponding document above.**

---

Generated: 2026-03-20
Scope: Menu Planner MVP + Web Migration
Coverage: 9 comprehensive files, ~5000 lines of documentation
