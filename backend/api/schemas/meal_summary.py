"""Pydantic schemas for the Meal Summary feature."""

from pydantic import BaseModel


class MealOccurrenceSchema(BaseModel):
    day: int
    meal_type: str
    servings: float
    pieces_override: int | None = None
    slot_index: int


class MealIngredientSchema(BaseModel):
    product_id: int | None
    product_name: str
    quantity_amount: float
    quantity_unit: str
    sub_recipe_id: int | None = None
    sub_recipe_name: str | None = None
    sub_ingredients: list["MealIngredientSchema"] = []


class PiecesInfoSchema(BaseModel):
    total_pieces: int
    pieces_per_portion: int


class MealSummaryRecipeSchema(BaseModel):
    recipe_id: int
    recipe_name: str
    occurrences: list[MealOccurrenceSchema]
    total_servings: float
    pieces_info: PiecesInfoSchema | None = None
    ingredients: list[MealIngredientSchema]


class MealSummaryProductOccurrence(BaseModel):
    day: int
    meal_type: str
    quantity: float
    unit: str
    slot_index: int


class MealSummaryProductSchema(BaseModel):
    product_id: int
    product_name: str
    occurrences: list[MealSummaryProductOccurrence]
    total_quantity: float
    unit: str


class MealSummaryResponseSchema(BaseModel):
    menu_id: int
    menu_name: str
    recipes: list[MealSummaryRecipeSchema]
    products: list[MealSummaryProductSchema]


class GenerateFilteredShoppingListRequest(BaseModel):
    """Request body for generating a shopping list from selected slots."""
    slot_indices: list[int]
