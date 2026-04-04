# API Layer — Overview Class Diagram

```mermaid
classDiagram
    %% === FASTAPI APP ===
    class FastAPIApp {
        <<fastapi>>
        +title: str
        +version: str
        +lifespan(app: FastAPI) AsyncIterator
        +middleware(http): rollback_on_error()
        +exception_handler(AuthenticationError)
        +exception_handler(UserAlreadyExistsError)
        +exception_handler(EntityNotFoundError)
        +exception_handler(CircularDependencyError)
        +exception_handler(MealTypeLimitError)
        +exception_handler(SystemMealTypeDeletionError)
        +exception_handler(DomainError)
        +exception_handler(RepositoryError)
    }

    %% === DEPENDENCY INJECTION ===
    class ApplicationContainer {
        <<composition_root>>
    }

    class GetContainer {
        +get_container(request: Request) ApplicationContainer
    }

    %% === AUTH DEPENDENCY ===
    class GetCurrentUser {
        +get_current_user(request: Request, container: ApplicationContainer) User
    }

    %% === ROUTERS (7 total) ===
    class AuthRouter {
        prefix: /auth
        POST /register(RegisterRequest) UserResponse
        POST /login(LoginRequest) TokenResponse
        POST /refresh() TokenResponse
        GET /me() UserResponse
        POST /change-password(ChangePasswordRequest) None
        POST /update-profile(UpdateProfileRequest) UserResponse
        POST /logout() None
    }

    class RecipesRouter {
        prefix: /recipes
        GET [?page, ?search, ?category_id] PaginatedResponse[RecipeResponse]
        GET /categories[] ActiveCategoryResponse
        POST /validate-sub-recipe(ValidateSubRecipeRequest) ValidateSubRecipeResponse
        GET /{id} RecipeResponse
        POST (RecipeCreate) RecipeResponse
        PUT /{id}(RecipeUpdate) RecipeResponse
        DELETE /{id} None
        GET /{id}/flatten(RecipeId) dict[int, QuantitySchema]
        GET /{id}/meal-summary(RecipeId, ?scale_factor) MealSummaryResponseSchema
        GET /{id}/matching-preferences(RecipeId) PreferenceMatchResponse
        POST /preview-flattened(FlattenedProductsPreviewRequest) PreviewResponse
    }

    class ProductsRouter {
        prefix: /products
        GET [?page, ?search, ?category_id] PaginatedResponse[ProductResponse]
        GET /categories[] ActiveCategoryResponse
        GET /{id} ProductResponse
        POST (ProductCreate) ProductResponse
        PUT /{id}(ProductUpdate) ProductResponse
        DELETE /{id} None
    }

    class MenusRouter {
        prefix: /menus
        GET [] MenuResponse
        POST (CreateMenuRequest) MenuResponse
        GET /{id} MenuResponse
        PUT /{id} (UpdateMenuRequest) MenuResponse
        DELETE /{id} None
        POST /{id}/slots/add(AddSlotRequest) MenuResponse
        POST /{id}/slots/move(MoveSlotRequest) MenuResponse
        POST /{id}/slots/remove(RemoveSlotRequest) MenuResponse
    }

    class ShoppingListRouter {
        prefix: /shopping-list
        GET /from-menu/{menu_id}(?exclude_sub_recipes) ShoppingListResponse
        POST /generate-and-save(GenerateAndSaveRequest) SavedShoppingListResponse
        GET /saved[] SavedShoppingListMetaResponse
        GET /saved/{id} SavedShoppingListResponse
        DELETE /saved/{id} None
        GET /saved/{id}/export(?format) file_response
        POST /saved/{id}/items (SavedShoppingListItemInput) SavedShoppingListItemSchema
        PUT /saved/{id}/items/{item_id} (SavedShoppingListItemInput) SavedShoppingListItemSchema
    }

    class FamilyRouter {
        prefix: /family
        GET [] FamilyMemberResponse
        POST (FamilyMemberCreate) FamilyMemberResponse
        GET /{id} FamilyMemberResponse
        PUT /{id} (FamilyMemberUpdate) FamilyMemberResponse
        DELETE /{id} None
        POST /{id}/preferences(AssignPreferencesRequest) FamilyMemberResponse
    }

    class PreferencesRouter {
        prefix: /preferences
        GET [] PreferenceResponse
        POST (PreferenceCreate) PreferenceResponse
        GET /{id} PreferenceResponse
        PUT /{id} (PreferenceUpdate) PreferenceResponse
        DELETE /{id} None
    }

    class CategoriesRouter {
        prefix: /categories
        GET /recipe/active[] ActiveCategoryResponse
        GET /recipe[] CategoryResponse
        POST /recipe (CreateCategoryRequest) int
        PUT /recipe/{id} (UpdateCategoryRequest) int
        DELETE /recipe/{id} None
        GET /product/active[] ActiveCategoryResponse
        GET /product[] CategoryResponse
        POST /product (CreateCategoryRequest) int
        PUT /product/{id} (UpdateCategoryRequest) int
        DELETE /product/{id} None
    }

    class MealTypesRouter {
        prefix: /meal-types
        GET [] MealTypeResponse
        POST (MealTypeCreate) MealTypeResponse
        GET /{id} MealTypeResponse
        PUT /{id} (MealTypeUpdate) MealTypeResponse
        DELETE /{id} None
        GET /{id}/usage[] MealTypeUsageResponse
    }

    class ImportExportRouter {
        prefix: /import-export
        GET /recipes/export(?format) file_response
        POST /recipes/import(upload_file) ImportResult
        GET /products/export(?format) file_response
        POST /products/import(upload_file) ImportResult
    }

    class SystemRouter {
        prefix: /system
        GET /units[] UnitResponse
        GET /info SystemInfoResponse
    }

    %% === SCHEMAS (Request/Response Models) ===
    class PaginatedResponse~T~ {
        items: list[T]
        total: int
        page: int
        page_size: int
    }

    class UserResponse {
        id: int
        email: str
        nickname: str
        created_at: datetime
        last_login_at: datetime | None
    }

    class TokenResponse {
        access_token: str
        refresh_token: str
    }

    class RecipeResponse {
        id: int
        name: str
        category_id: int
        servings: int
        ingredients: list[RecipeIngredientSchema]
        steps: list[CookingStepSchema]
        weight: int
        total_pieces: int | None
        pieces_per_portion: int | None
        link: str | None
        comment: str | None
    }

    class ProductResponse {
        id: int
        name: str
        recipe_unit: str
        purchase_unit: str
        price_per_purchase_unit: float
        brand: str
        supplier: str
        conversion_factor: float
        category_id: int
    }

    class MenuResponse {
        id: int
        name: str
        slots: list[MenuSlotSchema]
    }

    class MenuSlotSchema {
        id: int
        day: int
        meal_type_id: int
        recipe_id: int | None
        product_id: int | None
        quantity: float | None
        unit: str | None
        servings_override: float | None
        pieces_override: int | None
        position: int
        member_ids: list[int]
    }

    class ShoppingListResponse {
        items: list[ShoppingListItemResponse]
        total_cost: MoneySchema
    }

    class ShoppingListItemResponse {
        product_id: int
        product_name: str
        category: str
        quantity: QuantitySchema
        buy_quantity: QuantitySchema
        cost: MoneySchema
        purchased: bool
        recipe_quantity: QuantitySchema | None
    }

    class SavedShoppingListResponse {
        id: int
        name: str
        source_menu_id: int | None
        items: list[SavedShoppingListItemSchema]
        created_at: datetime
        updated_at: datetime
        total_cost: MoneySchema
    }

    class FamilyMemberResponse {
        id: int
        name: str
        portion_multiplier: float
        comment: str
        preference_ids: list[int]
    }

    class PreferenceResponse {
        id: int
        name: str
        type: str
        mode: str
        category_ids: list[int]
        product_ids: list[int]
        recipe_category_ids: list[int]
    }

    class MealTypeResponse {
        id: int
        name: str
        time: str
        is_system: bool
        sort_order: int
    }

    class ActiveCategoryResponse {
        id: int
        name: str
        color: str | None
    }

    class QuantitySchema {
        amount: float
        unit: str
    }

    class MoneySchema {
        amount: float
        currency: str
    }

    class MealSummaryResponseSchema {
        recipe_id: int
        recipe_name: str
        total_recipes_used: int
        total_products_used: int
        products: list[MealSummaryProductSchema]
    }

    %% === CONVERTERS ===
    class Converters {
        <<utility>>
        +recipe_to_response(recipe: Recipe, name_lookup: Callable) RecipeResponse
        +schema_to_recipe_data(schema: RecipeCreate) RecipeData
        +product_to_response(product: Product) ProductResponse
        +schema_to_product_data(schema: ProductCreate) ProductData
        +menu_to_response(menu: WeeklyMenu) MenuResponse
        +schema_to_menu_slot(schema: MenuSlotSchema) MenuSlot
        +preference_to_response(pref: Preference) PreferenceResponse
        +shopping_list_to_response(sl: ShoppingList) ShoppingListResponse
        +saved_shopping_list_to_response(ssl: SavedShoppingList) SavedShoppingListResponse
        +family_member_to_response(fm: FamilyMember) FamilyMemberResponse
        +meal_type_to_response(mt: MealType) MealTypeResponse
    }

    %% === DEPENDENCIES ===
    FastAPIApp --> AuthRouter : includes
    FastAPIApp --> RecipesRouter : includes
    FastAPIApp --> ProductsRouter : includes
    FastAPIApp --> MenusRouter : includes
    FastAPIApp --> ShoppingListRouter : includes
    FastAPIApp --> FamilyRouter : includes
    FastAPIApp --> PreferencesRouter : includes
    FastAPIApp --> CategoriesRouter : includes
    FastAPIApp --> MealTypesRouter : includes
    FastAPIApp --> ImportExportRouter : includes
    FastAPIApp --> SystemRouter : includes

    FastAPIApp --> ApplicationContainer : uses_in_lifespan
    FastAPIApp --> GetContainer : uses
    FastAPIApp --> GetCurrentUser : uses

    AuthRouter --> GetContainer
    AuthRouter --> GetCurrentUser

    RecipesRouter --> GetContainer
    RecipesRouter --> GetCurrentUser
    RecipesRouter --> Converters

    ProductsRouter --> GetContainer
    ProductsRouter --> GetCurrentUser

    MenusRouter --> GetContainer
    MenusRouter --> GetCurrentUser

    ShoppingListRouter --> GetContainer
    ShoppingListRouter --> GetCurrentUser

    FamilyRouter --> GetContainer
    FamilyRouter --> GetCurrentUser

    PreferencesRouter --> GetContainer
    PreferencesRouter --> GetCurrentUser

    CategoriesRouter --> GetContainer
    CategoriesRouter --> GetCurrentUser

    MealTypesRouter --> GetContainer
    MealTypesRouter --> GetCurrentUser

    ImportExportRouter --> GetContainer
    ImportExportRouter --> GetCurrentUser
```

## Layer Summary

The **API Layer** contains:
- **1 FastAPI App** with CORS, exception handlers, rollback middleware
- **9 Routers** (~50+ endpoints total):
  - Authentication (7 endpoints)
  - Recipes (11 endpoints) — CRUD + validation + flattening + preferences + meal summary
  - Products (6 endpoints) — CRUD + categories
  - Menus (8 endpoints) — CRUD + slot operations (add/move/remove)
  - Shopping Lists (8 endpoints) — generate + saved CRUD + export
  - Family Members (6 endpoints) — CRUD + preference assignment
  - Preferences (5 endpoints) — CRUD
  - Categories (10 endpoints) — recipe + product category management
  - Meal Types (6 endpoints) — CRUD + usage checking
  - Import/Export (4 endpoints) — recipes + products
  - System (2 endpoints) — units + info
- **20+ Pydantic Schemas** (request/response DTOs)
- **Converter Functions** (entity ↔ schema mapping)
- **Dependency Injection** (ApplicationContainer + get_current_user)

**Key Patterns:**
- Dependency injection via FastAPI Depends()
- ApplicationContainer created per request (lifespan)
- Bearer token authentication via get_current_user dependency
- User ID extraction from JWT via container use case
- Exception handlers map domain errors to HTTP status codes
- Converters decouple domain from API schemas
