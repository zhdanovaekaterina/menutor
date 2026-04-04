# Version 0.15.0 — Recipe Cost Per Portion

Technical documentation for version 0.15.0: automatic calculation and display of recipe portion cost based on ingredient prices from the product catalog. The system provides real-time cost preview during recipe editing, supports nested recipes and piece-based scaling modes, and includes a visual setting to toggle cost display across the entire application.

## Overview

The recipe cost system calculates the cost of a single recipe portion by aggregating the prices of all ingredients from the product catalog. Each recipe displays its portion cost in the recipe list with optional warnings for incomplete pricing, and provides a detailed cost breakdown during editing. Users can toggle cost visibility application-wide through a settings switch, and all calculations support nested recipes (recipe-as-ingredient) and piece-based scaling modes.

**Key features:**
- Pure domain service `RecipeCostCalculator` for cost computation
- Real-time cost preview during recipe form editing (300ms debounce)
- Nested recipe flattening via `ShoppingListBuilder.flatten_recipe_products()`
- Partial cost detection: `is_partial = true` when any ingredient lacks a price
- Expandable cost breakdown showing ingredient-by-ingredient calculation
- Cost sorting in recipe table (desktop)
- Mobile cost badge with "~" prefix for partial costs
- Settings toggle to hide/show cost everywhere (localStorage persistence)
- API endpoint `POST /api/recipes/cost-preview` for unsaved recipe preview
- Three new fields on `RecipeResponse`: `cost_per_portion`, `cost_currency`, `cost_is_partial`

## Domain Layer

### RecipeCostResult Value Object

**File:** `backend/domain/value_objects/recipe_cost_result.py`

```python
@dataclass
class RecipeCostResult:
    cost_per_portion: float | None      # Cost of one portion (e.g., 150.0)
    total_cost: float | None             # cost_per_portion × servings (e.g., 600.0)
    currency: str                        # "₽" or other (from user's product prices)
    is_partial: bool                     # True if any ingredient lacks price or product was deleted
    computed_servings: int | float       # Number of servings (for piece-mode: total_pieces / pieces_per_portion)
    ingredient_costs: list[IngredientCost]  # Breakdown by ingredient
```

### IngredientCost Value Object

**File:** `backend/domain/value_objects/ingredient_cost.py`

```python
@dataclass
class IngredientCost:
    ingredient_name: str                 # Product or recipe name
    quantity: float                      # Amount used (e.g., 500)
    unit: str                           # Unit of measurement (e.g., "г", "мл", "шт")
    unit_price: float | None            # Price per unit (None if unknown)
    total: float | None                 # quantity × unit_price (None if unit_price is None)
    is_missing: bool                    # True if product not found or has no price
```

### RecipeCostCalculator Domain Service

**File:** `backend/domain/services/recipe_cost_calculator.py`

Pure domain service performing cost calculation on flattened product lists:

```python
class RecipeCostCalculator:
    def calculate(
        self, 
        flattened_products: list[tuple[ProductId, str, float, str, float | None]],
        recipe_servings: int | float
    ) -> RecipeCostResult:
        """
        Calculate recipe cost from flat product list.
        
        Args:
            flattened_products: list of (product_id, name, quantity, unit, price_per_unit)
                               from ShoppingListBuilder.flatten_recipe_products()
            recipe_servings: number of portions for this recipe (or computed for piece-mode)
        
        Returns: RecipeCostResult with cost_per_portion, total_cost, ingredient breakdown
        
        Behavior:
        - Sums (quantity × price_per_unit) for all products with known prices
        - Divides by recipe_servings to get cost_per_portion
        - Sets is_partial=True if any ingredient has price_per_unit=0 or is_missing
        - Returns None for costs if all products lack prices
        """
```

### ORM Integration

**Ports:** no new repository ports needed; cost calculation uses existing product repositories via `ShoppingListBuilder`.

## Application Layer

### CalculateRecipeCost Use Case

**File:** `backend/application/use_cases/calculate_recipe_cost.py`

```python
@dataclass
class CalculateRecipeCostRequest:
    recipe_id: RecipeId
    user_id: UserId

class CalculateRecipeCost:
    def __init__(
        self, 
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        cost_calc: RecipeCostCalculator,
        shopping_list_builder: ShoppingListBuilder
    ) -> None: ...

    def execute(self, request: CalculateRecipeCostRequest) -> RecipeCostResult:
        """
        Calculate cost for a saved recipe.
        
        Flow:
        1. Fetch recipe by ID (verify user ownership)
        2. Flatten recipe ingredients via shopping_list_builder
        3. Call cost_calc.calculate() with flattened products
        4. Handle piece-mode: compute servings = total_pieces / pieces_per_portion
        
        Returns: RecipeCostResult with costs and breakdown
        Raises: RecipeNotFoundError, AccessDeniedError
        """
```

### PreviewRecipeCost Use Case

**File:** `backend/application/use_cases/preview_recipe_cost.py`

```python
@dataclass
class CostPreviewRequest:
    name: str
    portion_count: int | float           # Number of portions
    piece_mode: bool = False              # True for piece-based scaling
    pieces_per_portion: int = 1           # Pieces per 1 portion (piece-mode only)
    ingredients: list[IngredientInput]   # Unsaved ingredient list

@dataclass
class IngredientInput:
    product_id: ProductId | None         # None for new/unsaved products
    recipe_id: RecipeId | None           # For nested recipes
    quantity: float
    unit: str
    # OR manual product entry
    product_name: str | None
    unit_price: float | None

class PreviewRecipeCost:
    def __init__(
        self,
        product_repo: ProductRepository,
        cost_calc: RecipeCostCalculator,
        shopping_list_builder: ShoppingListBuilder
    ) -> None: ...

    def execute(self, request: CostPreviewRequest, user_id: UserId) -> RecipeCostResult:
        """
        Preview cost for unsaved/in-progress recipe.
        
        Flow:
        1. Validate ingredient list (fetch products by ID)
        2. Build ingredient cost table (matching CalculateRecipeCost logic)
        3. Compute servings:
           - Normal mode: portion_count
           - Piece-mode: sum(ingredient quantities) / pieces_per_portion
        4. Call cost_calc.calculate()
        
        Returns: RecipeCostResult
        Raises: ValidationError (missing products, invalid quantities, etc.)
        """
```

### Exception Classes

New exceptions in `backend/domain/exceptions.py`:

```python
class CostCalculationError(Exception):
    """Raised when cost calculation fails (e.g., all products lack prices)."""
    pass
```

## Infrastructure Layer

### ORM Models (No Changes)

No new ORM models; recipes table retains existing structure. Cost is computed on-the-fly, not persisted.

### API Layer

**File:** `backend/api/routers/recipes.py`

#### New Schemas

**File:** `backend/api/schemas/recipe_cost.py`

```python
class IngredientCostSchema(BaseModel):
    ingredient_name: str
    quantity: float
    unit: str
    unit_price: float | None
    total: float | None
    is_missing: bool

class RecipeCostResultSchema(BaseModel):
    cost_per_portion: float | None      # float or null
    total_cost: float | None
    currency: str
    is_partial: bool
    computed_servings: int | float
    ingredient_costs: list[IngredientCostSchema]

class CostPreviewRequestSchema(BaseModel):
    name: str
    portion_count: float
    piece_mode: bool = False
    pieces_per_portion: int = 1
    ingredients: list[CostPreviewIngredientSchema]

class CostPreviewIngredientSchema(BaseModel):
    product_id: int | None
    recipe_id: int | None
    quantity: float
    unit: str

class CostPreviewResponseSchema(BaseModel):
    cost_per_portion: float | None
    total_cost: float | None
    currency: str
    is_partial: bool
    ingredient_costs: list[IngredientCostSchema]
```

#### Updated RecipeResponse Schema

```python
class RecipeResponse(BaseModel):
    # ... existing fields ...
    cost_per_portion: float | None      # NEW
    cost_currency: str | None           # NEW
    cost_is_partial: bool               # NEW
```

#### New Endpoints

**Endpoint:** `POST /api/recipes/cost-preview`

```python
@router.post("/cost-preview", response_model=CostPreviewResponseSchema)
async def preview_recipe_cost(
    request: CostPreviewRequestSchema,
    current_user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container)
) -> CostPreviewResponseSchema:
    """
    Preview cost for unsaved recipe without saving.
    
    Request body:
    {
        "name": "Борщ",
        "portion_count": 4,
        "piece_mode": false,
        "pieces_per_portion": 1,
        "ingredients": [
            {"product_id": 1, "recipe_id": null, "quantity": 600, "unit": "г"},
            {"product_id": 2, "recipe_id": null, "quantity": 500, "unit": "г"},
            ...
        ]
    }
    
    Returns:
    {
        "cost_per_portion": 150.0,
        "total_cost": 600.0,
        "currency": "₽",
        "is_partial": false,
        "ingredient_costs": [
            {
                "ingredient_name": "Свёкла",
                "quantity": 600,
                "unit": "г",
                "unit_price": 50.0,
                "total": 30.0,
                "is_missing": false
            },
            ...
        ]
    }
    
    Raises: 400 (validation error), 401 (unauthorized)
    """
    use_case = container.preview_recipe_cost()
    result = use_case.execute(CostPreviewRequest(...), current_user.id)
    return converter.cost_result_to_schema(result)
```

#### Updated Recipe Endpoints

All recipe endpoints (list, get, create, update) now include the three new cost fields in responses:

- `GET /api/recipes` — list includes costs
- `GET /api/recipes/{id}` — includes costs
- `POST /api/recipes` — create response includes costs
- `PUT /api/recipes/{id}` — update response includes costs

## Composition Root

**File:** `backend/composition_root.py`

Wiring in `_wire_recipes()`:

```python
def _wire_recipes(self) -> None:
    # ... existing recipe wiring ...
    
    # NEW: Wire cost calculation services
    self.register_singleton(RecipeCostCalculator)
    
    # NEW: Wire cost use cases
    self.register(
        CalculateRecipeCost,
        lambda: CalculateRecipeCost(
            recipe_repo=self.recipe_repository(),
            product_repo=self.product_repository(),
            cost_calc=self.recipe_cost_calculator(),
            shopping_list_builder=self.shopping_list_builder()
        )
    )
    
    self.register(
        PreviewRecipeCost,
        lambda: PreviewRecipeCost(
            product_repo=self.product_repository(),
            cost_calc=self.recipe_cost_calculator(),
            shopping_list_builder=self.shopping_list_builder()
        )
    )
```

## Frontend Layer

### Vue Components

#### CostBadge.vue

**File:** `frontend/src/components/recipes/CostBadge.vue`

Small component displaying cost with optional warning icon:

```vue
<template>
  <div v-if="showCost && costPerPortion" class="cost-badge" :class="badgeClass">
    <span v-if="isPartial" class="warning-icon" title="Приблизительная стоимость">⚠</span>
    <span>{{ displayCost }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  costPerPortion: number | null
  currency: string
  isPartial: boolean
  showCost: boolean
}

const props = withDefaults(defineProps<Props>(), {
  currency: '₽',
  isPartial: false,
  showCost: true
})

const badgeClass = computed(() => ({
  'is-partial': props.isPartial
}))

const displayCost = computed(() => {
  if (!props.costPerPortion) return ''
  const prefix = props.isPartial ? '~' : ''
  return `${prefix}${props.costPerPortion.toFixed(2)} ${props.currency}`
})
</script>

<style scoped>
.cost-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.cost-badge.is-partial {
  background: #fff3cd;
}

.warning-icon {
  color: #ff9800;
}
</style>
```

#### CostSummaryBlock.vue

**File:** `frontend/src/components/recipes/CostSummaryBlock.vue`

Collapsible block in recipe form showing real-time cost preview:

```vue
<template>
  <div v-if="showCost" class="cost-summary-block">
    <button class="header" @click="isExpanded = !isExpanded">
      <span>Стоимость порции</span>
      <span class="toggle-icon">{{ isExpanded ? '▼' : '▶' }}</span>
    </button>
    
    <div v-if="isExpanded" class="content">
      <div class="cost-row">
        <span>Одна порция:</span>
        <span class="cost-value">{{ costPerPortion }}</span>
      </div>
      
      <div class="cost-row">
        <span>Всего ({{ recipeServings }} порций):</span>
        <span class="cost-value">{{ totalCost }}</span>
      </div>
      
      <div v-if="isPartial" class="warning">
        ⚠ Стоимость приблизительна: у некоторых ингредиентов не указана цена
      </div>
      
      <button class="breakdown-toggle" @click="showBreakdown = !showBreakdown">
        {{ showBreakdown ? 'Скрыть разбивку стоимости' : 'Показать разбивку стоимости' }}
      </button>
      
      <table v-if="showBreakdown" class="breakdown-table">
        <thead>
          <tr>
            <th>Ингредиент</th>
            <th>Количество</th>
            <th>Цена за единицу</th>
            <th>Стоимость</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ic in ingredientCosts" :key="ic.ingredient_name">
            <td>{{ ic.ingredient_name }}</td>
            <td>{{ ic.quantity }} {{ ic.unit }}</td>
            <td>{{ ic.unit_price?.toFixed(2) ?? '—' }}</td>
            <td>{{ ic.total?.toFixed(2) ?? '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RecipeCostResult } from '@/api/types'

interface Props {
  costResult: RecipeCostResult | null
  recipeServings: number
  showCost: boolean
}

const props = defineProps<Props>()

const isExpanded = ref(false)
const showBreakdown = ref(false)

const costPerPortion = computed(() => {
  if (!props.costResult?.cost_per_portion) return '—'
  const prefix = props.costResult.is_partial ? '~' : ''
  return `${prefix}${props.costResult.cost_per_portion.toFixed(2)} ${props.costResult.currency}`
})

const totalCost = computed(() => {
  if (!props.costResult?.total_cost) return '—'
  const prefix = props.costResult.is_partial ? '~' : ''
  return `${prefix}${props.costResult.total_cost.toFixed(2)} ${props.costResult.currency}`
})

const isPartial = computed(() => props.costResult?.is_partial ?? false)
const ingredientCosts = computed(() => props.costResult?.ingredient_costs ?? [])
</script>

<style scoped>
.cost-summary-block {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-top: 16px;
}

.header {
  width: 100%;
  padding: 12px;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.content {
  padding: 12px;
}

.cost-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.cost-value {
  font-weight: 500;
  color: #2196f3;
}

.warning {
  background: #fff3cd;
  border-left: 3px solid #ff9800;
  padding: 8px;
  margin: 8px 0;
  color: #856404;
  font-size: 13px;
}

.breakdown-toggle {
  background: transparent;
  border: none;
  color: #2196f3;
  cursor: pointer;
  padding: 8px 0;
  text-decoration: underline;
}

.breakdown-table {
  width: 100%;
  margin-top: 12px;
  border-collapse: collapse;
  font-size: 13px;
}

.breakdown-table th,
.breakdown-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.breakdown-table th {
  background: #f9f9f9;
  font-weight: 500;
}
</style>
```

#### RecipeTable.vue Updates

**File:** `frontend/src/components/recipes/RecipeTable.vue`

Changes:
- Add column `costPerPortion` (only on desktop if settings.showRecipeCost)
- Make column sortable by cost
- On mobile, show CostBadge after recipe name if settings.showRecipeCost

```vue
<!-- Desktop table with new cost column -->
<table>
  <thead>
    <tr>
      <th @click="sortBy('name')">Название</th>
      <th>Категория</th>
      <th>Порций</th>
      <th>Вес (г)</th>
      <th v-if="showRecipeCost" @click="sortBy('cost')">Стоимость</th>
    </tr>
  </thead>
  <tbody>
    <tr v-for="recipe in sortedRecipes" :key="recipe.id">
      <td>{{ recipe.name }}</td>
      <td>{{ recipe.category?.name }}</td>
      <td>{{ recipe.portion_count }}</td>
      <td>{{ recipe.weight_grams }}</td>
      <td v-if="showRecipeCost">
        <CostBadge
          :cost-per-portion="recipe.cost_per_portion"
          :currency="recipe.cost_currency || '₽'"
          :is-partial="recipe.cost_is_partial"
          :show-cost="showRecipeCost"
        />
      </td>
    </tr>
  </tbody>
</table>
```

#### RecipeForm.vue Updates

**File:** `frontend/src/components/recipes/RecipeForm.vue`

Integration points:
- Import and register `CostSummaryBlock`
- Watch for ingredient changes (debounced 300ms)
- Call `recipeStore.previewRecipeCost()` on changes
- Pass `costResult` to `CostSummaryBlock`
- Show warning icon (⚠) next to ingredients without prices

```vue
<template>
  <form>
    <!-- ... existing recipe fields ... -->
    
    <!-- Cost summary block (real-time preview) -->
    <CostSummaryBlock
      :cost-result="costResult"
      :recipe-servings="form.portion_count"
      :show-cost="showRecipeCost"
    />
    
    <!-- Ingredients section with warning icons -->
    <section class="ingredients">
      <div v-for="(ing, idx) in form.ingredients" :key="idx" class="ingredient-row">
        <select v-model="ing.product_id">
          <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <input v-model.number="ing.quantity" type="number" />
        <span class="unit">{{ ing.unit }}</span>
        
        <!-- Warning icon if ingredient has no price -->
        <span v-if="!getProductPrice(ing.product_id)" class="warning-icon" title="Укажите цену в каталоге продуктов">⚠</span>
      </div>
    </section>
  </form>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import CostSummaryBlock from './CostSummaryBlock.vue'
import { useRecipeStore } from '@/stores/recipes'
import { useSettingsStore } from '@/stores/settings'
import { debounce } from '@/utils/debounce'

const recipeStore = useRecipeStore()
const settingsStore = useSettingsStore()

const showRecipeCost = computed(() => settingsStore.showRecipeCost)
const costResult = ref(null)

// Debounced cost preview on ingredient changes
const updateCostPreview = debounce(() => {
  if (!showRecipeCost.value) return
  costResult.value = recipeStore.currentCostPreview
}, 300)

watch(() => form.ingredients, updateCostPreview, { deep: true })
</script>

<style scoped>
.warning-icon {
  color: #ff9800;
  margin-left: 4px;
}
</style>
```

#### IngredientListEditor.vue Updates

**File:** `frontend/src/components/recipes/IngredientListEditor.vue`

Changes:
- Show ⚠ warning icon next to ingredients without prices (if showRecipeCost enabled)
- Pass `showCostWarnings` prop to control visibility

```vue
<template>
  <div v-for="(ingredient, idx) in ingredients" :key="idx" class="ingredient-item">
    <span>{{ ingredient.name }}</span>
    <span>{{ ingredient.quantity }} {{ ingredient.unit }}</span>
    <span v-if="showCostWarnings && !ingredient.hasPrice" class="warning-icon">⚠</span>
    <button @click="removeIngredient(idx)">×</button>
  </div>
</template>

<script setup lang="ts">
interface Props {
  ingredients: Array<{ name: string; quantity: number; unit: string; hasPrice: boolean }>
  showCostWarnings: boolean
}

defineProps<Props>()
</script>
```

### Pinia Stores

#### recipeSettings Store

**File:** `frontend/src/stores/recipeSettings.ts`

New store for recipe-specific settings:

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRecipeSettingsStore = defineStore('recipeSettings', () => {
  const showRecipeCost = ref<boolean>(
    JSON.parse(localStorage.getItem('recipe_show_cost') ?? 'true')
  )
  
  const toggleShowRecipeCost = () => {
    showRecipeCost.value = !showRecipeCost.value
    localStorage.setItem('recipe_show_cost', JSON.stringify(showRecipeCost.value))
  }
  
  return { showRecipeCost, toggleShowRecipeCost }
})
```

#### recipes Store Updates

**File:** `frontend/src/stores/recipes.ts`

New methods in recipes store:

```typescript
async previewRecipeCost(request: CostPreviewRequest): Promise<RecipeCostResult> {
  const response = await api.post('/recipes/cost-preview', request)
  return response.data
}

// Existing methods now also return cost fields
async createRecipe(data: RecipeCreate): Promise<Recipe> {
  // ... now returns cost_per_portion, cost_currency, cost_is_partial
}

async updateRecipe(id: RecipeId, data: RecipeUpdate): Promise<Recipe> {
  // ... now returns cost_per_portion, cost_currency, cost_is_partial
}
```

### API Client Updates

**File:** `frontend/src/api/types.ts`

New types:

```typescript
export interface IngredientCost {
  ingredient_name: string
  quantity: number
  unit: string
  unit_price: number | null
  total: number | null
  is_missing: boolean
}

export interface RecipeCostResult {
  cost_per_portion: number | null
  total_cost: number | null
  currency: string
  is_partial: boolean
  computed_servings: number
  ingredient_costs: IngredientCost[]
}

export interface CostPreviewRequest {
  name: string
  portion_count: number
  piece_mode: boolean
  pieces_per_portion: number
  ingredients: CostPreviewIngredient[]
}

export interface CostPreviewIngredient {
  product_id: number | null
  recipe_id: number | null
  quantity: number
  unit: string
}

// Updated Recipe type
export interface Recipe {
  // ... existing fields ...
  cost_per_portion: number | null
  cost_currency: string | null
  cost_is_partial: boolean
}
```

**File:** `frontend/src/api/client.ts`

```typescript
export async function previewRecipeCost(request: CostPreviewRequest): Promise<RecipeCostResult> {
  const response = await api.post('/recipes/cost-preview', request)
  return response.data
}
```

### Recipe Settings Panel

**File:** `frontend/src/components/settings/RecipeSettingsPanel.vue`

New settings panel in Settings → Рецепты:

```vue
<template>
  <div class="recipe-settings">
    <h3>Показывать стоимость порции</h3>
    <label class="toggle">
      <input
        v-model="showRecipeCost"
        type="checkbox"
        @change="toggleShowRecipeCost"
      />
      <span>{{ showRecipeCost ? 'Включено' : 'Отключено' }}</span>
    </label>
    <p class="description">
      Отображает стоимость в таблице рецептов, в форме редактирования и в бейджах мобильных устройств.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRecipeSettingsStore } from '@/stores/recipeSettings'

const settingsStore = useRecipeSettingsStore()

const showRecipeCost = computed({
  get: () => settingsStore.showRecipeCost,
  set: (val) => {
    if (val !== settingsStore.showRecipeCost) {
      settingsStore.toggleShowRecipeCost()
    }
  }
})

const toggleShowRecipeCost = () => {
  settingsStore.toggleShowRecipeCost()
}
</script>

<style scoped>
.recipe-settings {
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.description {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}
</style>
```

## Key Design Decisions

### 1. Pure Domain Service

`RecipeCostCalculator` is a pure domain service (no I/O, no side effects) to maximize testability and reusability. It operates on already-flattened product lists, leaving ingredient resolution to use cases.

### 2. Partial Cost Handling

The `is_partial` flag is set to `true` if **any** ingredient lacks a price, signaling that the calculation is incomplete. This is visually indicated on UI with "~" prefix and warning icons, helping users understand which recipes have missing pricing data.

### 3. Nested Recipe Flattening

Rather than implement recursive cost calculation, we reuse `ShoppingListBuilder.flatten_recipe_products()` which already handles:
- Nested recipe expansion
- Piece-mode scaling computation
- Product duplication and aggregation

This avoids code duplication and ensures cost calculations align with shopping list generation.

### 4. Real-Time Preview with Debounce

The `PreviewRecipeCost` use case supports unsaved recipe preview with 300ms debouncing in the frontend to avoid excessive re-rendering and API calls during rapid ingredient editing.

### 5. Settings Persistence

The `showRecipeCost` toggle persists to localStorage (not the database) to respect user preference instantly without server round-trips. Different browsers/devices can have different settings.

### 6. No Cost Persistence

Costs are computed on-the-fly (not stored in the database) to ensure they always reflect current product prices. If a product price changes, all recipes using that product reflect the new cost immediately.

## Testing Strategy

### Unit Tests

**Backend:** `tests/unit/domain/test_recipe_cost_calculator.py`
- Test basic cost calculation
- Test partial cost detection (missing prices)
- Test nested recipe flattening edge cases
- Test piece-mode scaling (servings = total_pieces / pieces_per_portion)

**Backend:** `tests/unit/application/test_calculate_recipe_cost.py`
- Test use case with saved recipes
- Test access control (user can only see their recipes)
- Test error handling (recipe not found)

**Backend:** `tests/unit/application/test_preview_recipe_cost.py`
- Test cost preview for unsaved recipes
- Test with various ingredient lists
- Test validation (missing products, invalid units)

**Backend:** `tests/unit/api/test_recipes_cost.py`
- Test `POST /api/recipes/cost-preview` endpoint
- Test schema validation (CostPreviewRequestSchema)
- Test response format (RecipeCostResultSchema)

**Frontend:** `tests/unit/components/test_cost_badge.vue`
- Test rendering with valid cost
- Test "~" prefix for partial cost
- Test warning icon appearance

**Frontend:** `tests/unit/stores/test_recipe_settings.ts`
- Test localStorage persistence
- Test toggle action

### Integration Tests

**Backend:** `tests/integration/test_cost_calculation_e2e.py`
- Create recipe with ingredients
- Calculate cost
- Verify result matches manual calculation
- Test nested recipes with multiple levels

**Frontend:** `tests/integration/recipe_form_cost.spec.ts`
- Open recipe form
- Edit ingredients
- Verify cost updates in real-time with debouncing
- Test visibility toggle

## Production Considerations

### Performance

- Cost calculation is synchronous and fast (O(n) where n = number of ingredients)
- API endpoint `POST /api/recipes/cost-preview` is light-weight (no database writes)
- Debouncing (300ms) prevents excessive calculations during editing
- No caching required; costs always reflect current prices

### Data Integrity

- No circular dependencies possible (recipe-ingredient graph has no cycles due to `ShoppingListBuilder` validation)
- Costs handle missing products gracefully (is_partial = true)
- Currency symbol is drawn from product prices (all same user → all same currency)

### Backward Compatibility

- Three new fields on `RecipeResponse` are nullable (cost_per_portion, cost_currency, cost_is_partial)
- Existing recipe endpoints continue to work without cost calculation if not needed
- Settings toggle defaults to `true` (cost visible by default)

### Migration Path

- No database migration required (cost is not persisted)
- Existing recipes get cost calculated retroactively when viewed
- No data loss or schema changes
