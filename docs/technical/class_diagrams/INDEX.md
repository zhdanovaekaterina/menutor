# Menu Planner Backend Class Diagrams — Index

Complete set of Mermaid class diagrams for all four architectural layers of the Menu Planner backend application.

## Quick Navigation

### By Layer

#### 1. Domain Layer (Business Logic & Data)
- [domain_overview.md](domain_overview.md) — Entities, value objects, repositories, domain services
- [domain_detailed.md](domain_detailed.md) — Full domain with all fields, methods, and invariants

**Contents**: 10 entities, 6 value objects, 8 repository interfaces, 7 domain services

#### 2. Application Layer (Use Cases)
- [application_overview.md](application_overview.md) — Use case classes, CRUD templates, DTOs
- [application_detailed.md](application_detailed.md) — Full use cases with all signatures and dependencies

**Contents**: 6 CRUD base classes, 25+ use cases, 13+ DTOs, pagination

#### 3. Infrastructure Layer (Data Access & Services)
- [infrastructure_overview.md](infrastructure_overview.md) — ORM models, repositories, auth, export/import
- [infrastructure_detailed.md](infrastructure_detailed.md) — Full infrastructure with all model fields and methods

**Contents**: 16 ORM models, 11 repository implementations, 2 auth services, 14 exporters/importers

#### 4. API Layer (HTTP Interface)
- [api_overview.md](api_overview.md) — FastAPI app, routers, dependency injection
- [api_detailed.md](api_detailed.md) — Full API with all endpoints, schemas, converters

**Contents**: 1 FastAPI app, 9 routers, ~50 endpoints, 20+ Pydantic schemas, 17+ converters

---

## Entity Catalog

### Core Entities (Domain Layer)

| Entity | Purpose | Relationships |
|--------|---------|---------------|
| **User** | User account | owns Recipes, Products, Menus, FamilyMembers, Preferences, MealTypes |
| **Recipe** | Dish with ingredients | belongs to RecipeCategory; has RecipeIngredients (products or sub-recipes) and CookingSteps |
| **Product** | Purchasable item | belongs to ProductCategory; used in RecipeIngredients; in MenuSlots |
| **FamilyMember** | Family member profile | has Preferences; referenced in MenuSlots (member_ids) |
| **WeeklyMenu** | 7-day meal plan | contains MenuSlots (grid: day × meal_type) |
| **MenuSlot** | Single meal cell | references Recipe or Product; has MealType; has member_ids |
| **ShoppingList** | Ephemeral list | aggregated from Menu; temporary (not saved) |
| **SavedShoppingList** | Persistent list | saved version of ShoppingList; linked to Menu |
| **RefreshToken** | JWT refresh token | belongs to User; has expiration and revocation flag |
| **Preference** | Dietary/lifestyle pref | assigned to FamilyMembers; types: ALLERGY, CATEGORY_BASED |
| **MealType** | Meal type | system (Breakfast, Lunch, Dinner) or custom; max 10 custom per user |

### Value Objects (Domain Layer)

| Value Object | Purpose | Immutable |
|--------------|---------|-----------|
| **Quantity** | Amount + unit | Yes (frozen) |
| **Money** | Amount + currency | Yes (frozen) |
| **RecipeIngredient** | Reference to product or sub-recipe | Yes (frozen) |
| **CookingStep** | Order + description | Yes (frozen) |
| **Category** | ID, name, active flag, color | Yes (NamedTuple) |
| **ActiveCategory** | ID, name, color (active only) | Yes (NamedTuple) |
| **ImportResult** | Created + updated counts + errors | Yes (frozen) |

---

## Use Case Catalog

### Authentication (7 use cases)
1. **RegisterUser** — Create account, default family member, system meal types
2. **LoginUser** — Validate credentials, issue access+refresh token pair
3. **RefreshAccessToken** — Validate refresh token, rotate tokens
4. **GetCurrentUser** — Extract user from access token
5. **ChangePassword** — Update password
6. **UpdateProfile** — Update nickname and/or password
7. **LogoutUser** — Revoke refresh token

### Recipe Management (6 use cases)
1. **CreateRecipe** — Create with validation (duplicate name, sub-recipes, cycles, depth)
2. **EditRecipe** — Edit with same validations
3. **GetRecipe** — Retrieve with ownership check
4. **DeleteRecipe** — Bulk delete
5. **ListRecipes** — With optional category filter
6. **PaginatedListRecipes** — With search + pagination

### Product Management (6 use cases)
1-6. Same pattern as recipes

### Menu Planning (8 use cases)
1. **CreateMenu** — Create weekly menu
2. **SaveMenu** — Persist menu state
3. **LoadMenu** — Retrieve with ownership check
4. **DeleteMenu** — Delete
5. **ListMenus** — List user's menus
6. **AddDishToSlot** — Upsert (with auto-position)
7. **MoveSlotInMenu** — Atomic move with position shifting
8. **RemoveItemFromSlot** — Delete slot item

### Shopping Lists (5 use cases)
1. **GenerateShoppingList** — Full aggregation from menu
2. **GenerateFilteredShoppingList** — Subset of slots
3. **GenerateAndSaveShoppingList** — Generate + persist
4. **ManageSavedShoppingList** — CRUD saved lists
5. **ExportShoppingList** — Serialize to CSV/JSON/PDF

### Recipe Analysis (4 use cases)
1. **FlattenRecipeProducts** — Recursively resolve all products
2. **PreviewFlattenedProducts** — Frontend preview
3. **ValidateSubRecipe** — Validate references (cycles, depth)
4. **GenerateMealSummary** — Create ingredient tree

### Family Management (6 use cases)
1. **CreateFamilyMember** — Create family member
2. **EditFamilyMember** — Edit
3. **DeleteFamilyMember** — Delete
4. **ListFamilyMembers** — List
5. **AssignPreferences** — Update FamilyMember.preference_ids
6. (CRUD via base classes)

### Preference Management (5 use cases)
1. **CreatePreference** — Create dietary/lifestyle preference
2. **UpdatePreference** — Update
3. **DeletePreference** — Delete (remove from all members)
4. **ListPreferences** — List user's preferences
5. **MatchRecipePreferences** — Return matching preferences for recipe

### Meal Type Management (6 use cases)
1. **ListMealTypes** — Sorted by (time, sort_order, id)
2. **CreateMealType** — Validate name, check custom limit (max 10)
3. **UpdateMealType** — Update with duplicate name check
4. **DeleteMealType** — Prevent system type deletion
5. **CheckMealTypeUsage** — Return menus using this type
6. **CreateSystemMealTypes** — Auto-create 3 system types on user signup

### Category Management (1 unified use case)
1. **ManageCategory** — Recipe + product category CRUD + move/delete

### Import/Export (4 use cases)
1. **ExportRecipes** — Serialize to format
2. **ExportProducts** — Serialize to format
3. **ImportRecipes** — Deserialize + upsert
4. **ImportProducts** — Deserialize + upsert

---

## API Endpoints by Router

### /auth (7 endpoints)
```
POST   /register          → UserResponse
POST   /login             → TokenResponse
POST   /refresh           → TokenResponse
GET    /me                → UserResponse
POST   /change-password   → None
POST   /update-profile    → UserResponse
POST   /logout            → None
```

### /recipes (11 endpoints)
```
GET    [?page, ?search, ?category_id]     → PaginatedResponse[RecipeResponse]
GET    /categories                         → list[ActiveCategoryResponse]
POST   /validate-sub-recipe                → ValidateSubRecipeResponse
GET    /{id}                               → RecipeResponse
POST   /                                   → RecipeResponse
PUT    /{id}                               → RecipeResponse
DELETE /{id}                               → None
GET    /{id}/flatten                       → dict[int, QuantitySchema]
GET    /{id}/meal-summary[?scale_factor]  → MealSummaryResponseSchema
GET    /{id}/matching-preferences         → list[PreferenceResponse]
POST   /preview-flattened                 → PreviewResponse
```

### /products (6 endpoints)
```
GET    [?page, ?search, ?category_id]    → PaginatedResponse[ProductResponse]
GET    /categories                        → list[ActiveCategoryResponse]
GET    /{id}                              → ProductResponse
POST   /                                  → ProductResponse
PUT    /{id}                              → ProductResponse
DELETE /{id}                              → None
```

### /menus (8 endpoints)
```
GET    /                      → list[MenuResponse]
POST   /                      → MenuResponse
GET    /{id}                  → MenuResponse
PUT    /{id}                  → MenuResponse
DELETE /{id}                  → None
POST   /{id}/slots/add        → MenuResponse
POST   /{id}/slots/move       → MenuResponse
POST   /{id}/slots/remove     → MenuResponse
```

### /shopping-list (8 endpoints)
```
GET    /from-menu/{menu_id}[?exclude_sub_recipes]  → ShoppingListResponse
POST   /generate-and-save                          → SavedShoppingListResponse
GET    /saved                                       → list[SavedShoppingListMetaResponse]
GET    /saved/{id}                                  → SavedShoppingListResponse
DELETE /saved/{id}                                  → None
GET    /saved/{id}/export[?format]                 → FileResponse
POST   /saved/{id}/items                           → SavedShoppingListItemSchema
PUT    /saved/{id}/items/{item_id}                 → SavedShoppingListItemSchema
```

### /family (6 endpoints)
```
GET    /              → list[FamilyMemberResponse]
POST   /              → FamilyMemberResponse
GET    /{id}          → FamilyMemberResponse
PUT    /{id}          → FamilyMemberResponse
DELETE /{id}          → None
POST   /{id}/preferences  → FamilyMemberResponse
```

### /preferences (5 endpoints)
```
GET    /        → list[PreferenceResponse]
POST   /        → PreferenceResponse
GET    /{id}    → PreferenceResponse
PUT    /{id}    → PreferenceResponse
DELETE /{id}    → None
```

### /categories (10 endpoints)
```
GET    /recipe/active       → list[ActiveCategoryResponse]
GET    /recipe              → list[CategoryResponse]
POST   /recipe              → int
PUT    /recipe/{id}         → int
DELETE /recipe/{id}         → None
GET    /product/active      → list[ActiveCategoryResponse]
GET    /product             → list[CategoryResponse]
POST   /product             → int
PUT    /product/{id}        → int
DELETE /product/{id}        → None
```

### /meal-types (6 endpoints)
```
GET    /           → list[MealTypeResponse]
POST   /           → MealTypeResponse
GET    /{id}       → MealTypeResponse
PUT    /{id}       → MealTypeResponse
DELETE /{id}       → None
GET    /{id}/usage → list[MealTypeUsageResponse]
```

### /import-export (4 endpoints)
```
GET    /recipes/export     → FileResponse
POST   /recipes/import     → ImportResult
GET    /products/export    → FileResponse
POST   /products/import    → ImportResult
```

### /system (2 endpoints)
```
GET    /units  → list[UnitResponse]
GET    /info   → SystemInfoResponse
```

---

## Data Flow Example: Create Recipe

```
Client (curl/HTTP)
  ↓
FastAPI Router (POST /recipes)
  ↓ (Depends: get_container, get_current_user)
CreateRecipe Use Case
  ├─ Check duplicate name (RecipeRepository.find_by_name)
  ├─ Validate sub-recipes (RecipeDependencyValidator)
  └─ Save (RecipeRepository.save)
    ↓
OrmRecipeRepository
  ├─ Convert domain Recipe → ORM RecipeRow
  ├─ Save related rows (ingredients, steps)
  └─ Commit transaction
    ↓
Database (PostgreSQL/SQLite)
  └─ INSERT INTO recipes, recipe_ingredients, cooking_steps
    ↓
OrmRecipeRepository (reload)
  ├─ Query saved row
  ├─ Convert ORM RecipeRow → domain Recipe
  └─ Return Recipe
    ↓
Router
  ├─ Convert domain Recipe → RecipeResponse schema
  └─ Return JSON
    ↓
Client
  └─ Receives 200 OK with RecipeResponse
```

---

## Diagram Statistics

| Layer | Classes | Methods | Relationships | Lines of Code |
|-------|---------|---------|---------------|---------------|
| **Domain** | 26 | 70+ | 35+ | ~2000 |
| **Application** | 30+ | 100+ | 50+ | ~2500 |
| **Infrastructure** | 27 | 150+ | 60+ | ~4000 |
| **API** | 9 routers + 20 schemas | 50+ endpoints | 40+ | ~2500 |
| **Total** | 110+ | 350+ | 185+ | ~11000 |

---

## How to Use These Diagrams

### For Understanding Architecture
1. Start with README.md overview
2. Read domain_overview.md to understand entities and relationships
3. Read application_overview.md to see use cases
4. Read infrastructure_overview.md to see persistence
5. Read api_overview.md to see HTTP interface

### For Implementation
1. Reference domain_detailed.md for entity definitions
2. Reference application_detailed.md for use case signatures
3. Reference infrastructure_detailed.md for repository patterns
4. Reference api_detailed.md for endpoint specifications

### For Documentation
1. Use overview diagrams in architecture documentation
2. Use detailed diagrams in technical specifications
3. Reference specific diagram sections in code comments
4. Link to diagrams in pull request descriptions

### For Onboarding
1. Have new developers read README.md
2. Have them trace through a feature using the diagrams
3. Have them implement a simple feature and verify against diagrams
4. Have them create their own "mini diagrams" for understanding

---

## Related Documentation

- [README.md](README.md) — Comprehensive architecture guide
- `/docs/technical/` — Version-specific technical documentation
- `/docs/user_guide.md` — User-facing documentation (Russian)
- `/docs/WEB_UI_LAYOUTS.md` — Frontend layout specifications
- `/CLAUDE.md` — Project conventions and instructions
- `/docs/changelog.md` — Version history

---

## Maintenance

These diagrams are **manually maintained**. To update:

1. Read the relevant source code in `backend/{layer}/`
2. Update the corresponding diagram file (overview or detailed)
3. Verify the diagram still renders correctly in GitHub/GitLab
4. Link any related documentation
5. Commit with message: `docs: update {layer} class diagrams`

For large refactors, update diagrams as part of the PR to help reviewers understand changes.

---

## Version History

- **2026-04-03** — Created complete set of 8 diagrams covering all 4 layers
  - Domain: 10 entities, 6 VOs, 8 repos, 7 services
  - Application: 6 CRUD bases, 25+ use cases, 13+ DTOs
  - Infrastructure: 16 ORM models, 11 repos, 14 exporters/importers
  - API: 1 app, 9 routers, ~50 endpoints, 20+ schemas

---

**Last Updated**: 2026-04-03  
**Diagrams Created**: 8 (2 per layer)  
**Total Classes**: 110+  
**Total Methods**: 350+  
**Relationships**: 185+
