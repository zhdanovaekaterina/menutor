from pydantic import BaseModel, model_validator


class MenuSlotSchema(BaseModel):
    day: int
    meal_type: str
    recipe_id: int | None = None
    product_id: int | None = None
    quantity: float | None = None
    unit: str | None = None
    servings_override: float | None = None

    @model_validator(mode="after")
    def exactly_one_item(self) -> "MenuSlotSchema":
        has_recipe = self.recipe_id is not None
        has_product = self.product_id is not None
        if has_recipe == has_product:
            raise ValueError(
                "Слот должен содержать ровно одно: recipe_id или product_id"
            )
        return self


class MenuCreate(BaseModel):
    name: str


class RemoveItemRequest(BaseModel):
    day: int
    meal_type: str
    recipe_id: int | None = None
    product_id: int | None = None


class MenuResponse(BaseModel):
    id: int
    name: str
    slots: list[MenuSlotSchema]
