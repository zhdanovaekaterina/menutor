# Domain Layer — Detailed Class Diagram

```mermaid
classDiagram
    %% === ENTITIES ===
    class User {
        -id: UserId
        -email: str
        -nickname: str
        -hashed_password: str
        -created_at: datetime
        -last_login_at: datetime | None
    }

    class Recipe {
        -id: RecipeId
        -name: str
        -servings: int
        -ingredients: list[RecipeIngredient]
        -steps: list[CookingStep]
        -category_id: RecipeCategoryId
        -weight: int
        -user_id: UserId
        -total_pieces: int | None
        -pieces_per_portion: int | None
        -link: str | None
        -comment: str | None
        +__post_init__() None
        +is_pieces_mode: bool
        +computed_servings: int
        +scale_to(target_servings: float) Recipe
    }

    class Product {
        -id: ProductId
        -name: str
        -recipe_unit: str
        -purchase_unit: str
        -price_per_purchase_unit: Money
        -brand: str
        -supplier: str
        -conversion_factor: float
        -category_id: ProductCategoryId
        -user_id: UserId
        +compute_purchase(recipe_amount: float) tuple[Quantity, Money]
        +purchase_cost(purchase_amount: float) Money
    }

    class FamilyMember {
        -id: FamilyMemberId
        -name: str
        -portion_multiplier: float
        -comment: str
        -user_id: UserId
        -preference_ids: list[PreferenceId]
        +effective_servings(base_servings: float) float
    }

    class WeeklyMenu {
        -id: MenuId
        -name: str
        -slots: list[MenuSlot]
        -user_id: UserId
        +add_or_replace_slot(slot: MenuSlot) None
        +move_slot(day: int, meal_type_id: MealTypeId, recipe_id: RecipeId | None, product_id: ProductId | None, to_day: int, to_meal_type_id: MealTypeId, to_position: int, position: int | None) None
        +remove_item(day: int, meal_type_id: MealTypeId, recipe_id: RecipeId | None, product_id: ProductId | None, position: int | None) None
        +clear_slots() None
        -_same_item(existing: MenuSlot, new: MenuSlot) bool
    }

    class MenuSlot {
        -day: int
        -meal_type_id: MealTypeId
        -recipe_id: RecipeId | None
        -product_id: ProductId | None
        -quantity: float | None
        -unit: str | None
        -servings_override: float | None
        -pieces_override: int | None
        -position: int
        -member_ids: list[FamilyMemberId]
        +__post_init__() None
    }

    class ShoppingList {
        -items: list[ShoppingListItem]
        +total_cost() Money
        +items_by_category() dict[str, list[ShoppingListItem]]
    }

    class ShoppingListItem {
        -product_id: ProductId
        -product_name: str
        -category: str
        -quantity: Quantity
        -cost: Money
        -purchased: bool
        -recipe_quantity: Quantity | None
        +buy_quantity: Quantity
    }

    class SavedShoppingList {
        -id: SavedShoppingListId
        -user_id: UserId
        -name: str
        -items: list[SavedShoppingListItem]
        -source_menu_id: MenuId | None
        -created_at: datetime
        -updated_at: datetime
        +total_cost() Money
        +items_by_category() dict[str, list[SavedShoppingListItem]]
    }

    class SavedShoppingListItem {
        -id: SavedShoppingListItemId
        -product_id: ProductId | None
        -product_name: str
        -category: str
        -quantity: Quantity
        -buy_quantity: Quantity
        -buy_quantity_overridden: bool
        -cost: Money
        -purchased: bool
        -recipe_quantity: Quantity | None
        -item_order: int
    }

    class RefreshToken {
        -id: RefreshTokenId
        -user_id: UserId
        -token_hash: str
        -expires_at: datetime
        -revoked: bool
    }

    class Preference {
        -id: PreferenceId
        -name: str
        -type: PreferenceType
        -mode: PreferenceMode
        -category_ids: list[ProductCategoryId]
        -product_ids: list[ProductId]
        -recipe_category_ids: list[RecipeCategoryId]
        -user_id: UserId
        +__post_init__() None
    }

    class MealType {
        -id: MealTypeId
        -user_id: UserId
        -name: str
        -time: time
        -is_system: bool
        -sort_order: int
        +MAX_CUSTOM_PER_USER: int
        +MAX_NAME_LENGTH: int
    }

    %% === VALUE OBJECTS ===
    class Quantity {
        -amount: float
        -unit: str
        -_UNIT_GROUPS: dict[str, str]
        -_TO_BASE: dict[str, float]
        +__post_init__() None
        +convert_to(target_unit: str) Quantity
        +is_weight: bool
        +__add__(other: Quantity) Quantity
    }

    class Money {
        -amount: Decimal
        -currency: str
        +__add__(other: Money) Money
        +__mul__(factor: float) Money
    }

    class RecipeIngredient {
        -product_id: ProductId | None
        -sub_recipe_id: RecipeId | None
        -quantity: Quantity
        -order: int
        +__post_init__() None
        +is_sub_recipe: bool
        +is_product: bool
    }

    class CookingStep {
        -order: int
        -description: str
    }

    class ActiveCategory {
        -id: int
        -name: str
        -color: str | None
    }

    class Category {
        -id: int
        -name: str
        -active: bool
        -color: str | None
    }

    class PreferenceType {
        <<enumeration>>
        CATEGORY_BASED
        ALLERGY
    }

    class PreferenceMode {
        <<enumeration>>
        BLOCKED
        ALLOWED
    }

    class ImportResult {
        -created: int
        -updated: int
        -errors: list[str]
    }

    %% === REPOSITORY PORTS ===
    class UserRepository {
        <<interface>>
        +get_by_id(id: UserId) User | None
        +get_by_email(email: str) User | None
        +save(user: User) User
    }

    class RecipeRepository {
        <<interface>>
        +get_by_id(id: RecipeId) Recipe | None
        +find_by_category_id(category_id: RecipeCategoryId, user_id: UserId) list[Recipe]
        +find_all(user_id: UserId) list[Recipe]
        +count(user_id: UserId, search: str, category_id: RecipeCategoryId | None) int
        +find_page(user_id: UserId, search: str, limit: int, offset: int, category_id: RecipeCategoryId | None) list[Recipe]
        +save(recipe: Recipe) Recipe
        +delete(ids: list[RecipeId]) None
        +find_parents_of(sub_recipe_id: RecipeId, user_id: UserId) list[Recipe]
        +find_by_name(name: str, user_id: UserId) Recipe | None
    }

    class ProductRepository {
        <<interface>>
        +get_by_id(id: ProductId) Product | None
        +find_by_category_id(category_id: ProductCategoryId, user_id: UserId) list[Product]
        +find_all(user_id: UserId) list[Product]
        +count(user_id: UserId, search: str, category_id: ProductCategoryId | None) int
        +find_page(user_id: UserId, search: str, limit: int, offset: int, category_id: ProductCategoryId | None) list[Product]
        +save(product: Product) Product
        +delete(ids: list[ProductId]) None
        +find_linked_ids(ids: list[ProductId]) list[ProductId]
        +find_by_name(name: str, user_id: UserId) Product | None
    }

    class MenuRepository {
        <<interface>>
        +get_by_id(id: MenuId) WeeklyMenu | None
        +find_all(user_id: UserId) list[WeeklyMenu]
        +save(menu: WeeklyMenu) WeeklyMenu
        +delete(ids: list[MenuId]) None
    }

    class FamilyMemberRepository {
        <<interface>>
        +get_by_id(id: FamilyMemberId) FamilyMember | None
        +find_all(user_id: UserId) list[FamilyMember]
        +save(member: FamilyMember) FamilyMember
        +delete(ids: list[FamilyMemberId]) None
    }

    class CategoryRepository {
        <<interface>>
        +find_active() list[ActiveCategory]
        +find_all() list[Category]
        +save(name: str, category_id: int | None, color: str | None) int
        +delete(category_id: int) None
        +hard_delete(category_id: int) None
        +activate(category_id: int) None
        +is_used(category_id: int) bool
        +move_and_delete(from_id: int, to_id: int) None
    }

    class RecipeCategoryRepository {
        <<interface>>
    }

    class ProductCategoryRepository {
        <<interface>>
    }

    class RefreshTokenRepository {
        <<interface>>
        +save(token: RefreshToken) RefreshToken
        +get_by_token_hash(token_hash: str) RefreshToken | None
        +revoke(token_hash: str) None
        +revoke_all_for_user(user_id: UserId) None
    }

    class SavedShoppingListRepository {
        <<interface>>
        +save(shopping_list: SavedShoppingList) SavedShoppingList
        +get_by_id(id: SavedShoppingListId) SavedShoppingList | None
        +find_all(user_id: UserId) list[SavedShoppingList]
        +delete(ids: list[SavedShoppingListId]) None
    }

    class PreferenceRepository {
        <<interface>>
        +get_by_id(id: PreferenceId) Preference | None
        +find_all(user_id: UserId) list[Preference]
        +find_by_ids(ids: list[PreferenceId], user_id: UserId) list[Preference]
        +find_by_name(name: str, user_id: UserId) Preference | None
        +save(preference: Preference) Preference
        +delete(ids: list[PreferenceId]) None
    }

    class MealTypeRepository {
        <<interface>>
        +get_by_id(id: MealTypeId) MealType | None
        +find_all(user_id: UserId) list[MealType]
        +find_by_name(user_id: UserId, name: str) MealType | None
        +count_custom(user_id: UserId) int
        +save(meal_type: MealType) MealType
        +delete(ids: list[MealTypeId]) None
        +get_usage(meal_type_id: MealTypeId) list[tuple[int, str]]
    }

    class EntityExporter {
        <<protocol>>
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class EntityImporter {
        <<protocol>>
        +import_from_bytes(data: bytes, user_id: UserId) ImportResult
        +supported_extensions() list[str]
    }

    %% === DOMAIN SERVICES ===
    class PasswordHasher {
        <<interface>>
        +hash(password: str) str
        +verify(password: str, hashed: str) bool
    }

    class TokenService {
        <<interface>>
        +create_access_token(user_id: UserId) str
        +create_refresh_token(user_id: UserId) str
        +validate_access_token(token: str) UserId | None
        +get_refresh_token_hash(token: str) str
    }

    class PortionCalculator {
        +total_servings(base_servings: float, members: list[FamilyMember]) float
    }

    class UnitConverter {
        +convert(quantity: Quantity, target_unit: str) Quantity
    }

    class RecipeDependencyValidator {
        -_repo: RecipeRepository
        +__init__(recipe_repo: RecipeRepository) None
        +validate(recipe_id: RecipeId, sub_recipe_ids: list[RecipeId]) None
        -_dfs(current_id: RecipeId, visited: set[RecipeId], depth: int) None
        +compute_depth(recipe_id: RecipeId) int
        -_compute_depth_recursive(recipe: Recipe, visited: set[RecipeId], current_depth: int) int
    }

    class ShoppingListBuilder {
        -_recipe_repo: RecipeRepository
        -_product_repo: ProductRepository
        -_product_category_repo: ProductCategoryRepository
        -_portion_calc: PortionCalculator
        -_unit_converter: UnitConverter
        +__init__(recipe_repo: RecipeRepository, product_repo: ProductRepository, product_category_repo: ProductCategoryRepository, portion_calc: PortionCalculator, unit_converter: UnitConverter) None
        +build(menu: WeeklyMenu) ShoppingList
        -_aggregated_to_shopping_list(aggregated: dict[ProductId, Quantity]) ShoppingList
        -_resolve_recipe_products(recipe: Recipe, scale_factor: float, visited: set[RecipeId], _excluded_sub_recipe_ids: set[RecipeId] | None) dict[ProductId, Quantity]
        +flatten_recipe_products(recipe: Recipe) dict[ProductId, Quantity]
        +build_filtered(menu: WeeklyMenu, slot_indices: set[int], excluded_sub_recipe_ids: set[RecipeId] | None) ShoppingList
        +resolve_recipe_ingredients_tree(recipe: Recipe, scale_factor: float, visited: set[RecipeId] | None) list[IngredientNode]
    }

    class PreferenceMatcher {
        -_recipe_repo: RecipeRepository
        -_product_repo: ProductRepository
        +__init__(recipe_repo: RecipeRepository, product_repo: ProductRepository) None
        +matches_preference(recipe: Recipe, preference: Preference) bool
        +match_all(recipe: Recipe, preferences: list[Preference]) list[Preference]
        -_resolve_all_product_ids(recipe: Recipe, visited: set[RecipeId]) set[ProductId]
        -_resolve_all_recipe_category_ids(recipe: Recipe, visited: set[RecipeId]) tuple[set[RecipeCategoryId], bool]
        -_resolve_category_ids(product_ids: set[ProductId]) tuple[set[ProductCategoryId], bool]
        +_matches_allergy(product_ids: set[ProductId], product_category_ids: set[ProductCategoryId], recipe_category_ids: set[RecipeCategoryId], preference: Preference) bool
        +_matches_blocked(product_category_ids: set[ProductCategoryId], recipe_category_ids: set[RecipeCategoryId], preference: Preference) bool
        +_matches_allowed(product_ids: set[ProductId], product_category_ids: set[ProductCategoryId], recipe_category_ids: set[RecipeCategoryId], preference: Preference, has_uncategorized_product: bool, has_uncategorized_recipe: bool) bool
    }

    class IngredientNode {
        -product_id: ProductId | None
        -product_name: str
        -quantity_amount: float
        -quantity_unit: str
        -sub_recipe_id: RecipeId | None
        -sub_recipe_name: str | None
        -children: list[IngredientNode]
    }

    %% === TYPE DEFINITIONS ===
    note "Type Aliases (NewType):\nRecipeId, ProductId, MenuId, FamilyMemberId,\nProductCategoryId, RecipeCategoryId, UserId,\nRefreshTokenId, SavedShoppingListId,\nSavedShoppingListItemId, PreferenceId, MealTypeId"

    %% === RELATIONSHIPS ===
    Recipe --> "1..*" RecipeIngredient : has
    Recipe --> "0..*" CookingStep : steps
    Recipe --> RecipeCategoryId : uses
    Recipe --> UserId : belongs_to

    Product --> Money : has
    Product --> ProductCategoryId : categorized_by
    Product --> UserId : belongs_to

    MenuSlot --> MealTypeId : references
    MenuSlot --> RecipeId : can_reference
    MenuSlot --> ProductId : can_reference
    MenuSlot --> "0..*" FamilyMemberId : for_members

    WeeklyMenu --> "0..*" MenuSlot : contains
    WeeklyMenu --> UserId : belongs_to

    ShoppingList --> "0..*" ShoppingListItem : contains
    ShoppingListItem --> ProductId : is_for
    ShoppingListItem --> Money : has_cost
    ShoppingListItem --> Quantity : has_quantity

    SavedShoppingList --> "0..*" SavedShoppingListItem : contains
    SavedShoppingList --> UserId : belongs_to
    SavedShoppingList --> MenuId : from
    SavedShoppingListItem --> ProductId : is_for
    SavedShoppingListItem --> Money : has_cost
    SavedShoppingListItem --> Quantity : has_quantity

    FamilyMember --> UserId : belongs_to
    FamilyMember --> "0..*" PreferenceId : has

    RefreshToken --> UserId : belongs_to

    Preference --> PreferenceType : has
    Preference --> PreferenceMode : has
    Preference --> UserId : belongs_to
    Preference --> "0..*" ProductCategoryId : can_reference
    Preference --> "0..*" ProductId : can_reference
    Preference --> "0..*" RecipeCategoryId : can_reference

    MealType --> UserId : belongs_to

    RecipeIngredient --> ProductId : can_reference
    RecipeIngredient --> RecipeId : can_reference
    RecipeIngredient --> Quantity : has

    IngredientNode --> ProductId : can_reference
    IngredientNode --> RecipeId : can_reference
    IngredientNode --> Quantity : has
    IngredientNode --> "0..*" IngredientNode : has_children

    RecipeCategoryRepository --|> CategoryRepository : extends
    ProductCategoryRepository --|> CategoryRepository : extends

    RecipeDependencyValidator --> RecipeRepository : depends_on
    ShoppingListBuilder --> RecipeRepository : depends_on
    ShoppingListBuilder --> ProductRepository : depends_on
    ShoppingListBuilder --> ProductCategoryRepository : depends_on
    ShoppingListBuilder --> PortionCalculator : depends_on
    ShoppingListBuilder --> UnitConverter : depends_on
    ShoppingListBuilder --> IngredientNode : creates

    PreferenceMatcher --> RecipeRepository : depends_on
    PreferenceMatcher --> ProductRepository : depends_on
```

## Detailed Breakdown

### Entities (dataclass)
- **User**: User account with email, nickname, password hash, login timestamps
- **Recipe**: Recipe with ingredients (products or sub-recipes), cooking steps, scaling capabilities (servings or pieces mode)
- **Product**: Product with recipe/purchase units, price, conversion factor
- **FamilyMember**: Family member with portion multiplier and dietary preferences
- **WeeklyMenu**: Weekly meal plan with slots for 7 days × meal types
- **MenuSlot**: Single meal plan cell (day, meal type) with recipe or product, optional member targeting
- **ShoppingList**: Ephemeral shopping list with aggregated quantities and costs
- **SavedShoppingList**: Persistent shopping list linked to menu, with individual items
- **RefreshToken**: JWT refresh token with hash and expiration
- **Preference**: Dietary/lifestyle preference (allergy, blocked category, allowed products)
- **MealType**: Meal type (breakfast, lunch, dinner, custom) with time and ordering

### Value Objects (dataclass or NamedTuple, frozen)
- **Quantity**: Amount + unit with conversion logic
- **Money**: Decimal amount + currency with arithmetic
- **RecipeIngredient**: Reference to product or sub-recipe with quantity
- **CookingStep**: Order + description
- **Category/ActiveCategory**: Category with active flag and color
- **PreferenceType/PreferenceMode**: Enumerations
- **ImportResult**: Count of created/updated entities + error messages

### Repository Ports (Abstract interfaces)
8 abstract repositories define the persistence contract:
- **UserRepository**: CRUD for users
- **RecipeRepository**: CRUD + search + parent/child queries for recipes
- **ProductRepository**: CRUD + search + link detection for products
- **MenuRepository**: CRUD for weekly menus
- **FamilyMemberRepository**: CRUD for family members
- **CategoryRepository**: CRUD + activation + move/delete for categories (abstract)
- **RecipeCategoryRepository/ProductCategoryRepository**: Type-safe marker subclasses
- **RefreshTokenRepository**: Token save/revoke operations
- **SavedShoppingListRepository**: CRUD for saved lists
- **PreferenceRepository**: CRUD + search for preferences
- **MealTypeRepository**: CRUD + usage checking for meal types

### Service Protocols & Interfaces
- **PasswordHasher**: Abstract interface for password hashing (bcrypt/argon2)
- **TokenService**: Abstract interface for JWT token creation/validation
- **EntityExporter/EntityImporter**: Protocols for serialization/import (CSV/JSON/etc)

### Domain Services (concrete)
- **PortionCalculator**: Sums portion multipliers across family members
- **UnitConverter**: Delegates unit conversion to Quantity
- **RecipeDependencyValidator**: DFS cycle detection + nesting depth validation (max 5 levels)
- **ShoppingListBuilder**: Complex aggregation logic: recipe flattening, ingredient tree resolution, filtered shopping lists
- **PreferenceMatcher**: Recursive preference matching (allergies, blocked categories, allowed lists)

### Key Invariants & Validations
- **MenuSlot**: Exactly one of recipe_id or product_id
- **RecipeIngredient**: Exactly one of product_id or sub_recipe_id
- **Recipe**: If pieces_mode enabled, total_pieces >= 1 and pieces_per_portion <= total_pieces
- **Preference**: Allergies always BLOCKED mode; category-based prefs don't have individual products
- **RecipeDependencyValidator**: No circular dependencies; max nesting 5 levels
