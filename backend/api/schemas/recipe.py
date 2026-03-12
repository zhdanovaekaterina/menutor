from pydantic import BaseModel


class RecipeIngredientSchema(BaseModel):
    product_id: int
    quantity_amount: float
    quantity_unit: str


class CookingStepSchema(BaseModel):
    order: int
    description: str


class RecipeCreate(BaseModel):
    name: str
    category_id: int
    servings: int
    ingredients: list[RecipeIngredientSchema] = []
    steps: list[CookingStepSchema] = []
    weight: int = 0


class RecipeUpdate(BaseModel):
    name: str
    category_id: int
    servings: int
    ingredients: list[RecipeIngredientSchema] = []
    steps: list[CookingStepSchema] = []
    weight: int = 0


class RecipeResponse(BaseModel):
    id: int
    name: str
    category_id: int
    servings: int
    ingredients: list[RecipeIngredientSchema]
    steps: list[CookingStepSchema]
    weight: int
