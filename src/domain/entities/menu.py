from dataclasses import dataclass, field

from src.domain.value_objects.types import MenuId, ProductId, RecipeId


@dataclass
class MenuSlot:
    day: int  # 0–6 (Mon–Sun)
    meal_type: str
    recipe_id: RecipeId | None = field(default=None)
    product_id: ProductId | None = field(default=None)
    quantity: float | None = field(default=None)
    unit: str | None = field(default=None)
    servings_override: float | None = field(default=None)

    def __post_init__(self) -> None:
        has_recipe = self.recipe_id is not None
        has_product = self.product_id is not None
        if has_recipe == has_product:
            raise ValueError(
                "MenuSlot должен содержать ровно одно: recipe_id или product_id"
            )


@dataclass
class WeeklyMenu:
    id: MenuId
    name: str
    slots: list[MenuSlot] = field(default_factory=list)
