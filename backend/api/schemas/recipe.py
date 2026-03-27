from pydantic import BaseModel, model_validator


class RecipeIngredientSchema(BaseModel):
    product_id: int | None = None
    sub_recipe_id: int | None = None
    sub_recipe_name: str | None = None  # response-only, denormalized
    quantity_amount: float
    quantity_unit: str
    order: int = 0

    @model_validator(mode="after")
    def check_xor(self) -> "RecipeIngredientSchema":
        has_product = self.product_id is not None
        has_sub = self.sub_recipe_id is not None
        if has_product == has_sub:
            raise ValueError(
                "Ингредиент должен ссылаться на продукт ИЛИ рецепт, но не на оба"
            )
        return self


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
    total_pieces: int | None = None
    pieces_per_portion: int | None = None
    link: str | None = None
    comment: str | None = None


RecipeUpdate = RecipeCreate


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
    link: str | None = None
    comment: str | None = None


class ValidateSubRecipeRequest(BaseModel):
    parent_recipe_id: int | None = None
    sub_recipe_id: int


class ValidateSubRecipeResponse(BaseModel):
    valid: bool
    error: str | None = None


class FlattenedProductResponse(BaseModel):
    product_id: int
    product_name: str
    quantity_amount: float
    quantity_unit: str


class IngredientPreviewItem(BaseModel):
    product_id: int | None = None
    sub_recipe_id: int | None = None
    quantity_amount: float
    quantity_unit: str


class FlattenedProductsPreviewRequest(BaseModel):
    ingredients: list[IngredientPreviewItem]
