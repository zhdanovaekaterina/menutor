# Application Layer — Detailed Class Diagram

```mermaid
classDiagram
    %% === DATA TRANSFER OBJECTS ===
    class PaginatedResult~T~ {
        -items: list[T]
        -total: int
        -page: int
        -page_size: int
    }

    class RegisterData {
        -email: str
        -password: str
        -nickname: str
    }

    class LoginData {
        -email: str
        -password: str
    }

    class TokenPair {
        -access_token: str
        -refresh_token: str
    }

    class ChangePasswordData {
        -current_password: str
        -new_password: str
    }

    class UpdateProfileData {
        -nickname: str | None
        -password: str | None
    }

    class RecipeData {
        -name: str
        -category_id: RecipeCategoryId
        -servings: int
        -ingredients: list[RecipeIngredient]
        -steps: list[CookingStep]
        -weight: int
        -total_pieces: int | None
        -pieces_per_portion: int | None
        -link: str | None
        -comment: str | None
    }

    class ProductData {
        -name: str
        -recipe_unit: str
        -purchase_unit: str
        -price_per_purchase_unit: Money
        -brand: str
        -supplier: str
        -conversion_factor: float
        -category_id: ProductCategoryId
    }

    class FamilyMemberData {
        -name: str
        -portion_multiplier: float
        -comment: str
        -preference_ids: list[PreferenceId]
    }

    class CategoryData {
        -name: str
        -category_id: int | None
        -color: str | None
    }

    class PreferenceData {
        -name: str
        -type: PreferenceType
        -mode: PreferenceMode
        -category_ids: list[ProductCategoryId]
        -product_ids: list[ProductId]
        -recipe_category_ids: list[RecipeCategoryId]
    }

    class MealTypeData {
        -name: str
        -time: time
    }

    %% === HELPER FUNCTIONS ===
    class CRUDHelpers {
        <<utility>>
        +load_owned(repo: Any, id: Any, user_id: UserId, label: str) Any
    }

    %% === CRUD BASE CLASSES ===
    class CreateEntity {
        <<abstract>>
        -_repo: Any
        +__init__(repo: Any) None
        +_build_entity(data: Any, user_id: UserId) Any
        +execute(data: Any, user_id: UserId) Any
    }

    class EditEntity {
        <<abstract>>
        -_repo: Any
        -_label: str
        +__init__(repo: Any) None
        +_build_entity(id: Any, data: Any, user_id: UserId) Any
        +execute(id: Any, data: Any, user_id: UserId) Any
    }

    class DeleteEntity {
        -_repo: Any
        +__init__(repo: Any) None
        +execute(ids: Any, user_id: UserId) None
    }

    class GetEntity {
        -_repo: Any
        +__init__(repo: Any) None
        +execute(id: Any, user_id: UserId) Any | None
    }

    class ListEntities {
        -_repo: Any
        +__init__(repo: Any) None
        +execute(user_id: UserId, category_id: Any) list[Any]
    }

    class PaginatedListEntities {
        -_repo: Any
        +__init__(repo: Any) None
        +execute(user_id: UserId, category_id: Any, page: int | None, search: str) PaginatedResult
    }

    %% === AUTHENTICATION USE CASES ===
    class RegisterUser {
        -_user_repo: UserRepository
        -_hasher: PasswordHasher
        -_family_repo: FamilyMemberRepository
        -_meal_type_repo: MealTypeRepository
        +__init__(user_repo: UserRepository, hasher: PasswordHasher, family_repo: FamilyMemberRepository, meal_type_repo: MealTypeRepository) None
        +execute(data: RegisterData) User
    }

    class LoginUser {
        -_user_repo: UserRepository
        -_hasher: PasswordHasher
        -_token_service: TokenService
        -_refresh_repo: RefreshTokenRepository
        +__init__(user_repo: UserRepository, hasher: PasswordHasher, token_service: TokenService, refresh_repo: RefreshTokenRepository) None
        +execute(data: LoginData) TokenPair
    }

    class RefreshAccessToken {
        -_token_service: TokenService
        -_refresh_repo: RefreshTokenRepository
        -_user_repo: UserRepository
        +__init__(token_service: TokenService, refresh_repo: RefreshTokenRepository, user_repo: UserRepository) None
        +execute(raw_refresh_token: str) TokenPair
    }

    class GetCurrentUser {
        -_token_service: TokenService
        -_user_repo: UserRepository
        +__init__(token_service: TokenService, user_repo: UserRepository) None
        +execute(access_token: str) User
    }

    class ChangePassword {
        -_user_repo: UserRepository
        -_hasher: PasswordHasher
        +__init__(user_repo: UserRepository, hasher: PasswordHasher) None
        +execute(user: User, data: ChangePasswordData) None
    }

    class UpdateProfile {
        -_user_repo: UserRepository
        -_hasher: PasswordHasher
        +__init__(user_repo: UserRepository, hasher: PasswordHasher) None
        +execute(user: User, data: UpdateProfileData) User
    }

    class LogoutUser {
        -_token_service: TokenService
        -_refresh_repo: RefreshTokenRepository
        +__init__(token_service: TokenService, refresh_repo: RefreshTokenRepository) None
        +execute(raw_refresh_token: str) None
    }

    %% === RECIPE USE CASES ===
    class CreateRecipe {
        -_repo: RecipeRepository
        -_validator: RecipeDependencyValidator | None
        +__init__(repo: RecipeRepository, validator: RecipeDependencyValidator | None) None
        +_build_entity(data: Any, user_id: UserId) Recipe
        +execute(data: RecipeData, user_id: UserId) Recipe
    }

    class EditRecipe {
        -_repo: RecipeRepository
        -_label: str
        -_validator: RecipeDependencyValidator | None
        +__init__(repo: RecipeRepository, validator: RecipeDependencyValidator | None) None
        +_build_entity(id: Any, data: Any, user_id: UserId) Recipe
        +execute(id: RecipeId, data: RecipeData, user_id: UserId) Recipe
    }

    class GetRecipe {
        <<alias>>
        -_repo: RecipeRepository
    }

    class DeleteRecipe {
        <<alias>>
        -_repo: RecipeRepository
    }

    class ListRecipes {
        <<alias>>
        -_repo: RecipeRepository
    }

    class PaginatedListRecipes {
        <<alias>>
        -_repo: RecipeRepository
    }

    %% === PRODUCT USE CASES ===
    class CreateProduct {
        -_repo: ProductRepository
        +_build_entity(data: Any, user_id: UserId) Product
    }

    class EditProduct {
        -_repo: ProductRepository
        -_label: str
        +_build_entity(id: Any, data: Any, user_id: UserId) Product
    }

    class GetProduct {
        <<alias>>
        -_repo: ProductRepository
    }

    class DeleteProduct {
        <<alias>>
        -_repo: ProductRepository
    }

    class ListProducts {
        <<alias>>
        -_repo: ProductRepository
    }

    class PaginatedListProducts {
        <<alias>>
        -_repo: ProductRepository
    }

    %% === MENU PLANNING USE CASES ===
    class CreateMenu {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(name: str, user_id: UserId) WeeklyMenu
    }

    class SaveMenu {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(menu: WeeklyMenu) WeeklyMenu
    }

    class LoadMenu {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(menu_id: MenuId, user_id: UserId) WeeklyMenu | None
    }

    class DeleteMenu {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(menu_id: MenuId, user_id: UserId) None
    }

    class ListMenus {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(user_id: UserId) list[WeeklyMenu]
    }

    class AddDishToSlot {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(menu_id: MenuId, slot: MenuSlot, user_id: UserId) WeeklyMenu
    }

    class MoveSlotInMenu {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(menu_id: MenuId, day: int, meal_type_id: MealTypeId, recipe_id: RecipeId | None, product_id: ProductId | None, to_day: int, to_meal_type_id: MealTypeId, to_position: int, position: int | None, user_id: UserId) WeeklyMenu
    }

    class RemoveItemFromSlot {
        -_repo: MenuRepository
        +__init__(repo: MenuRepository) None
        +execute(menu_id: MenuId, day: int, meal_type_id: MealTypeId, recipe_id: RecipeId | None, product_id: ProductId | None, position: int | None, user_id: UserId) WeeklyMenu
    }

    %% === SHOPPING LIST USE CASES ===
    class GenerateShoppingList {
        -_menu_repo: MenuRepository
        -_builder: ShoppingListBuilder
        +__init__(menu_repo: MenuRepository, builder: ShoppingListBuilder) None
        +execute(menu_id: MenuId, user_id: UserId) ShoppingList
    }

    class GenerateFilteredShoppingList {
        -_menu_repo: MenuRepository
        -_builder: ShoppingListBuilder
        +__init__(menu_repo: MenuRepository, builder: ShoppingListBuilder) None
        +execute(menu_id: MenuId, slot_indices: set[int], excluded_sub_recipe_ids: set[RecipeId] | None, user_id: UserId) ShoppingList
    }

    class GenerateAndSaveShoppingList {
        -_menu_repo: MenuRepository
        -_list_repo: SavedShoppingListRepository
        -_builder: ShoppingListBuilder
        +__init__(menu_repo: MenuRepository, list_repo: SavedShoppingListRepository, builder: ShoppingListBuilder) None
        +execute(menu_id: MenuId, name: str, user_id: UserId) SavedShoppingList
    }

    class LoadSavedShoppingList {
        -_repo: SavedShoppingListRepository
        +__init__(repo: SavedShoppingListRepository) None
        +execute(id: SavedShoppingListId, user_id: UserId) SavedShoppingList | None
    }

    class ListSavedShoppingLists {
        -_repo: SavedShoppingListRepository
        +__init__(repo: SavedShoppingListRepository) None
        +execute(user_id: UserId) list[SavedShoppingList]
    }

    class DeleteSavedShoppingList {
        -_repo: SavedShoppingListRepository
        +__init__(repo: SavedShoppingListRepository) None
        +execute(ids: SavedShoppingListId | list[SavedShoppingListId], user_id: UserId) None
    }

    class ExportShoppingList {
        -_exporter: EntityExporter
        +__init__(exporter: EntityExporter) None
        +execute(shopping_list: ShoppingList) tuple[bytes, str, str]
    }

    %% === RECIPE ANALYSIS USE CASES ===
    class FlattenRecipeProducts {
        -_menu_repo: MenuRepository
        -_builder: ShoppingListBuilder
        +__init__(menu_repo: MenuRepository, builder: ShoppingListBuilder) None
        +execute(recipe_id: RecipeId, user_id: UserId) dict[ProductId, Quantity]
    }

    class PreviewFlattenedProducts {
        -_builder: ShoppingListBuilder
        -_recipe_repo: RecipeRepository
        +__init__(builder: ShoppingListBuilder, recipe_repo: RecipeRepository) None
        +execute(recipe: Recipe) dict[ProductId, Quantity]
    }

    class ValidateSubRecipe {
        -_validator: RecipeDependencyValidator
        +__init__(validator: RecipeDependencyValidator) None
        +execute(recipe_id: RecipeId, sub_recipe_ids: list[RecipeId]) None
    }

    class GenerateMealSummary {
        -_builder: ShoppingListBuilder
        -_recipe_repo: RecipeRepository
        +__init__(builder: ShoppingListBuilder, recipe_repo: RecipeRepository) None
        +execute(recipe_id: RecipeId, scale_factor: float, user_id: UserId) list[IngredientNode]
    }

    %% === CATEGORY USE CASES ===
    class ManageCategory {
        -_recipe_cat_repo: RecipeCategoryRepository
        -_product_cat_repo: ProductCategoryRepository
        +__init__(recipe_cat_repo: RecipeCategoryRepository, product_cat_repo: ProductCategoryRepository) None
        +get_active_recipe_categories() list[ActiveCategory]
        +get_active_product_categories() list[ActiveCategory]
        +get_all_recipe_categories() list[Category]
        +get_all_product_categories() list[Category]
        +create_recipe_category(name: str, color: str | None) int
        +create_product_category(name: str, color: str | None) int
        +update_recipe_category(cat_id: int, name: str, color: str | None) int
        +update_product_category(cat_id: int, name: str, color: str | None) int
        +delete_recipe_category(cat_id: int) None
        +delete_product_category(cat_id: int) None
        +is_recipe_category_used(cat_id: int) bool
        +is_product_category_used(cat_id: int) bool
        +move_and_delete_recipe_category(from_id: int, to_id: int) None
        +move_and_delete_product_category(from_id: int, to_id: int) None
    }

    %% === FAMILY USE CASES ===
    class CreateFamilyMember {
        -_repo: FamilyMemberRepository
        +_build_entity(data: Any, user_id: UserId) FamilyMember
    }

    class EditFamilyMember {
        -_repo: FamilyMemberRepository
        -_label: str
        +_build_entity(id: Any, data: Any, user_id: UserId) FamilyMember
    }

    class DeleteFamilyMember {
        <<alias>>
        -_repo: FamilyMemberRepository
    }

    class ListFamilyMembers {
        <<alias>>
        -_repo: FamilyMemberRepository
    }

    class AssignPreferences {
        -_family_repo: FamilyMemberRepository
        -_pref_repo: PreferenceRepository
        +__init__(family_repo: FamilyMemberRepository, pref_repo: PreferenceRepository) None
        +execute(member_id: FamilyMemberId, pref_ids: list[PreferenceId], user_id: UserId) FamilyMember
    }

    %% === PREFERENCE USE CASES ===
    class CreatePreference {
        -_repo: PreferenceRepository
        +__init__(repo: PreferenceRepository) None
        +execute(data: PreferenceData, user_id: UserId) Preference
    }

    class UpdatePreference {
        -_repo: PreferenceRepository
        +__init__(repo: PreferenceRepository) None
        +execute(preference_id: PreferenceId, data: PreferenceData, user_id: UserId) Preference
    }

    class DeletePreference {
        -_preference_repo: PreferenceRepository
        -_family_repo: FamilyMemberRepository
        +__init__(preference_repo: PreferenceRepository, family_repo: FamilyMemberRepository) None
        +execute(preference_id: PreferenceId, user_id: UserId) None
    }

    class ListPreferences {
        -_repo: PreferenceRepository
        +__init__(repo: PreferenceRepository) None
        +execute(user_id: UserId) list[Preference]
    }

    class MatchRecipePreferences {
        -_recipe_repo: RecipeRepository
        -_preference_repo: PreferenceRepository
        -_matcher: PreferenceMatcher
        +__init__(recipe_repo: RecipeRepository, preference_repo: PreferenceRepository, matcher: PreferenceMatcher) None
        +execute(recipe_id: RecipeId, user_id: UserId) list[Preference]
    }

    %% === MEAL TYPE USE CASES ===
    class ListMealTypes {
        -_repo: MealTypeRepository
        +__init__(repo: MealTypeRepository) None
        +execute(user_id: UserId) list[MealType]
    }

    class CreateMealType {
        -_repo: MealTypeRepository
        +__init__(repo: MealTypeRepository) None
        +execute(data: MealTypeData, user_id: UserId) MealType
    }

    class UpdateMealType {
        -_repo: MealTypeRepository
        +__init__(repo: MealTypeRepository) None
        +execute(meal_type_id: MealTypeId, data: MealTypeData, user_id: UserId) MealType
    }

    class DeleteMealType {
        -_repo: MealTypeRepository
        +__init__(repo: MealTypeRepository) None
        +execute(meal_type_id: MealTypeId, user_id: UserId) None
    }

    class CheckMealTypeUsage {
        -_repo: MealTypeRepository
        +__init__(repo: MealTypeRepository) None
        +execute(meal_type_id: MealTypeId, user_id: UserId) list[tuple[int, str]]
    }

    class CreateSystemMealTypes {
        -_repo: MealTypeRepository
        +__init__(repo: MealTypeRepository) None
        +execute(user_id: UserId) list[MealType]
    }

    %% === IMPORT/EXPORT USE CASES ===
    class ExportRecipes {
        -_recipe_repo: RecipeRepository
        -_exporter: EntityExporter
        +__init__(recipe_repo: RecipeRepository, exporter: EntityExporter) None
        +execute(user_id: UserId) tuple[bytes, str, str]
    }

    class ExportProducts {
        -_product_repo: ProductRepository
        -_exporter: EntityExporter
        +__init__(product_repo: ProductRepository, exporter: EntityExporter) None
        +execute(user_id: UserId) tuple[bytes, str, str]
    }

    class ImportRecipes {
        -_importer: EntityImporter
        -_recipe_repo: RecipeRepository
        +__init__(importer: EntityImporter, recipe_repo: RecipeRepository) None
        +execute(data: bytes, user_id: UserId) ImportResult
    }

    class ImportProducts {
        -_importer: EntityImporter
        -_product_repo: ProductRepository
        +__init__(importer: EntityImporter, product_repo: ProductRepository) None
        +execute(data: bytes, user_id: UserId) ImportResult
    }

    %% === RELATIONSHIPS ===
    CreateEntity --> PaginatedListEntities : similar
    EditEntity --> CreateEntity : similar
    GetEntity --> PaginatedListEntities : similar

    RegisterUser --> UserRepository
    RegisterUser --> PasswordHasher
    RegisterUser --> FamilyMemberRepository
    RegisterUser --> MealTypeRepository
    RegisterUser --> CreateSystemMealTypes : calls

    LoginUser --> UserRepository
    LoginUser --> PasswordHasher
    LoginUser --> TokenService
    LoginUser --> RefreshTokenRepository

    RefreshAccessToken --> TokenService
    RefreshAccessToken --> RefreshTokenRepository
    RefreshAccessToken --> UserRepository

    CreateRecipe --> CreateEntity
    CreateRecipe --> RecipeRepository
    CreateRecipe --> RecipeDependencyValidator

    EditRecipe --> EditEntity
    EditRecipe --> RecipeRepository
    EditRecipe --> RecipeDependencyValidator

    CreateMenu --> MenuRepository
    SaveMenu --> MenuRepository
    LoadMenu --> MenuRepository
    AddDishToSlot --> MenuRepository
    MoveSlotInMenu --> MenuRepository
    RemoveItemFromSlot --> MenuRepository

    GenerateShoppingList --> MenuRepository
    GenerateShoppingList --> ShoppingListBuilder

    GenerateFilteredShoppingList --> MenuRepository
    GenerateFilteredShoppingList --> ShoppingListBuilder

    GenerateAndSaveShoppingList --> MenuRepository
    GenerateAndSaveShoppingList --> SavedShoppingListRepository
    GenerateAndSaveShoppingList --> ShoppingListBuilder

    LoadSavedShoppingList --> SavedShoppingListRepository
    ListSavedShoppingLists --> SavedShoppingListRepository
    DeleteSavedShoppingList --> SavedShoppingListRepository

    ExportShoppingList --> EntityExporter

    FlattenRecipeProducts --> RecipeRepository
    FlattenRecipeProducts --> ShoppingListBuilder

    PreviewFlattenedProducts --> RecipeRepository
    PreviewFlattenedProducts --> ShoppingListBuilder

    ValidateSubRecipe --> RecipeDependencyValidator

    GenerateMealSummary --> RecipeRepository
    GenerateMealSummary --> ShoppingListBuilder

    CreateFamilyMember --> CreateEntity
    CreateFamilyMember --> FamilyMemberRepository

    EditFamilyMember --> EditEntity
    EditFamilyMember --> FamilyMemberRepository

    AssignPreferences --> FamilyMemberRepository
    AssignPreferences --> PreferenceRepository

    CreatePreference --> PreferenceRepository
    UpdatePreference --> PreferenceRepository
    DeletePreference --> PreferenceRepository
    DeletePreference --> FamilyMemberRepository

    ListMealTypes --> MealTypeRepository
    CreateMealType --> MealTypeRepository
    UpdateMealType --> MealTypeRepository
    DeleteMealType --> MealTypeRepository
    CheckMealTypeUsage --> MealTypeRepository
    CreateSystemMealTypes --> MealTypeRepository

    MatchRecipePreferences --> RecipeRepository
    MatchRecipePreferences --> PreferenceRepository
    MatchRecipePreferences --> PreferenceMatcher

    ExportRecipes --> RecipeRepository
    ExportRecipes --> EntityExporter

    ExportProducts --> ProductRepository
    ExportProducts --> EntityExporter

    ImportRecipes --> EntityImporter
    ImportRecipes --> RecipeRepository

    ImportProducts --> EntityImporter
    ImportProducts --> ProductRepository

    ManageCategory --> RecipeCategoryRepository
    ManageCategory --> ProductCategoryRepository
```

## Detailed Breakdown

### Base CRUD Classes
These abstract and concrete classes eliminate boilerplate across Recipe, Product, and FamilyMember domains:

- **CreateEntity** (abstract): Subclassed by CreateRecipe, CreateProduct, CreateFamilyMember
  - Requires `_build_entity()` override
  - `execute()` validates and saves entity

- **EditEntity** (abstract): Subclassed by EditRecipe, EditProduct, EditFamilyMember
  - Requires `_build_entity()` override
  - Ownership check via load_owned before saving

- **DeleteEntity**: Used directly as type alias (DeleteRecipe, DeleteProduct, etc.)
  - Verifies ownership before deletion
  - Accepts single ID or list

- **GetEntity**: Used as type alias for retrieval with ownership check

- **ListEntities**: Lists all entities or filter by category

- **PaginatedListEntities**: Supports pagination (page 25), search, and optional category filter
  - When page=None, returns full unfiltered list (for ingredient pickers)
  - When page provided, returns PAGE_SIZE items with offset and search applied

### Authentication Use Cases (7)
- **RegisterUser**: Creates user, default FamilyMember, system MealTypes
- **LoginUser**: Validates credentials, creates access+refresh token pair, stores refresh hash
- **RefreshAccessToken**: Validates refresh token, revokes old, issues new token pair
- **GetCurrentUser**: Validates access token, returns user
- **ChangePassword**: Verifies old password, hashes new one
- **UpdateProfile**: Updates nickname and/or password
- **LogoutUser**: Revokes refresh token

### Recipe Management Use Cases (6)
- **CreateRecipe**: Validates duplicate name, sub-recipe existence/ownership, cycles, depth
- **EditRecipe**: Same validation as create
- **GetRecipe**: Ownership check
- **DeleteRecipe**: Bulk delete with ownership filter
- **ListRecipes**: With optional category filter
- **PaginatedListRecipes**: Paginated with search

### Product Management Use Cases (6)
Same pattern as recipes

### Menu Planning Use Cases (8)
- **CreateMenu**: Creates new weekly menu
- **SaveMenu**: Persists menu state
- **LoadMenu**: Retrieves with ownership check
- **DeleteMenu**: Ownership-filtered deletion
- **ListMenus**: Lists user's menus
- **AddDishToSlot**: Upsert by day+meal_type_id+item_id, auto-position assignment
- **MoveSlotInMenu**: Atomic move with position shifting
- **RemoveItemFromSlot**: Delete specific slot item

### Shopping List Use Cases (5)
- **GenerateShoppingList**: Full aggregation from menu
- **GenerateFilteredShoppingList**: Subset of slots, with optional sub-recipe exclusions
- **GenerateAndSaveShoppingList**: Generates + persists as SavedShoppingList
- **LoadSavedShoppingList** / **ListSavedShoppingLists** / **DeleteSavedShoppingList**: CRUD saved lists
- **ExportShoppingList**: Serializes to bytes (CSV/JSON)

### Recipe Analysis Use Cases (4)
- **FlattenRecipeProducts**: Recursively resolves all products from recipe+sub-recipes
- **PreviewFlattenedProducts**: Frontend preview (no menu context)
- **ValidateSubRecipe**: Validates sub-recipe references (cycles, depth)
- **GenerateMealSummary**: Creates ingredient tree (IngredientNode hierarchy)

### Family & Preferences Use Cases
- **CreateFamilyMember**, **EditFamilyMember**, **DeleteFamilyMember**, **ListFamilyMembers**: CRUD
- **AssignPreferences**: Updates FamilyMember.preference_ids
- **CreatePreference**, **UpdatePreference**, **DeletePreference** (removes from all members), **ListPreferences**: CRUD
- **MatchRecipePreferences**: Returns matching preferences for recipe

### Meal Type Use Cases (6)
- **ListMealTypes**: Returns sorted by (time, sort_order, id)
- **CreateMealType**: Validates name, checks custom limit (max 10), auto-assigns sort_order
- **UpdateMealType**: Same validation, prevents duplicate names
- **DeleteMealType**: Prevents system type deletion
- **CheckMealTypeUsage**: Returns menus using this type
- **CreateSystemMealTypes**: Auto-creates Breakfast/Lunch/Dinner on signup

### Import/Export Use Cases
- **ExportRecipes/ExportProducts**: Serializes user's recipes/products via EntityExporter
- **ImportRecipes/ImportProducts**: Deserializes + upserts via EntityImporter

### Constants
- PAGE_SIZE = 25 (for pagination)
- REFRESH_TOKEN_DAYS = 30
- SYSTEM_MEAL_TYPES = [(name, time, sort_order), ...] (3 hardcoded types)
- MealType.MAX_CUSTOM_PER_USER = 10
- MealType.MAX_NAME_LENGTH = 50
