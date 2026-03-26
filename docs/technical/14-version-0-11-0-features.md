# Version 0.11.0 Features: Category Colors & Pagination

**Release date:** 26.03.2026

## Overview

Version 0.11.0 introduces two major features:

1. **Category colors** — each product and recipe category can be assigned an `#RRGGBB` color that propagates through the planner UI and PDF exports.
2. **Pagination system** — product and recipe lists load data in fixed-size pages of 25 items, reducing memory usage and improving load times for large catalogs.

---

## Feature 1: Category Colors

### Domain Changes

**File:** `backend/domain/value_objects/category.py`

```python
@dataclass
class ActiveCategory:
    id: int
    name: str
    color: str | None = None   # new field, #RRGGBB or None
```

The `color` field is optional; `None` means "no color assigned" (the UI falls back to a default).

### Database Migration

**File:** `alembic/versions/0cf76e3bb053_add_category_color.py`

Adds a nullable `VARCHAR(7)` column `color` to both `product_categories` and `recipe_categories` tables:

```sql
ALTER TABLE product_categories ADD COLUMN color VARCHAR(7);
ALTER TABLE recipe_categories  ADD COLUMN color VARCHAR(7);
```

### Infrastructure

**File:** `backend/infrastructure/repositories/base_category.py`

The base ORM category repository reads and writes the new `color` column in all `save` / `find` operations.

### API

**File:** `backend/api/schemas/category.py`

```python
class ActiveCategoryResponse(BaseModel):
    id: int
    name: str
    color: str | None
```

Color is validated as a nullable `#RRGGBB` string. The `create` / `update` schemas accept an optional `color` field, which is threaded through converters and routers.

### PDF Exporters

**Files:** `backend/infrastructure/export/menu_pdf_exporter.py`, `backend/infrastructure/export/shopping_list_pdf_exporter.py`

Both exporters now accept category color information and use it to render colored markers (borders, badges) next to category headings and item rows when a color is set.

### Frontend

#### TypeScript Types

**File:** `frontend/src/api/types.ts`

```typescript
interface ActiveCategory {
  id: number
  name: string
  color: string | null
}
```

#### Color Utilities

**File:** `frontend/src/utils/color.ts`

Helper functions for working with hex colors:
- Parsing and validating `#RRGGBB` strings
- Converting hex to RGB for tint generation
- Generating lighter background tints from a category color

**File:** `frontend/src/constants/colors.ts`

Predefined palette of 30 colors shown as swatches in the color picker.

#### Color Picker Components

| Component | File | Purpose |
|---|---|---|
| `ColorPicker` | `ui/ColorPicker.vue` | Container; shows swatch grid + advanced toggle |
| `ColorPickerSwatch` | `ui/ColorPickerSwatch.vue` | Single clickable color circle |
| `ColorPickerAdvanced` | `ui/ColorPickerAdvanced.vue` | Free-text `#RRGGBB` input with validation |

#### Recent Colors

**File:** `frontend/src/composables/useRecentColors.ts`

Stores the last N colors used across category saves in `localStorage`, shown as a "recent" row at the top of the color picker.

#### CategoryPanel Integration

**File:** `frontend/src/components/settings/CategoryPanel.vue`

- Each category row now shows a small color swatch button.
- Clicking it opens the `ColorPicker` popover inline.
- On save, the selected color is sent to the API together with the category name.

#### Planner Grid

**Files:** `frontend/src/components/planner/ItemRow.vue`, `frontend/src/components/planner/GridCell.vue`

- `GridCell` resolves the category color for each recipe/product slot via the categories store.
- `ItemRow` receives the resolved color and applies it as a dynamic CSS border-left color and a tinted background, replacing the previous static blue/orange defaults.
- When no color is assigned, the previous defaults are used as fallback.

**File:** `frontend/src/views/MenuPlannerView.vue`

Both product and recipe category stores are now loaded on mount so that `GridCell` always has color data available when rendering.

#### Categories Store

**File:** `frontend/src/stores/categories.ts`

The store now exposes helper methods to look up a category color by id for both product and recipe categories, used by `GridCell`.

---

## Feature 2: Pagination System

## User-Facing Changes

### Product and Recipe Tables

- **Page Size:** Fixed at 25 items per page (configurable via `PAGE_SIZE` constant)
- **Navigation:** Users can navigate between pages using pagination controls
- **Search and Filters:** Applied across all pages; filters reset pagination to page 1 when changed
- **Responsive UI:** Pagination controls adapt to different screen sizes

### Ingredient and Sub-Recipe Pickers

- **Full List Loading:** Modal dialogs for selecting ingredients and sub-recipes load the complete list without pagination
- **No Pagination in Selectors:** Ensures users can access all available items without page navigation

## Architecture

### Backend Changes

#### New Domain Application Entity

**File:** `backend/application/paginated_result.py`

```python
@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
```

- Generic data class for returning paginated results from use cases
- Contains current page items, total count, current page number, and page size
- Default `PAGE_SIZE` = 25 (defined in this module)

#### Repository Interface Updates

**Files:** `backend/domain/ports/product_repository.py`, `backend/domain/ports/recipe_repository.py`

New abstract methods:

```python
def count(
    self,
    user_id: UserId,
    search: str = "",
    category_id: ProductCategoryId | None = None,
) -> int: ...

def find_page(
    self,
    user_id: UserId,
    search: str,
    limit: int,
    offset: int,
    category_id: ProductCategoryId | None = None,
) -> list[Product]: ...
```

- `count()`: Returns total count of items matching search and filter criteria
- `find_page()`: Returns a single page of items at the specified offset

#### ORM Repository Implementations

**Files:** `backend/infrastructure/repositories/orm_product_repository.py`, `backend/infrastructure/repositories/orm_recipe_repository.py`

Implementations use SQLAlchemy:

- `count()`: Issues `SELECT COUNT(*)` query with search/filter conditions
- `find_page()`: Issues paginated query with `LIMIT` and `OFFSET`, respecting search and category filters
- Handles user ownership checks in all queries

#### Base Use Case Class

**File:** `backend/application/use_cases/crud_base.py`

New `PaginatedListEntities` class:

```python
class PaginatedListEntities:
    """Paginated listing with optional search and category filter.

    When page is None: returns full unfiltered list (for pickers/forms)
    When page is provided: returns one page with search + category applied
    """

    def execute(
        self,
        user_id: UserId,
        category_id: Any = None,
        page: int | None = None,
        search: str = "",
    ) -> PaginatedResult:
        # Returns PaginatedResult with calculated offset and filtered results
```

Logic:
- If `page=None`: returns all items in one page (for ingredient/sub-recipe selectors)
- If `page` is provided: returns `PAGE_SIZE` items at calculated offset
- Applies search and category filters in both modes

#### API Router Changes

**Files:** `backend/api/routers/products.py`, `backend/api/routers/recipes.py`

Updated endpoints:

```python
@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    page: int | None = Query(None, ge=1),
    search: str = Query(""),
    category_id: int | None = Query(None),
    ...
) -> PaginatedResponse[ProductResponse]:
    result = container.list_products.execute(
        user.id,
        ProductCategoryId(category_id) if category_id is not None else None,
        page=page,
        search=search,
    )
    return PaginatedResponse[ProductResponse](
        items=[product_to_response(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )
```

- `page` query parameter (optional, ≥1)
- Returns `PaginatedResponse[T]` with pagination metadata

#### API Response Schema

**File:** `backend/api/schemas/pagination.py` (new)

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
```

Generic Pydantic model for all paginated responses.

### Frontend Changes

#### Pagination Utility

**File:** `frontend/src/utils/pagination.ts` (new)

```typescript
export const PAGE_SIZE = 25
```

Shared constant ensuring frontend and backend use the same page size.

#### Store State

**Files:** `frontend/src/stores/products.ts`, `frontend/src/stores/recipes.ts`

New reactive state:

```typescript
const items = ref<Product[]>([])          // Current page items
const allItems = ref<Product[]>([])        // All items (for pickers)
const page = ref(1)                        // Current page number
const total = ref(0)                       // Total item count
const pageSize = ref(PAGE_SIZE)           // Items per page
const search = ref('')                     // Search query
const categoryId = ref<number | null>(null) // Category filter
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
```

Store methods:

- `_loadPage()`: Fetches the current page with filters applied
- `_loadAll()`: Fetches all items without pagination (for pickers)
- `load()`: Loads both the current page and all items in parallel
- `setPage(p)`: Changes the current page and reloads
- `setFilters()`: Updates search/category, resets to page 1, and reloads

#### API Client

**File:** `frontend/src/api/client.ts`

Updated fetch function:

```typescript
async function fetchProducts(params?: {
  page?: number
  search?: string
  categoryId?: number
}): Promise<PaginatedResponse<Product>> {
  // Only sends 'page' parameter if provided
}
```

- Omits `page` parameter from request if not specified (returns all items)

#### Type Definitions

**File:** `frontend/src/api/types.ts`

New type:

```typescript
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
```

#### Component Updates

**File:** `frontend/src/components/products/ProductTable.vue`, `frontend/src/components/recipes/RecipeTable.vue`

- Displays current page items only
- Client-side sorting applied to the current page results

## How It Works

### Product/Recipe List Flow

1. **Page Load:**
   - User navigates to Products page
   - Store calls `load()` → loads page 1 (25 items) + all items
   - Table displays first 25 items

2. **Search/Filter:**
   - User enters search query or selects category
   - `setFilters()` called → resets page to 1
   - New first page with filters applied is fetched
   - Results count updated

3. **Page Change:**
   - User clicks next/previous button
   - `setPage()` called with new page number
   - API fetches items for that page with current filters
   - Table updates with new page content

### Ingredient Selector Flow

1. **Open Modal:**
   - User clicks "Add ingredient" in recipe form
   - Modal calls `fetchProducts()` without `page` parameter
   - All items (regardless of count) loaded into modal
   - No pagination in selector—user can access all items

## Performance Impact

- **First Page Load:** 25 items displayed instead of entire catalog
- **Memory Usage:** Reduced for large catalogs (thousands of products)
- **Database:** Queries use `LIMIT`/`OFFSET` for efficient pagination
- **Selector Lists:** Full lists loaded (needed for complete user choice)

## Configuration

### Changing Page Size

To modify the number of items per page:

1. Update `backend/application/paginated_result.py`:
   ```python
   PAGE_SIZE = 50  # Change from 25
   ```

2. Update `frontend/src/utils/pagination.ts`:
   ```typescript
   export const PAGE_SIZE = 50
   ```

**Note:** Both must be updated together to maintain consistency.

## Testing

### Backend Tests

- `tests/unit/api/test_products_router.py`: Tests pagination parameters and responses
- `tests/unit/application/test_manage_product.py`: Tests `PaginatedListEntities` use case
- ORM repository tests: Verify `count()` and `find_page()` implementations

### Frontend Tests

- Store tests: Verify `setPage()`, `setFilters()`, pagination state
- API client tests: Verify pagination parameter handling
- Component tests: Verify table displays correct page items

### Integration Tests

- E2E: Complete flow from loading → searching → navigating pages
- Verify filters are preserved across page changes
- Verify selector modals load all items without pagination

## Backwards Compatibility

- API endpoints with no `page` parameter return all items (for existing clients)
- Existing import/export workflows unaffected
- No database schema changes required
