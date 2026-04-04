# Infrastructure Layer — Detailed Class Diagram

```mermaid
classDiagram
    %% === AUTHENTICATION IMPLEMENTATIONS ===
    class BcryptPasswordHasher {
        +hash(password: str) str
        +verify(password: str, hashed: str) bool
    }

    class JwtTokenService {
        -_secret: str
        +__init__(secret_key: str) None
        +create_access_token(user_id: UserId) str
        +create_refresh_token(user_id: UserId) str
        +validate_access_token(token: str) UserId | None
        +get_refresh_token_hash(token: str) str
    }

    %% === DATABASE MODELS (ORM) ===
    class Base {
        <<declarative_base>>
    }

    class UserRow {
        -id: int (PK)
        -email: str (UNIQUE)
        -nickname: str
        -hashed_password: str
        -created_at: datetime
        -last_login_at: datetime | None
        -refresh_tokens: relationship[RefreshTokenRow]
    }

    class RefreshTokenRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -token_hash: str (UNIQUE)
        -expires_at: datetime
        -revoked: bool
        -user: relationship[UserRow]
    }

    class UnitRow {
        -name: str (PK)
        -unit_group: str
    }

    class RecipeCategoryRow {
        -id: int (PK)
        -name: str (UNIQUE)
        -active: int
        -color: str(7) | None
    }

    class ProductCategoryRow {
        -id: int (PK)
        -name: str (UNIQUE)
        -active: int
        -color: str(7) | None
    }

    class ProductRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -name: str
        -category_id: int (FK → product_categories.id)
        -brand: str
        -supplier: str
        -recipe_unit: str (FK → units.name)
        -purchase_unit: str (FK → units.name)
        -price_per_purchase_unit: float
        -conversion_factor: float
    }

    class RecipeRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -name: str
        -category_id: int (FK → recipe_categories.id)
        -dietary_tags: str (JSON)
        -servings: int
        -weight: int
        -total_pieces: int | None
        -pieces_per_portion: int | None
        -link: str | None
        -comment: str | None
        -ingredients: relationship[RecipeIngredientRow]
        -steps: relationship[CookingStepRow]
    }

    class RecipeIngredientRow {
        -id: int (PK)
        -recipe_id: int (FK → recipes.id, CASCADE)
        -product_id: int | None (FK → products.id)
        -sub_recipe_id: int | None (FK → recipes.id, SET NULL)
        -amount: float
        -unit: str (FK → units.name)
        -ingredient_order: int
    }

    class CookingStepRow {
        -id: int (PK)
        -recipe_id: int (FK → recipes.id, CASCADE)
        -step_order: int
        -description: str
    }

    class FamilyMemberRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -name: str
        -portion_multiplier: float
        -comment: str
        -preference_ids: str (JSON list)
    }

    class MenuRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -name: str
        -menu_slots: relationship[MenuSlotRow]
    }

    class MenuSlotRow {
        -id: int (PK)
        -menu_id: int (FK → menus.id, CASCADE)
        -day: int (0-6)
        -meal_type_id: int (FK → meal_types.id)
        -recipe_id: int | None (FK → recipes.id)
        -product_id: int | None (FK → products.id)
        -quantity: float | None
        -unit: str | None
        -servings_override: float | None
        -pieces_override: int | None
        -slot_position: int
        -member_ids: str (JSON list)
    }

    class SavedShoppingListRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -name: str
        -source_menu_id: int | None (FK → menus.id)
        -created_at: datetime
        -updated_at: datetime
        -items: relationship[SavedShoppingListItemRow]
    }

    class SavedShoppingListItemRow {
        -id: int (PK)
        -saved_shopping_list_id: int (FK → saved_shopping_lists.id, CASCADE)
        -product_id: int | None (FK → products.id)
        -product_name: str
        -category: str
        -quantity_amount: float
        -quantity_unit: str
        -buy_quantity_amount: float
        -buy_quantity_unit: str
        -buy_quantity_overridden: bool
        -cost_amount: float
        -cost_currency: str
        -purchased: bool
        -recipe_quantity_amount: float | None
        -recipe_quantity_unit: str | None
        -item_order: int
    }

    class PreferenceRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -name: str
        -type: str (CATEGORY_BASED | ALLERGY)
        -mode: str (BLOCKED | ALLOWED)
        -category_ids: str (JSON list)
        -product_ids: str (JSON list)
        -recipe_category_ids: str (JSON list)
    }

    class MealTypeRow {
        -id: int (PK)
        -user_id: int (FK → users.id, CASCADE)
        -name: str
        -time: time
        -is_system: bool
        -sort_order: int
    }

    %% === REPOSITORY BASE ===
    class BaseOrmRepository~E,I~ {
        <<abstract>>
        -_session: Session
        -_row_class: Any
        +__init__(session: Session) None
        +_get_entity_id(entity: E) int
        +_wrap_id(raw_id: int) I
        +_make_new_row(entity: E) Any
        +_update_row(row: Any, entity: E) None
        +_row_to_entity(row: Any) E
        +save(entity: E) E
        +delete(ids: list[I]) None
        +get_by_id(id: I) E | None
        +find_all(user_id: UserId) list[E]
    }

    class BaseCategoryRepository {
        <<abstract>>
        -_session: Session
        -_row_class: Any
        +find_active() list[ActiveCategory]
        +find_all() list[Category]
        +save(name: str, category_id: int | None, color: str | None) int
        +delete(category_id: int) None
        +hard_delete(category_id: int) None
        +activate(category_id: int) None
        +is_used(category_id: int) bool
        +move_and_delete(from_id: int, to_id: int) None
    }

    %% === REPOSITORY IMPLEMENTATIONS ===
    class OrmUserRepository {
        -_session: Session
        -_row_class: UserRow
        +__init__(session: Session) None
        +_get_entity_id(entity: User) int
        +_wrap_id(raw_id: int) UserId
        +_make_new_row(entity: User) UserRow
        +_update_row(row: UserRow, entity: User) None
        +_row_to_entity(row: UserRow) User
        +get_by_id(id: UserId) User | None
        +get_by_email(email: str) User | None
        +find_all(user_id: UserId) list[User]
        +save(user: User) User
        +delete(ids: list[UserId]) None
    }

    class OrmRecipeRepository {
        -_session: Session
        -_row_class: RecipeRow
        +__init__(session: Session) None
        +_get_entity_id(entity: Recipe) int
        +_wrap_id(raw_id: int) RecipeId
        +_make_new_row(entity: Recipe) RecipeRow
        +_update_row(row: RecipeRow, entity: Recipe) None
        +_row_to_entity(row: RecipeRow) Recipe
        -_ingredients_to_rows(ingredients: list[RecipeIngredient]) list[RecipeIngredientRow]
        -_steps_to_rows(steps: list[CookingStep]) list[CookingStepRow]
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

    class OrmProductRepository {
        -_session: Session
        -_row_class: ProductRow
        +__init__(session: Session) None
        +_get_entity_id(entity: Product) int
        +_wrap_id(raw_id: int) ProductId
        +_make_new_row(entity: Product) ProductRow
        +_update_row(row: ProductRow, entity: Product) None
        +_row_to_entity(row: ProductRow) Product
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

    class OrmMenuRepository {
        -_session: Session
        -_row_class: MenuRow
        +__init__(session: Session) None
        +_get_entity_id(entity: WeeklyMenu) int
        +_wrap_id(raw_id: int) MenuId
        +_make_new_row(entity: WeeklyMenu) MenuRow
        +_update_row(row: MenuRow, entity: WeeklyMenu) None
        +_row_to_entity(row: MenuRow) WeeklyMenu
        -_slots_to_rows(slots: list[MenuSlot]) list[MenuSlotRow]
        +get_by_id(id: MenuId) WeeklyMenu | None
        +find_all(user_id: UserId) list[WeeklyMenu]
        +save(menu: WeeklyMenu) WeeklyMenu
        +delete(ids: list[MenuId]) None
    }

    class OrmFamilyMemberRepository {
        -_session: Session
        -_row_class: FamilyMemberRow
        +__init__(session: Session) None
        +_get_entity_id(entity: FamilyMember) int
        +_wrap_id(raw_id: int) FamilyMemberId
        +_make_new_row(entity: FamilyMember) FamilyMemberRow
        +_update_row(row: FamilyMemberRow, entity: FamilyMember) None
        +_row_to_entity(row: FamilyMemberRow) FamilyMember
        +get_by_id(id: FamilyMemberId) FamilyMember | None
        +find_all(user_id: UserId) list[FamilyMember]
        +save(member: FamilyMember) FamilyMember
        +delete(ids: list[FamilyMemberId]) None
    }

    class OrmRecipeCategoryRepository {
        <<extends BaseCategoryRepository>>
        -_row_class: RecipeCategoryRow
    }

    class OrmProductCategoryRepository {
        <<extends BaseCategoryRepository>>
        -_row_class: ProductCategoryRow
    }

    class OrmRefreshTokenRepository {
        -_session: Session
        +__init__(session: Session) None
        +save(token: RefreshToken) RefreshToken
        +get_by_token_hash(token_hash: str) RefreshToken | None
        +revoke(token_hash: str) None
        +revoke_all_for_user(user_id: UserId) None
    }

    class OrmSavedShoppingListRepository {
        -_session: Session
        -_row_class: SavedShoppingListRow
        +__init__(session: Session) None
        +_get_entity_id(entity: SavedShoppingList) int
        +_wrap_id(raw_id: int) SavedShoppingListId
        +_make_new_row(entity: SavedShoppingList) SavedShoppingListRow
        +_update_row(row: SavedShoppingListRow, entity: SavedShoppingList) None
        +_row_to_entity(row: SavedShoppingListRow) SavedShoppingList
        +save(shopping_list: SavedShoppingList) SavedShoppingList
        +get_by_id(id: SavedShoppingListId) SavedShoppingList | None
        +find_all(user_id: UserId) list[SavedShoppingList]
        +delete(ids: list[SavedShoppingListId]) None
    }

    class OrmPreferenceRepository {
        -_session: Session
        -_row_class: PreferenceRow
        +__init__(session: Session) None
        +_get_entity_id(entity: Preference) int
        +_wrap_id(raw_id: int) PreferenceId
        +_make_new_row(entity: Preference) PreferenceRow
        +_update_row(row: PreferenceRow, entity: Preference) None
        +_row_to_entity(row: PreferenceRow) Preference
        +get_by_id(id: PreferenceId) Preference | None
        +find_all(user_id: UserId) list[Preference]
        +find_by_ids(ids: list[PreferenceId], user_id: UserId) list[Preference]
        +find_by_name(name: str, user_id: UserId) Preference | None
        +save(preference: Preference) Preference
        +delete(ids: list[PreferenceId]) None
    }

    class OrmMealTypeRepository {
        -_session: Session
        -_row_class: MealTypeRow
        +__init__(session: Session) None
        +_get_entity_id(entity: MealType) int
        +_wrap_id(raw_id: int) MealTypeId
        +_make_new_row(entity: MealType) MealTypeRow
        +_update_row(row: MealTypeRow, entity: MealType) None
        +_row_to_entity(row: MealTypeRow) MealType
        +get_by_id(id: MealTypeId) MealType | None
        +find_all(user_id: UserId) list[MealType]
        +find_by_name(user_id: UserId, name: str) MealType | None
        +count_custom(user_id: UserId) int
        +save(meal_type: MealType) MealType
        +delete(ids: list[MealTypeId]) None
        +get_usage(meal_type_id: MealTypeId) list[tuple[int, str]]
    }

    %% === EXPORT IMPLEMENTATIONS ===
    class ExportRegistry {
        -_exporters: dict[tuple[str, str], EntityExporter]
        +__init__() None
        +register(entity_type: str, format: str, exporter: EntityExporter) None
        +get(entity_type: str, format: str) EntityExporter | None
        +formats_for(entity_type: str) list[str]
    }

    class ShoppingListCsvExporter {
        -_write_rows(writer: csv.writer, shopping_list: ShoppingList) None
        +export(shopping_list: ShoppingList, filepath: str) None
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class ShoppingListJsonExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class ShoppingListPdfExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class RecipeCsvExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class RecipeJsonExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class ProductCsvExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class ProductJsonExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class MenuJsonExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    class MenuPdfExporter {
        +export_bytes(entities: list[Any]) bytes
        +example_bytes() bytes
        +content_type() str
        +file_extension() str
    }

    %% === IMPORT IMPLEMENTATIONS ===
    class ImportRegistry {
        -_importers: dict[tuple[str, str], EntityImporter]
        +__init__() None
        +register(entity_type: str, format: str, importer: EntityImporter) None
        +get(entity_type: str, format: str) EntityImporter | None
        +formats_for(entity_type: str) list[str]
    }

    class RecipeCsvImporter {
        -_repo: RecipeRepository
        -_category_repo: RecipeCategoryRepository
        +__init__(repo: RecipeRepository, category_repo: RecipeCategoryRepository) None
        +import_from_bytes(data: bytes, user_id: UserId) ImportResult
        +supported_extensions() list[str]
    }

    class RecipeJsonImporter {
        -_repo: RecipeRepository
        -_category_repo: RecipeCategoryRepository
        +__init__(repo: RecipeRepository, category_repo: RecipeCategoryRepository) None
        +import_from_bytes(data: bytes, user_id: UserId) ImportResult
        +supported_extensions() list[str]
    }

    class ProductCsvImporter {
        -_repo: ProductRepository
        -_category_repo: ProductCategoryRepository
        +__init__(repo: ProductRepository, category_repo: ProductCategoryRepository) None
        +import_from_bytes(data: bytes, user_id: UserId) ImportResult
        +supported_extensions() list[str]
    }

    class ProductJsonImporter {
        -_repo: ProductRepository
        -_category_repo: ProductCategoryRepository
        +__init__(repo: ProductRepository, category_repo: ProductCategoryRepository) None
        +import_from_bytes(data: bytes, user_id: UserId) ImportResult
        +supported_extensions() list[str]
    }

    class MenuJsonImporter {
        -_menu_repo: MenuRepository
        -_recipe_repo: RecipeRepository
        -_product_repo: ProductRepository
        -_meal_type_repo: MealTypeRepository
        +__init__(menu_repo: MenuRepository, recipe_repo: RecipeRepository, product_repo: ProductRepository, meal_type_repo: MealTypeRepository) None
        +import_from_bytes(data: bytes, user_id: UserId) ImportResult
        +supported_extensions() list[str]
    }

    %% === DATABASE CONNECTION ===
    class DatabaseConnection {
        <<utility>>
        +get_engine(db_url: str) Engine
        -_is_sqlite(engine: Engine) bool
        -_run_sqlite_migrations(engine: Engine) bool
        -_restore_sqlite_menu_slots_backup(engine: Engine) None
        +apply_schema(engine: Engine) None
        +seed_defaults(session: Session) None
        -_seed_defaults_sqlite(session: Session) None
        -_seed_defaults_pg(session: Session) None
    }

    %% === RELATIONSHIPS ===
    BcryptPasswordHasher ..|> PasswordHasher : implements
    JwtTokenService ..|> TokenService : implements

    Base <|-- UserRow
    Base <|-- RefreshTokenRow
    Base <|-- UnitRow
    Base <|-- RecipeCategoryRow
    Base <|-- ProductCategoryRow
    Base <|-- ProductRow
    Base <|-- RecipeRow
    Base <|-- RecipeIngredientRow
    Base <|-- CookingStepRow
    Base <|-- FamilyMemberRow
    Base <|-- MenuRow
    Base <|-- MenuSlotRow
    Base <|-- SavedShoppingListRow
    Base <|-- SavedShoppingListItemRow
    Base <|-- PreferenceRow
    Base <|-- MealTypeRow

    UserRow --> RefreshTokenRow : has

    OrmUserRepository --|> BaseOrmRepository
    OrmRecipeRepository --|> BaseOrmRepository
    OrmProductRepository --|> BaseOrmRepository
    OrmMenuRepository --|> BaseOrmRepository
    OrmFamilyMemberRepository --|> BaseOrmRepository
    OrmSavedShoppingListRepository --|> BaseOrmRepository
    OrmPreferenceRepository --|> BaseOrmRepository
    OrmMealTypeRepository --|> BaseOrmRepository

    OrmRecipeCategoryRepository --|> BaseCategoryRepository
    OrmProductCategoryRepository --|> BaseCategoryRepository

    OrmUserRepository ..|> UserRepository : implements
    OrmRecipeRepository ..|> RecipeRepository : implements
    OrmProductRepository ..|> ProductRepository : implements
    OrmMenuRepository ..|> MenuRepository : implements
    OrmFamilyMemberRepository ..|> FamilyMemberRepository : implements
    OrmRecipeCategoryRepository ..|> RecipeCategoryRepository : implements
    OrmProductCategoryRepository ..|> ProductCategoryRepository : implements
    OrmRefreshTokenRepository ..|> RefreshTokenRepository : implements
    OrmSavedShoppingListRepository ..|> SavedShoppingListRepository : implements
    OrmPreferenceRepository ..|> PreferenceRepository : implements
    OrmMealTypeRepository ..|> MealTypeRepository : implements

    ExportRegistry --> ShoppingListCsvExporter : uses
    ExportRegistry --> ShoppingListJsonExporter : uses
    ExportRegistry --> ShoppingListPdfExporter : uses
    ExportRegistry --> RecipeCsvExporter : uses
    ExportRegistry --> RecipeJsonExporter : uses
    ExportRegistry --> ProductCsvExporter : uses
    ExportRegistry --> ProductJsonExporter : uses
    ExportRegistry --> MenuJsonExporter : uses
    ExportRegistry --> MenuPdfExporter : uses

    ImportRegistry --> RecipeCsvImporter : uses
    ImportRegistry --> RecipeJsonImporter : uses
    ImportRegistry --> ProductCsvImporter : uses
    ImportRegistry --> ProductJsonImporter : uses
    ImportRegistry --> MenuJsonImporter : uses

    ShoppingListCsvExporter ..|> EntityExporter : implements
    ShoppingListJsonExporter ..|> EntityExporter : implements
    ShoppingListPdfExporter ..|> EntityExporter : implements
    RecipeCsvExporter ..|> EntityExporter : implements
    RecipeJsonExporter ..|> EntityExporter : implements
    ProductCsvExporter ..|> EntityExporter : implements
    ProductJsonExporter ..|> EntityExporter : implements
    MenuJsonExporter ..|> EntityExporter : implements
    MenuPdfExporter ..|> EntityExporter : implements

    RecipeCsvImporter ..|> EntityImporter : implements
    RecipeJsonImporter ..|> EntityImporter : implements
    ProductCsvImporter ..|> EntityImporter : implements
    ProductJsonImporter ..|> EntityImporter : implements
    MenuJsonImporter ..|> EntityImporter : implements

    RecipeCsvImporter --> RecipeRepository : depends_on
    RecipeJsonImporter --> RecipeRepository : depends_on
    ProductCsvImporter --> ProductRepository : depends_on
    ProductJsonImporter --> ProductRepository : depends_on
    MenuJsonImporter --> MenuRepository : depends_on
```

## Detailed Breakdown

### Authentication Service Implementations
- **BcryptPasswordHasher**: bcrypt.hashpw() for hashing, bcrypt.checkpw() for verify
- **JwtTokenService**: 
  - Access tokens: HS256 with 30min expiry (configurable)
  - Refresh tokens: URL-safe 64-byte random token
  - Token hash: SHA256 for secure storage

### ORM Models (16 classes)
- **UserRow**: user accounts with refresh token relationship
- **RefreshTokenRow**: hashed tokens with expiration and revocation flag
- **UnitRow**: unit definitions (g, kg, ml, l, tsp, tbsp, pcs, box, pack, serv)
- **RecipeCategoryRow** / **ProductCategoryRow**: categories with active flag and color
- **ProductRow**: products with units and pricing
- **RecipeRow** + **RecipeIngredientRow** + **CookingStepRow**: recipes with ingredients and steps
- **FamilyMemberRow**: family members with JSON-serialized preference IDs
- **MenuRow** + **MenuSlotRow**: menus with slots (day, meal_type, recipe/product, overrides, member_ids as JSON)
- **SavedShoppingListRow** + **SavedShoppingListItemRow**: persistent shopping lists with JSON quantity/cost storage
- **PreferenceRow**: preferences with JSON arrays for category/product IDs
- **MealTypeRow**: meal types with time and ordering

### Base Repository
**BaseOrmRepository[E, I]** generic template reduces boilerplate 8x:
- Abstract methods: _get_entity_id(), _wrap_id(), _make_new_row(), _update_row(), _row_to_entity()
- Shared save(): insert or update with flush+commit
- Shared delete(): bulk deletion with transaction
- Shared get_by_id() / find_all(): basic queries

### Repository Implementations (11)
Each repository implements domain port interface:
- **OrmUserRepository**: get_by_email() for login
- **OrmRecipeRepository**: find_parents_of() for cycle detection, find_by_name() for duplicate check
- **OrmProductRepository**: find_linked_ids() to detect products used in recipes
- **OrmMenuRepository**: upsert slots via menu entity methods
- **OrmFamilyMemberRepository**: simple CRUD
- **OrmRecipeCategoryRepository** / **OrmProductCategoryRepository**: marker subclasses
- **OrmRefreshTokenRepository**: revoke(), revoke_all_for_user()
- **OrmSavedShoppingListRepository**: CRUD for persistent lists
- **OrmPreferenceRepository**: find_by_ids(), find_by_name()
- **OrmMealTypeRepository**: count_custom(), get_usage() (returns menu references)

### Export Registry + Implementations (9)
Plugin-based architecture for multi-format export:
- **ExportRegistry**: (entity_type, format) → EntityExporter mapping
- **Shopping List**: CSV, JSON, PDF (tabular + summary)
- **Recipes**: CSV (flattened), JSON (full tree)
- **Products**: CSV, JSON
- **Menus**: JSON (slots with member assignments), PDF (weekly grid)

### Import Registry + Implementations (5)
Multi-format import with upsert semantics:
- **ImportRegistry**: (entity_type, format) → EntityImporter mapping
- **RecipeCsvImporter** / **RecipeJsonImporter**: duplicate detection, category linking
- **ProductCsvImporter** / **ProductJsonImporter**: unit validation, category linking
- **MenuJsonImporter**: validates recipe/product references, resolves meal_type IDs

### Database Connection Utilities
- **get_engine()**: SQLite (file/memory) + PostgreSQL support, FK pragma for SQLite
- **apply_schema()**: idempotent table creation via SQLAlchemy
- **seed_defaults()**: populates units + default categories (6 recipe, 8 product)
- **SQLite Migrations**: legacy schema updates for backwards compatibility

### Key Design Patterns
- **Generic Repository**: BaseOrmRepository[E, I] eliminates ~500 lines of boilerplate
- **Registry Pattern**: Exporters/importers self-register by type+format
- **Typed IDs**: NewType wrappers (RecipeId, ProductId) ensure type safety
- **JSON Columns**: preference_ids, member_ids stored as JSON strings (PostgreSQL-compatible)
- **Cascade Deletes**: FK constraints with CASCADE ensure referential integrity
- **Dialect Abstraction**: get_engine() handles SQLite vs PostgreSQL differences
