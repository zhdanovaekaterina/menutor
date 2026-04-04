# API Layer — Detailed Class Diagram

```mermaid
classDiagram
    %% === FASTAPI APP SETUP ===
    class FastAPIApp {
        <<fastapi_application>>
        -title: str = "Menutor API"
        -description: str = "API планировщика меню"
        -version: str
        +lifespan(app: FastAPI) AsyncIterator[None]
        +middleware(http) rollback_on_error()
        +exception_handler(AuthenticationError) JSONResponse
        +exception_handler(UserAlreadyExistsError) JSONResponse
        +exception_handler(EntityNotFoundError) JSONResponse
        +exception_handler(CircularDependencyError) JSONResponse
        +exception_handler(MealTypeLimitError) JSONResponse
        +exception_handler(SystemMealTypeDeletionError) JSONResponse
        +exception_handler(DomainError) JSONResponse
        +exception_handler(RepositoryError) JSONResponse
        +exception_handler(ImportValidationError) JSONResponse
        +exception_handler(NestingDepthExceededError) JSONResponse
    }

    class ApplicationContainer {
        <<composition_root>>
        -_session: Session
        +get_register_user: RegisterUser
        +get_login_user: LoginUser
        +get_refresh_token: RefreshAccessToken
        +get_current_user: GetCurrentUser
        +get_change_password: ChangePassword
        +get_update_profile: UpdateProfile
        +get_logout_user: LogoutUser
        +get_create_recipe: CreateRecipe
        +get_edit_recipe: EditRecipe
        +get_recipe: GetEntity
        +get_list_recipes: PaginatedListEntities
        +get_delete_recipe: DeleteEntity
        +get_create_product: CreateProduct
        +get_edit_product: EditProduct
        +get_product: GetEntity
        +get_list_products: PaginatedListEntities
        +get_delete_product: DeleteEntity
        +get_create_menu: CreateMenu
        +get_save_menu: SaveMenu
        +get_load_menu: LoadMenu
        +get_delete_menu: DeleteMenu
        +get_list_menus: ListMenus
        +get_add_dish_to_slot: AddDishToSlot
        +get_move_slot: MoveSlotInMenu
        +get_remove_slot: RemoveItemFromSlot
        +get_generate_shopping_list: GenerateShoppingList
        +get_generate_filtered_shopping_list: GenerateFilteredShoppingList
        +get_generate_and_save_shopping_list: GenerateAndSaveShoppingList
        +get_load_saved_list: LoadSavedShoppingList
        +get_list_saved_lists: ListSavedShoppingLists
        +get_delete_saved_list: DeleteSavedShoppingList
        +get_export_shopping_list: ExportShoppingList
        +get_flatten_recipe: FlattenRecipeProducts
        +get_preview_flattened: PreviewFlattenedProducts
        +get_validate_sub_recipe: ValidateSubRecipe
        +get_generate_meal_summary: GenerateMealSummary
        +get_create_family_member: CreateFamilyMember
        +get_edit_family_member: EditFamilyMember
        +get_list_family_members: ListFamilyMembers
        +get_delete_family_member: DeleteFamilyMember
        +get_assign_preferences: AssignPreferences
        +get_create_preference: CreatePreference
        +get_update_preference: UpdatePreference
        +get_delete_preference: DeletePreference
        +get_list_preferences: ListPreferences
        +get_match_recipe_preferences: MatchRecipePreferences
        +get_list_meal_types: ListMealTypes
        +get_create_meal_type: CreateMealType
        +get_update_meal_type: UpdateMealType
        +get_delete_meal_type: DeleteMealType
        +get_check_meal_type_usage: CheckMealTypeUsage
        +get_manage_recipe_categories: ManageCategory
        +get_manage_product_categories: ManageCategory
        +get_export_recipes: ExportRecipes
        +get_import_recipes: ImportRecipes
        +get_export_products: ExportProducts
        +get_import_products: ImportProducts
        +export_registry: ExportRegistry
        +import_registry: ImportRegistry
    }

    class Deps {
        <<dependency_provider>>
        +get_container(request: Request) ApplicationContainer
    }

    class Auth {
        <<authentication>>
        +get_current_user(request: Request, container: ApplicationContainer) User
    }

    %% === ROUTERS ===
    class AuthRouter {
        prefix: /auth
        tags: [auth]
        +register(body: RegisterRequest, container, user) UserResponse
        +login(body: LoginRequest, container) TokenResponse
        +refresh_token(body: RefreshRequest, container) TokenResponse
        +get_me(container, user: User) UserResponse
        +change_password(body: ChangePasswordRequest, user: User, container) None
        +update_profile(body: UpdateProfileRequest, user: User, container) UserResponse
        +logout(body: LogoutRequest, container) None
    }

    class RecipesRouter {
        prefix: /recipes
        tags: [recipes]
        +list_recipes(page, search, category_id, container, user) PaginatedResponse
        +list_recipe_categories(container, user) list[ActiveCategoryResponse]
        +validate_sub_recipe(body: ValidateSubRecipeRequest, container, user) ValidateSubRecipeResponse
        +get_recipe(recipe_id, container, user) RecipeResponse
        +create_recipe(body: RecipeCreate, container, user) RecipeResponse
        +update_recipe(recipe_id, body: RecipeUpdate, container, user) RecipeResponse
        +delete_recipe(recipe_id, container, user) None
        +flatten_recipe_products(recipe_id, container, user) dict[int, QuantitySchema]
        +get_recipe_meal_summary(recipe_id, scale_factor, container, user) MealSummaryResponseSchema
        +get_matching_preferences(recipe_id, container, user) list[PreferenceResponse]
        +preview_flattened_products(body: FlattenedProductsPreviewRequest) PreviewResponse
    }

    class ProductsRouter {
        prefix: /products
        tags: [products]
        +list_products(page, search, category_id, container, user) PaginatedResponse
        +list_product_categories(container, user) list[ActiveCategoryResponse]
        +get_product(product_id, container, user) ProductResponse
        +create_product(body: ProductCreate, container, user) ProductResponse
        +update_product(product_id, body: ProductUpdate, container, user) ProductResponse
        +delete_product(product_id, container, user) None
    }

    class MenusRouter {
        prefix: /menus
        tags: [menus]
        +list_menus(container, user) list[MenuResponse]
        +create_menu(body: CreateMenuRequest, container, user) MenuResponse
        +get_menu(menu_id, container, user) MenuResponse
        +update_menu(menu_id, body: UpdateMenuRequest, container, user) MenuResponse
        +delete_menu(menu_id, container, user) None
        +add_dish_to_slot(menu_id, body: AddSlotRequest, container, user) MenuResponse
        +move_slot_in_menu(menu_id, body: MoveSlotRequest, container, user) MenuResponse
        +remove_slot_item(menu_id, body: RemoveSlotRequest, container, user) MenuResponse
    }

    class ShoppingListRouter {
        prefix: /shopping-list
        tags: [shopping_list]
        +generate_from_menu(menu_id, exclude_sub_recipes, container, user) ShoppingListResponse
        +generate_and_save(body: GenerateAndSaveRequest, container, user) SavedShoppingListResponse
        +list_saved_lists(container, user) list[SavedShoppingListMetaResponse]
        +get_saved_list(list_id, container, user) SavedShoppingListResponse
        +delete_saved_list(list_id, container, user) None
        +export_saved_list(list_id, format, container, user) FileResponse
        +add_saved_list_item(list_id, body: SavedShoppingListItemInput, container, user) SavedShoppingListItemSchema
        +update_saved_list_item(list_id, item_id, body: SavedShoppingListItemInput, container, user) SavedShoppingListItemSchema
    }

    class FamilyRouter {
        prefix: /family
        tags: [family]
        +list_family_members(container, user) list[FamilyMemberResponse]
        +create_family_member(body: FamilyMemberCreate, container, user) FamilyMemberResponse
        +get_family_member(member_id, container, user) FamilyMemberResponse
        +update_family_member(member_id, body: FamilyMemberUpdate, container, user) FamilyMemberResponse
        +delete_family_member(member_id, container, user) None
        +assign_preferences(member_id, body: AssignPreferencesRequest, container, user) FamilyMemberResponse
    }

    class PreferencesRouter {
        prefix: /preferences
        tags: [preferences]
        +list_preferences(container, user) list[PreferenceResponse]
        +create_preference(body: PreferenceCreate, container, user) PreferenceResponse
        +get_preference(preference_id, container, user) PreferenceResponse
        +update_preference(preference_id, body: PreferenceUpdate, container, user) PreferenceResponse
        +delete_preference(preference_id, container, user) None
    }

    class CategoriesRouter {
        prefix: /categories
        tags: [categories]
        +get_active_recipe_categories(container, user) list[ActiveCategoryResponse]
        +get_all_recipe_categories(container, user) list[CategoryResponse]
        +create_recipe_category(body: CreateCategoryRequest, container, user) int
        +update_recipe_category(category_id, body: UpdateCategoryRequest, container, user) int
        +delete_recipe_category(category_id, container, user) None
        +get_active_product_categories(container, user) list[ActiveCategoryResponse]
        +get_all_product_categories(container, user) list[CategoryResponse]
        +create_product_category(body: CreateCategoryRequest, container, user) int
        +update_product_category(category_id, body: UpdateCategoryRequest, container, user) int
        +delete_product_category(category_id, container, user) None
    }

    class MealTypesRouter {
        prefix: /meal-types
        tags: [meal_types]
        +list_meal_types(container, user) list[MealTypeResponse]
        +create_meal_type(body: MealTypeCreate, container, user) MealTypeResponse
        +get_meal_type(meal_type_id, container, user) MealTypeResponse
        +update_meal_type(meal_type_id, body: MealTypeUpdate, container, user) MealTypeResponse
        +delete_meal_type(meal_type_id, container, user) None
        +get_meal_type_usage(meal_type_id, container, user) list[MealTypeUsageResponse]
    }

    class ImportExportRouter {
        prefix: /import-export
        tags: [import_export]
        +export_recipes(format, container, user) FileResponse
        +import_recipes(file, container, user) ImportResult
        +export_products(format, container, user) FileResponse
        +import_products(file, container, user) ImportResult
    }

    class SystemRouter {
        prefix: /system
        tags: [system]
        +get_units() list[UnitResponse]
        +get_system_info() SystemInfoResponse
    }

    %% === PYDANTIC SCHEMAS (Request/Response) ===
    class BaseModel {
        <<pydantic>>
    }

    class PaginatedResponse~T~ {
        -items: list[T]
        -total: int
        -page: int
        -page_size: int
    }

    class UserResponse {
        -id: int
        -email: str
        -nickname: str
        -created_at: datetime
        -last_login_at: datetime | None
    }

    class TokenResponse {
        -access_token: str
        -refresh_token: str
    }

    class RecipeResponse {
        -id: int
        -name: str
        -category_id: int
        -servings: int
        -ingredients: list[RecipeIngredientSchema]
        -steps: list[CookingStepSchema]
        -weight: int
        -total_pieces: int | None
        -pieces_per_portion: int | None
        -link: str | None
        -comment: str | None
    }

    class RecipeCreate {
        -name: str
        -category_id: int
        -servings: int
        -ingredients: list[RecipeIngredientSchema]
        -steps: list[CookingStepSchema]
        -weight: int
        -total_pieces: int | None
        -pieces_per_portion: int | None
        -link: str | None
        -comment: str | None
    }

    class RecipeIngredientSchema {
        -product_id: int | None
        -sub_recipe_id: int | None
        -sub_recipe_name: str | None
        -quantity_amount: float
        -quantity_unit: str
        -order: int
        +check_xor() validation
    }

    class CookingStepSchema {
        -order: int
        -description: str
    }

    class ProductResponse {
        -id: int
        -name: str
        -recipe_unit: str
        -purchase_unit: str
        -price_per_purchase_unit: float
        -brand: str
        -supplier: str
        -conversion_factor: float
        -category_id: int
    }

    class ProductCreate {
        -name: str
        -recipe_unit: str
        -purchase_unit: str
        -price_per_purchase_unit: float
        -brand: str
        -supplier: str
        -conversion_factor: float
        -category_id: int
    }

    class MenuResponse {
        -id: int
        -name: str
        -slots: list[MenuSlotSchema]
    }

    class MenuSlotSchema {
        -id: int
        -day: int (0-6)
        -meal_type_id: int
        -recipe_id: int | None
        -product_id: int | None
        -quantity: float | None
        -unit: str | None
        -servings_override: float | None
        -pieces_override: int | None
        -position: int
        -member_ids: list[int]
    }

    class ShoppingListResponse {
        -items: list[ShoppingListItemResponse]
        -total_cost: MoneySchema
    }

    class ShoppingListItemResponse {
        -product_id: int
        -product_name: str
        -category: str
        -quantity: QuantitySchema
        -buy_quantity: QuantitySchema
        -cost: MoneySchema
        -purchased: bool
        -recipe_quantity: QuantitySchema | None
    }

    class SavedShoppingListResponse {
        -id: int
        -name: str
        -source_menu_id: int | None
        -items: list[SavedShoppingListItemSchema]
        -created_at: datetime
        -updated_at: datetime
        -total_cost: MoneySchema
    }

    class SavedShoppingListItemSchema {
        -id: int
        -product_id: int | None
        -product_name: str
        -category: str
        -quantity: QuantitySchema
        -buy_quantity: QuantitySchema
        -buy_quantity_overridden: bool
        -cost: MoneySchema
        -purchased: bool
        -recipe_quantity: QuantitySchema | None
        -item_order: int
    }

    class FamilyMemberResponse {
        -id: int
        -name: str
        -portion_multiplier: float
        -comment: str
        -preference_ids: list[int]
    }

    class FamilyMemberCreate {
        -name: str
        -portion_multiplier: float
        -comment: str
        -preference_ids: list[int]
    }

    class PreferenceResponse {
        -id: int
        -name: str
        -type: str (CATEGORY_BASED | ALLERGY)
        -mode: str (BLOCKED | ALLOWED)
        -category_ids: list[int]
        -product_ids: list[int]
        -recipe_category_ids: list[int]
    }

    class PreferenceCreate {
        -name: str
        -type: str
        -mode: str
        -category_ids: list[int]
        -product_ids: list[int]
        -recipe_category_ids: list[int]
    }

    class MealTypeResponse {
        -id: int
        -name: str
        -time: str (HH:MM)
        -is_system: bool
        -sort_order: int
    }

    class MealTypeCreate {
        -name: str
        -time: time
    }

    class ActiveCategoryResponse {
        -id: int
        -name: str
        -color: str | None
    }

    class CategoryResponse {
        -id: int
        -name: str
        -active: bool
        -color: str | None
    }

    class QuantitySchema {
        -amount: float
        -unit: str
    }

    class MoneySchema {
        -amount: float
        -currency: str
    }

    class MealSummaryResponseSchema {
        -recipe_id: int
        -recipe_name: str
        -total_recipes_used: int
        -total_products_used: int
        -products: list[MealSummaryProductSchema]
    }

    class MealSummaryProductSchema {
        -product_id: int
        -product_name: str
        -quantity: QuantitySchema
        -category: str
        -occurrences: list[MealOccurrenceSchema]
    }

    class ValidateSubRecipeRequest {
        -parent_recipe_id: int | None
        -sub_recipe_id: int
    }

    class ValidateSubRecipeResponse {
        -valid: bool
        -error: str | None
    }

    %% === CONVERTER FUNCTIONS ===
    class Converters {
        <<utility>>
        +recipe_to_response(recipe: Recipe, name_lookup: Callable) RecipeResponse
        +schema_to_recipe_data(schema: RecipeCreate) RecipeData
        +product_to_response(product: Product) ProductResponse
        +schema_to_product_data(schema: ProductCreate) ProductData
        +schema_to_product_data_with_id(product_id: ProductId, schema: ProductCreate) ProductData
        +menu_to_response(menu: WeeklyMenu) MenuResponse
        +schema_to_menu_slot(schema: MenuSlotSchema) MenuSlot
        +preference_to_response(pref: Preference) PreferenceResponse
        +schema_to_preference_data(schema: PreferenceCreate) PreferenceData
        +shopping_list_to_response(sl: ShoppingList) ShoppingListResponse
        +shopping_list_item_to_response(item: ShoppingListItem) ShoppingListItemResponse
        +saved_shopping_list_to_response(ssl: SavedShoppingList) SavedShoppingListResponse
        +family_member_to_response(fm: FamilyMember) FamilyMemberResponse
        +schema_to_family_member_data(schema: FamilyMemberCreate) FamilyMemberData
        +meal_type_to_response(mt: MealType) MealTypeResponse
        +ingredient_node_to_schema(node: IngredientNode) MealIngredientSchema
        +active_category_to_response(ac: ActiveCategory) ActiveCategoryResponse
        +category_to_response(c: Category) CategoryResponse
    }

    %% === RELATIONSHIPS ===
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

    FastAPIApp --> ApplicationContainer : creates_in_lifespan
    FastAPIApp --> Deps : uses
    FastAPIApp --> Auth : uses

    AuthRouter --> ApplicationContainer : depends_on
    AuthRouter --> Auth : depends_on
    RecipesRouter --> ApplicationContainer : depends_on
    RecipesRouter --> Auth : depends_on
    RecipesRouter --> Converters : uses
    ProductsRouter --> ApplicationContainer : depends_on
    ProductsRouter --> Auth : depends_on
    MenusRouter --> ApplicationContainer : depends_on
    MenusRouter --> Auth : depends_on
    ShoppingListRouter --> ApplicationContainer : depends_on
    ShoppingListRouter --> Auth : depends_on
    FamilyRouter --> ApplicationContainer : depends_on
    FamilyRouter --> Auth : depends_on
    PreferencesRouter --> ApplicationContainer : depends_on
    PreferencesRouter --> Auth : depends_on
    CategoriesRouter --> ApplicationContainer : depends_on
    CategoriesRouter --> Auth : depends_on
    MealTypesRouter --> ApplicationContainer : depends_on
    MealTypesRouter --> Auth : depends_on
    ImportExportRouter --> ApplicationContainer : depends_on
    ImportExportRouter --> Auth : depends_on

    PaginatedResponse~T~ --|> BaseModel
    UserResponse --|> BaseModel
    TokenResponse --|> BaseModel
    RecipeResponse --|> BaseModel
    RecipeCreate --|> BaseModel
    RecipeIngredientSchema --|> BaseModel
    CookingStepSchema --|> BaseModel
    ProductResponse --|> BaseModel
    ProductCreate --|> BaseModel
    MenuResponse --|> BaseModel
    MenuSlotSchema --|> BaseModel
    ShoppingListResponse --|> BaseModel
    ShoppingListItemResponse --|> BaseModel
    SavedShoppingListResponse --|> BaseModel
    SavedShoppingListItemSchema --|> BaseModel
    FamilyMemberResponse --|> BaseModel
    FamilyMemberCreate --|> BaseModel
    PreferenceResponse --|> BaseModel
    PreferenceCreate --|> BaseModel
    MealTypeResponse --|> BaseModel
    MealTypeCreate --|> BaseModel
    ActiveCategoryResponse --|> BaseModel
    CategoryResponse --|> BaseModel
    QuantitySchema --|> BaseModel
    MoneySchema --|> BaseModel
    MealSummaryResponseSchema --|> BaseModel
```

## Detailed Breakdown

### FastAPI Application Setup
- **Lifespan hook**: Creates ApplicationContainer on startup
- **Middleware**: rollback_on_error() reverts sessions on exceptions
- **Exception handlers**: Map domain exceptions to HTTP status codes:
  - AuthenticationError → 401 Unauthorized
  - UserAlreadyExistsError → 409 Conflict
  - EntityNotFoundError → 404 Not Found
  - CircularDependencyError → 400 Bad Request
  - MealTypeLimitError → 400 Bad Request
  - SystemMealTypeDeletionError → 400 Bad Request
  - DomainError → 400 Bad Request
  - RepositoryError → 500 Internal Server Error
  - ImportValidationError → 400 Bad Request
  - NestingDepthExceededError → 400 Bad Request

### Dependency Injection
- **get_container()**: Extracts ApplicationContainer from request.app.state
- **get_current_user()**: Extracts Bearer token → validates via container → returns User
- All routers depend on these to inject container and authenticated user

### Routers (9 total, ~50 endpoints)
Each router prefix-groups related endpoints:

- **AuthRouter** (/auth):
  - POST /register → user creation + default family member + system meal types
  - POST /login → JWT token pair generation
  - POST /refresh → token rotation
  - GET /me → current user from token
  - POST /change-password → password update
  - POST /update-profile → nickname/password update
  - POST /logout → refresh token revocation

- **RecipesRouter** (/recipes):
  - Paginated list with search/category filter
  - CRUD with sub-recipe validation (cycles, depth, ownership)
  - Special endpoints: flatten, meal-summary, matching-preferences, preview

- **ProductsRouter** (/products):
  - Similar CRUD to recipes but simpler (no sub-recipes)

- **MenusRouter** (/menus):
  - CRUD weekly menus
  - Slot operations: add (upsert), move (with position shifting), remove

- **ShoppingListRouter** (/shopping-list):
  - Generate from menu (with optional sub-recipe exclusions)
  - Generate and save (creates SavedShoppingList)
  - CRUD saved lists
  - Export by format (CSV, JSON, PDF)
  - Item-level operations (add, update)

- **FamilyRouter** (/family):
  - CRUD family members
  - Assign preferences to members

- **PreferencesRouter** (/preferences):
  - CRUD dietary/lifestyle preferences

- **CategoriesRouter** (/categories):
  - Separate recipe and product category management
  - Get active / get all / create / update / delete

- **MealTypesRouter** (/meal-types):
  - CRUD meal types
  - Check usage (returns list of menus using the type)

- **ImportExportRouter** (/import-export):
  - Export recipes/products to format (CSV, JSON)
  - Import from file with upsert semantics

- **SystemRouter** (/system):
  - GET /units → list of available units
  - GET /info → system info (version, etc.)

### Pydantic Schemas (20+ classes)
Request and response DTOs with validation:
- **Pagination**: PaginatedResponse[T]
- **Auth**: UserResponse, TokenResponse, RegisterRequest, LoginRequest, etc.
- **Recipes**: RecipeCreate, RecipeResponse, RecipeIngredientSchema, etc.
- **Products**: ProductCreate, ProductResponse
- **Menus**: MenuResponse, MenuSlotSchema, CreateMenuRequest, AddSlotRequest, etc.
- **Shopping**: ShoppingListResponse, SavedShoppingListResponse, SavedShoppingListItemSchema
- **Family**: FamilyMemberResponse, FamilyMemberCreate
- **Preferences**: PreferenceResponse, PreferenceCreate
- **Meal Types**: MealTypeResponse, MealTypeCreate
- **Categories**: ActiveCategoryResponse, CategoryResponse
- **Value Objects**: QuantitySchema, MoneySchema
- **Special**: MealSummaryResponseSchema, ValidateSubRecipeRequest/Response

### Converter Functions
Decouple domain entities from API schemas:
- recipe_to_response(): Recipe + name_lookup → RecipeResponse
- schema_to_recipe_data(): RecipeCreate → RecipeData
- Similar patterns for products, menus, preferences, shopping lists, etc.
- Handles denormalization (e.g., sub_recipe_name added to response)

### Authentication Flow
1. Client: POST /auth/login with email + password
2. Server: validates, creates access + refresh token pair
3. Client: GET /recipes with Bearer {access_token}
4. Server: get_current_user dependency extracts token, validates, returns User
5. Router handlers receive authenticated user object
6. All repo queries filtered by user_id (ownership enforcement)
7. When token expires: POST /auth/refresh with refresh_token
8. Server: validates refresh, revokes old, issues new pair

### Error Handling
Domain exceptions are caught and converted to HTTP responses:
- 401: auth failures (invalid token, password mismatch)
- 409: user already exists
- 404: entity not found
- 400: validation errors (duplicate names, invalid sub-recipes, cycles, etc.)
- 500: repository/database errors

### Key Design Decisions
- **Dependency Injection**: FastAPI Depends() makes testing easy
- **Separation of Concerns**: Converters decouple API from domain
- **Validation at Multiple Levels**: Pydantic (schema) + domain (entity invariants) + use cases (business rules)
- **Bearer Token Auth**: Standard HTTP authorization header
- **Stateless**: Each request is independent; container created per request
- **Rollback on Error**: Session rollback ensures no partial updates
