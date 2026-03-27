/* TypeScript interfaces matching backend Pydantic schemas */

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface RecipeIngredient {
  product_id: number | null
  sub_recipe_id: number | null
  sub_recipe_name?: string | null
  quantity_amount: number
  quantity_unit: string
  order: number
}

export interface ValidateSubRecipeRequest {
  parent_recipe_id: number | null
  sub_recipe_id: number
}

export interface ValidateSubRecipeResponse {
  valid: boolean
  error: string | null
}

export interface FlattenedProduct {
  product_id: number
  product_name: string
  quantity_amount: number
  quantity_unit: string
}

export interface IngredientRow {
  product_id: number | null
  sub_recipe_id: number | null
  quantity_amount: number
  quantity_unit: string
}

export interface RecipeDependent {
  id: number
  name: string
}

export interface CookingStep {
  order: number
  description: string
}

export interface RecipeCreate {
  name: string
  category_id: number
  servings: number
  ingredients?: RecipeIngredient[]
  steps?: CookingStep[]
  weight?: number
  total_pieces?: number | null
  pieces_per_portion?: number | null
  link?: string | null
  comment?: string | null
}

export interface Recipe {
  id: number
  name: string
  category_id: number
  servings: number
  ingredients: RecipeIngredient[]
  steps: CookingStep[]
  weight: number
  total_pieces: number | null
  pieces_per_portion: number | null
  link: string | null
  comment: string | null
}

export interface ProductCreate {
  name: string
  category_id: number
  recipe_unit: string
  purchase_unit: string
  price_amount: string
  price_currency?: string
  brand?: string
  supplier?: string
  conversion_factor?: number
}

export interface Product {
  id: number
  name: string
  category_id: number
  recipe_unit: string
  purchase_unit: string
  price_amount: string
  price_currency: string
  brand: string
  supplier: string
  conversion_factor: number
}

export interface MenuSlot {
  day: number
  meal_type: string
  recipe_id?: number | null
  product_id?: number | null
  quantity?: number | null
  unit?: string | null
  servings_override?: number | null
  pieces_override?: number | null
  position?: number
}

export interface Menu {
  id: number
  name: string
  slots: MenuSlot[]
}

export interface RemoveItemRequest {
  day: number
  meal_type: string
  recipe_id?: number | null
  product_id?: number | null
}

export interface MoveSlotRequest {
  day: number
  meal_type: string
  recipe_id?: number | null
  product_id?: number | null
  to_day: number
  to_meal_type: string
  to_position: number
}

export interface FamilyMemberCreate {
  name: string
  portion_multiplier?: number
  dietary_restrictions?: string
  comment?: string
}

export interface FamilyMember {
  id: number
  name: string
  portion_multiplier: number
  dietary_restrictions: string
  comment: string
}

export interface ActiveCategory {
  id: number
  name: string
  color: string | null
}

export interface Category {
  id: number
  name: string
  active: boolean
  color: string | null
}

export interface Quantity {
  amount: number
  unit: string
}

export interface Money {
  amount: string
  currency: string
}

export interface ShoppingListItem {
  product_id: number
  product_name: string
  category: string
  quantity: Quantity
  buy_quantity: Quantity
  buy_quantity_overridden?: boolean
  cost: Money
  purchased: boolean
  recipe_quantity: Quantity | null
}

export interface ShoppingList {
  items: ShoppingListItem[]
  total_cost: Money
}

export interface SavedShoppingListItem {
  id: number
  product_id: number | null
  product_name: string
  category: string
  quantity: Quantity
  buy_quantity: Quantity
  buy_quantity_overridden: boolean
  cost: Money
  purchased: boolean
  recipe_quantity: Quantity | null
  item_order: number
}

export interface SavedShoppingList {
  id: number
  name: string
  items: SavedShoppingListItem[]
  total_cost: Money
  source_menu_id: number | null
  created_at: string
  updated_at: string
}

export interface SavedShoppingListMeta {
  id: number
  name: string
  source_menu_id: number | null
  created_at: string
  updated_at: string
}

export interface SavedShoppingListItemInput {
  product_id: number | null
  product_name: string
  category: string
  quantity_amount: number
  quantity_unit: string
  buy_quantity_amount: number
  buy_quantity_unit: string
  buy_quantity_overridden: boolean
  cost_amount: number
  cost_currency: string
  purchased: boolean
  recipe_quantity_amount: number | null
  recipe_quantity_unit: string | null
  item_order: number
}

export interface UpdateSavedShoppingListRequest {
  name: string
  items: SavedShoppingListItemInput[]
}

export interface RenameSavedShoppingListRequest {
  name: string
}

/* Auth */
export interface RegisterRequest {
  email: string
  password: string
  nickname?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RefreshRequest {
  refresh_token: string
}

export interface UserResponse {
  id: number
  email: string
  nickname: string
  created_at: string
}

export interface UpdateProfileRequest {
  nickname?: string
  password?: string
}

export interface ImportResult {
  created: number
  updated: number
  errors: string[]
}

/* Meal Summary */
export interface MealOccurrence {
  day: number
  meal_type: string
  servings: number
  pieces_override?: number | null
  slot_index: number
}

export interface MealIngredient {
  product_id: number | null
  product_name: string
  quantity_amount: number
  quantity_unit: string
  sub_recipe_id?: number | null
  sub_recipe_name?: string | null
  sub_ingredients?: MealIngredient[]
}

export interface PiecesInfo {
  total_pieces: number
  pieces_per_portion: number
}

export interface MealSummaryRecipe {
  recipe_id: number
  recipe_name: string
  occurrences: MealOccurrence[]
  total_servings: number
  pieces_info?: PiecesInfo | null
  ingredients: MealIngredient[]
}

export interface MealSummaryProductOccurrence {
  day: number
  meal_type: string
  quantity: number
  unit: string
  slot_index: number
}

export interface MealSummaryProduct {
  product_id: number
  product_name: string
  occurrences: MealSummaryProductOccurrence[]
  total_quantity: number
  unit: string
}

export interface MealSummaryResponse {
  menu_id: number
  menu_name: string
  recipes: MealSummaryRecipe[]
  products: MealSummaryProduct[]
}

export interface GenerateFilteredShoppingListRequest {
  slot_indices: number[]
  excluded_sub_recipe_ids: number[]
}
