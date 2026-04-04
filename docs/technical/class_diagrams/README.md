# Backend Class Diagrams

This directory contains comprehensive Mermaid class diagrams for all four layers of the Menu Planner backend, organized by architecture layer.

## Files

### Domain Layer
- **domain_overview.md** — High-level domain entities, value objects, ports, and domain services (10 entities, 6 value objects, 8 repositories, 2 protocols, 7 services)
- **domain_detailed.md** — Complete domain layer with all fields, methods, relationships, and invariants

### Application Layer
- **application_overview.md** — Use case structure: 6 CRUD base classes, 25+ use cases (auth, recipes, products, menus, shopping, etc.), 13+ DTOs
- **application_detailed.md** — Detailed use case breakdown with all method signatures, dependencies, and business logic

### Infrastructure Layer
- **infrastructure_overview.md** — ORM models, repositories, authentication implementations, export/import registries
- **infrastructure_detailed.md** — Complete infrastructure: 16 ORM models, BaseOrmRepository pattern, 11 repository implementations, 9 exporters, 5 importers

### API Layer
- **api_overview.md** — FastAPI app, 9 routers (~50 endpoints), Pydantic schemas, dependency injection
- **api_detailed.md** — Complete API: all routers, endpoints, request/response schemas, converters, authentication flow

## Architecture Overview

The backend follows **Clean Architecture** with four layers:

```
Vue Frontend (TypeScript + Pinia)
           ↓
     FastAPI API Layer (backend/api/)
     ↓              ↓              ↓
  Routers      Schemas      Converters
     ↓
Application Layer (backend/application/)
     ↓
  Use Cases (one class = one operation)
     ↓
Domain Layer (backend/domain/)
     ↓        ↓         ↓
 Entities  Services  Ports/ABCs
     ↓
Infrastructure Layer (backend/infrastructure/)
     ↓          ↓           ↓
 ORM Repos  Auth Impl  Export/Import
     ↓
Database (PostgreSQL / SQLite)
```

## Key Design Patterns

### Domain Layer
- **Entities**: Dataclasses with invariant validation in `__post_init__`
- **Value Objects**: Frozen dataclasses (Money, Quantity, RecipeIngredient, etc.)
- **Ports**: Abstract interfaces (UserRepository, RecipeRepository, etc.)
- **Domain Services**: Business logic (RecipeDependencyValidator, PreferenceMatcher, ShoppingListBuilder)
- **Dependency Validation**: Cycle detection, depth limits, ownership checks

### Application Layer
- **CRUD Base Classes**: Generic templates (CreateEntity, EditEntity, DeleteEntity, etc.) reduce boilerplate 8x
- **Use Cases**: One class per operation with single `execute()` method
- **DTOs**: Data transfer objects bridge API schemas and domain entities
- **Ownership Checks**: Every query filtered by user_id to prevent cross-user data access

### Infrastructure Layer
- **BaseOrmRepository[E, I]**: Generic base class for 11 repositories (saves ~500 lines of boilerplate)
- **Registry Pattern**: Exporters/importers self-register by (entity_type, format)
- **Multi-Database Support**: SQLite (dev/test) and PostgreSQL (prod) with dialect detection
- **Cascade Deletes**: Foreign keys ensure referential integrity
- **JSON Columns**: Preference/member IDs stored as JSON strings for flexibility

### API Layer
- **Dependency Injection**: FastAPI Depends() for container, authentication, repositories
- **Bearer Token Auth**: JWT access tokens (30min) with refresh rotation (30 days)
- **Exception Handlers**: Domain errors mapped to HTTP status codes
- **Converter Functions**: Decouple domain entities from API schemas
- **Paginated Responses**: PAGE_SIZE=25 with offset-based pagination

## Entity Relationships

### Core Domain Model
```
User (1) ──→ (N) FamilyMember ──→ (N) Preference
 ↓
(N) Recipe ──→ (N) RecipeIngredient ──→ (1) Product
                                        ↓
(N) WeeklyMenu ──→ (N) MenuSlot ──→ (1) MealType
                      ├─→ (1) Recipe
                      ├─→ (1) Product
                      └─→ (N) FamilyMember (via member_ids JSON)
↓
(N) SavedShoppingList ──→ (N) SavedShoppingListItem
                           ├─→ (1) Product
                           └─→ Money + Quantity
```

### Categories
```
Recipe ──→ RecipeCategory
Product ──→ ProductCategory
```

### Meal Types
```
MenuSlot ──→ MealType
             └─→ System vs Custom (per-user creation limit: 10 custom)
```

### Preferences
```
FamilyMember ──→ (N) Preference
                 ├─→ Type: ALLERGY | CATEGORY_BASED
                 ├─→ Mode: BLOCKED | ALLOWED
                 └─→ References: Products, ProductCategories, RecipeCategories
```

## Key Statistics

### Domain Layer
- **Entities**: 10 (User, Recipe, Product, FamilyMember, WeeklyMenu, MenuSlot, ShoppingList, SavedShoppingList, RefreshToken, Preference, MealType)
- **Value Objects**: 6 (Quantity, Money, RecipeIngredient, CookingStep, Category variants, ImportResult)
- **Repositories**: 8 (User, Recipe, Product, Menu, FamilyMember, Category, RefreshToken, SavedShoppingList, Preference, MealType)
- **Domain Services**: 7 (PasswordHasher, TokenService, PortionCalculator, UnitConverter, RecipeDependencyValidator, ShoppingListBuilder, PreferenceMatcher)

### Application Layer
- **CRUD Base Classes**: 6 (CreateEntity, EditEntity, DeleteEntity, GetEntity, ListEntities, PaginatedListEntities)
- **Use Cases**: 25+ across 8 domains
  - Auth: 7 (register, login, refresh, get_current, change_password, update_profile, logout)
  - Recipes: 6 (create, edit, get, delete, list, paginated)
  - Products: 6 (create, edit, get, delete, list, paginated)
  - Menus: 8 (create, save, load, delete, list, add_dish, move_slot, remove_item)
  - Shopping: 5 (generate, filtered, generate_and_save, manage saved lists, export)
  - Recipe Analysis: 4 (flatten, preview, validate, meal_summary)
  - Family: 6 (create, edit, delete, list, assign_preferences)
  - Preferences: 5 (create, update, delete, list, match_recipe)
  - Meal Types: 6 (list, create, update, delete, check_usage, create_system)
  - Categories: 1 (manage recipe + product categories)
  - Import/Export: 2 (export, import)
- **DTOs**: 13+ (RegisterData, LoginData, TokenPair, RecipeData, ProductData, etc.)

### Infrastructure Layer
- **ORM Models**: 16 (User, RefreshToken, Unit, RecipeCategory, ProductCategory, Product, Recipe, RecipeIngredient, CookingStep, FamilyMember, Menu, MenuSlot, SavedShoppingList, SavedShoppingListItem, Preference, MealType)
- **Repositories**: 11 (User, Recipe, Product, Menu, FamilyMember, RecipeCategory, ProductCategory, RefreshToken, SavedShoppingList, Preference, MealType)
- **Auth Implementations**: 2 (BcryptPasswordHasher, JwtTokenService)
- **Exporters**: 9 (ShoppingList CSV/JSON/PDF, Recipe CSV/JSON, Product CSV/JSON, Menu JSON/PDF)
- **Importers**: 5 (Recipe CSV/JSON, Product CSV/JSON, Menu JSON)

### API Layer
- **Routers**: 9 (auth, recipes, products, menus, shopping_list, family, preferences, categories, meal_types, import_export, system)
- **Endpoints**: ~50 (across all routers)
- **Pydantic Schemas**: 20+ (request/response DTOs with validation)
- **Converters**: 17+ (entity ↔ schema mappings)

## How to Read the Diagrams

### Overview Diagrams
- Show main classes and key relationships only
- Ideal for understanding architecture at a glance
- Best for presentations and documentation

### Detailed Diagrams
- Include all fields, methods, parameters, and return types
- Show all relationships (inheritance, composition, aggregation, dependency)
- Ideal for implementation reference and onboarding

## Usage in Development

1. **Understanding Architecture**: Start with overview diagrams to grasp layer responsibilities
2. **Implementing Features**: Reference detailed diagrams for exact signatures and relationships
3. **Debugging**: Trace data flow through layers using the diagrams
4. **Code Review**: Verify new code against diagram patterns
5. **Onboarding**: Use diagrams to teach new team members the codebase structure

## Notes

- All diagrams are automatically regenerated from source code via Mermaid
- Mermaid syntax: uses classDiagram type with proper relationships:
  - `--|>` = inheritance
  - `*--` = composition
  - `o--` = aggregation
  - `-->` = association
  - `..|>` = interface implementation
  - `..>` = dependency
- Diagrams support zooming and exporting to PNG/SVG in GitHub/GitLab interfaces
- Include these diagrams in architecture documentation, tech specs, and onboarding materials

## Related Documentation

- `/docs/WEB_UI_LAYOUTS.md` — Frontend (Vue 3) layout structure
- `/docs/AUTH_IMPLEMENTATION_PLAN.md` — Detailed auth implementation
- `/docs/user_guide.md` — User-facing documentation (Russian)
- `/docs/technical/` — Technical architecture docs for each version
- `/CLAUDE.md` — Project instructions and conventions
