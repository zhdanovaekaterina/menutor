/* TypeScript interfaces matching backend Pydantic schemas */

export interface RecipeIngredient {
  product_id: number
  quantity_amount: number
  quantity_unit: string
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
}

export interface Recipe {
  id: number
  name: string
  category_id: number
  servings: number
  ingredients: RecipeIngredient[]
  steps: CookingStep[]
  weight: number
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
  weight_per_piece_g?: number | null
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
  weight_per_piece_g: number | null
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
}

export interface Category {
  id: number
  name: string
  active: boolean
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
  cost: Money
  purchased: boolean
  recipe_quantity: Quantity | null
}

export interface ShoppingList {
  items: ShoppingListItem[]
  total_cost: Money
}
