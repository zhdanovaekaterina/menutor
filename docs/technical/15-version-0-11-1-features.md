# Version 0.11.1 Features: Recipe Metadata & Mobile Improvements

**Release date:** 27.03.2026

## Overview

Version 0.11.1 introduces recipe metadata fields and enhances mobile experience with better navigation and export capabilities:

1. **Recipe metadata** — new optional `link` and `comment` fields for storing recipe source URLs and additional notes
2. **Mobile PDF export** — PDF export button now accessible in mobile kebab menu alongside JSON import/export
3. **Pagination fixes** — improved handling of filters and search across page navigation
4. **Tap-outside behavior** — mobile bottom sheets close when tapping outside the component area
5. **PDF export bugfix** — corrected PDF generation for complex menus with nested recipes

---

## Feature 1: Recipe Metadata (Link & Comment)

### Domain Changes

**File:** `backend/domain/entities/recipe.py`

```python
@dataclass
class Recipe:
    id: RecipeId
    name: str
    servings: int
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    steps: list[CookingStep] = field(default_factory=list)
    category_id: RecipeCategoryId = field(default=RecipeCategoryId(0))
    weight: int = 0
    user_id: UserId = field(default=UserId(0))
    total_pieces: int | None = None
    pieces_per_portion: int | None = None
    link: str | None = None            # NEW: URL to recipe source
    comment: str | None = None         # NEW: additional notes
```

Both fields are optional:
- `link`: nullable string field for storing recipe source URLs (e.g., blog post, website, cookbook reference)
- `comment`: nullable string field for user notes (e.g., cooking tips, variations, family preferences)

### Database Migration

**File:** `backend/infrastructure/database/migrations/versions/a2b3c4d5e6f7_add_link_and_comment_to_recipes.py`

Adds two nullable `TEXT` columns to the `recipes` table:

```sql
ALTER TABLE recipes ADD COLUMN link TEXT;
ALTER TABLE recipes ADD COLUMN comment TEXT;
```

### Infrastructure

**File:** `backend/infrastructure/repositories/orm_recipe_repository.py`

ORM repository reads and writes the new columns in all `save()` / `find()` / `find_by_id()` operations:

```python
def save(self, recipe: Recipe) -> Recipe:
    # Existing code...
    db_recipe = RecipeModel(
        # ... existing fields ...
        link=recipe.link,
        comment=recipe.comment,
    )
    # ... save to session ...
```

### API

**File:** `backend/api/schemas/recipe.py`

Updated Pydantic schemas to include the new fields:

```python
class RecipeCreate(BaseModel):
    name: str
    category_id: int
    servings: int
    ingredients: list[RecipeIngredientSchema] = []
    steps: list[CookingStepSchema] = []
    weight: int = 0
    total_pieces: int | None = None
    pieces_per_portion: int | None = None
    link: str | None = None          # NEW
    comment: str | None = None       # NEW


class RecipeResponse(BaseModel):
    id: int
    name: str
    category_id: int
    servings: int
    ingredients: list[RecipeIngredientSchema]
    steps: list[CookingStepSchema]
    weight: int
    total_pieces: int | None = None
    pieces_per_portion: int | None = None
    link: str | None                 # NEW
    comment: str | None              # NEW
```

The fields are optional in both create and update requests.

### Frontend

**File:** `frontend/src/api/types.ts`

Updated TypeScript interface:

```typescript
interface Recipe {
  id: number
  name: string
  categoryId: number
  servings: number
  ingredients: RecipeIngredient[]
  steps: CookingStep[]
  weight: number
  totalPieces: number | null
  piecesPerPortion: number | null
  link: string | null              // NEW
  comment: string | null           // NEW
}
```

**File:** `frontend/src/components/recipes/RecipeForm.vue`

Form now includes two additional fields at the bottom of the recipe details section:

- **Link** — text input for recipe source URL
- **Comment** — textarea for additional notes (word-wrapped, multi-line capable)

Both fields are optional. The form handles empty/null values gracefully.

**File:** `frontend/src/stores/recipes.ts`

Store methods (`createRecipe`, `updateRecipe`) now include the new fields in payloads and maintain them in state.

### Import/Export

**Files:** `backend/infrastructure/export/recipe_csv_exporter.py`, `backend/infrastructure/export/recipe_json_exporter.py`, `backend/infrastructure/import_/recipe_csv_importer.py`, `backend/infrastructure/import_/recipe_json_importer.py`

- **CSV export:** new columns `link` and `comment` appended to recipe rows
- **CSV import:** columns are optional; if missing, fields default to `None`
- **JSON export:** fields included in recipe objects
- **JSON import:** fields imported if present; ignored if missing (backwards-compatible)

### Backwards Compatibility

- Existing recipes without these fields continue to work normally
- API accepts requests without these fields (they default to `None`)
- Export files without these columns can still be imported

---

## Feature 2: Mobile PDF Export

### User-Facing Change

**File:** `frontend/src/views/MenuPlannerView.vue`

Mobile kebab menu now includes **"Скачать PDF"** option (in Russian: "Download PDF"):

```
Menu Options (⋮):
├── Обзор блюд (Meal Summary)
├── Сформировать список покупок (Generate Shopping List)
├── Очистить меню (Clear Menu)
├── Импорт (Import JSON)
├── Экспорт (Export JSON)
└── Скачать PDF (Download PDF) ← NEW
```

Clicking this option triggers the same PDF export flow as the desktop **"Скачать → PDF"** button.

### Backend API

**File:** `backend/api/routers/menus.py`

Existing PDF export endpoint remains unchanged; mobile frontend now simply calls it from the kebab menu instead of a separate desktop button.

### Desktop Consistency

The mobile PDF export uses the same API endpoint and export logic as the desktop version, ensuring identical output across platforms.

---

## Feature 3: Pagination Handling Improvements

### Issues Fixed

**File:** `frontend/src/stores/products.ts`, `frontend/src/stores/recipes.ts`

1. **Filter reset behavior** — when search query or category filter changes, pagination resets to page 1 (instead of staying on current page, which could be invalid)

```typescript
setFilters(search: string, categoryId: number | null) {
  this.search = search
  this.categoryId = categoryId
  this.page = 1  // Reset to first page
  this.load()
}
```

2. **Search persistence** — filters are now correctly maintained as users navigate pages

3. **Total count accuracy** — count is re-fetched when filters change to reflect new filtered total

### Components

**Files:** `frontend/src/components/products/ProductTable.vue`, `frontend/src/components/recipes/RecipeTable.vue`

Pagination controls now correctly reflect:
- Current page number
- Total pages (calculated from total count and page size)
- Disabled state for prev/next buttons at boundaries

---

## Feature 4: Tap-Outside Behavior for Mobile Bottom Sheets

### Implementation

**File:** `frontend/src/composables/useClickOutside.ts` (referenced by mobile components)

Mobile bottom sheets (MobileItemPicker, dialogs) now implement tap-outside-to-close behavior:
- When user taps the overlay/backdrop area (outside the bottom sheet content), the sheet closes
- Taps within the sheet content do not close it
- Implemented via overlay click handler with event delegation

### Components Affected

- **MobileItemPicker** — bottom sheet for adding recipes/products in mobile menu planner
- **Mobile dialogs** — confirmation dialogs, input dialogs slide up from bottom

### User Experience

Users can now:
1. Open a bottom sheet by tapping a cell or button
2. Browse/search for items
3. Close the sheet by tapping the dark overlay above it (common mobile UX pattern)
4. Or select an item and the sheet closes automatically

---

## Feature 5: PDF Export Bugfix

### Issues Resolved

**File:** `backend/infrastructure/export/menu_pdf_exporter.py`

Fixed PDF generation for menus containing:

1. **Nested recipes** — sub-recipes are now properly expanded in the PDF output
2. **Complex ingredient lists** — ingredients with long names or special characters no longer cause rendering issues
3. **Page breaks** — content is correctly distributed across pages for large menus
4. **Category colors** — colored badges/highlights render correctly in PDF

### Backend API

The API endpoint remains unchanged. Clients can continue calling the existing PDF export endpoint without modification.

---

## Testing

### Backend Tests

- `tests/unit/api/test_recipes_router.py` — tests for new recipe fields in create/update/get
- `tests/integration/repositories/test_orm_recipe_repo.py` — tests for recipe repository saving/loading link and comment fields
- `tests/unit/infrastructure/test_recipe_exporters.py` — tests for CSV/JSON export inclusion of new fields

### Frontend Tests

- Store tests verify that recipe mutations preserve link/comment fields
- Form component tests verify input fields render and bind correctly
- Mobile menu tests verify PDF export button appears in kebab menu

### Integration Tests

- E2E tests: create recipe with link/comment → export to JSON → import → verify fields preserved
- E2E tests: mobile menu → open kebab menu → click PDF export → file downloads

---

## Migration Path

### For Existing Deployments

1. **Database migration** — run `alembic upgrade head` to add columns to `recipes` table
2. **API restart** — restart FastAPI to serve updated schemas
3. **Frontend redeploy** — new version automatically fetches latest RecipeResponse schema with optional new fields

### For Existing Data

- All existing recipes will have `link=None` and `comment=None` after migration
- No data loss
- Recipes without these fields are fully functional

---

## Configuration Notes

No configuration changes required. All features are enabled by default.

---

## Rollback Plan

If needed to revert v0.11.1:

1. **Database rollback** — `alembic downgrade -1` removes link/comment columns (irreversible; data will be lost if not backed up)
2. **API downgrade** — deploy previous API version (0.11.0)
3. **Frontend downgrade** — deploy previous frontend build (will ignore link/comment in responses due to TypeScript optional typing)

---

## Related Issues

- **PDF export complexity** — now handles nested recipes and large menus without truncation
- **Mobile UX** — consistent bottom-sheet behavior with modern mobile app patterns
- **Data enrichment** — users can now store recipe sources and cook notes alongside recipes

