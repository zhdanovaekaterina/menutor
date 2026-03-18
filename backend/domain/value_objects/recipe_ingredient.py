from dataclasses import dataclass, field

from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId, RecipeId


@dataclass(frozen=True)
class RecipeIngredient:
    product_id: ProductId | None = None
    sub_recipe_id: RecipeId | None = None
    quantity: Quantity = field(default_factory=lambda: Quantity(0, "g"))
    order: int = 0

    def __post_init__(self) -> None:
        has_product = self.product_id is not None
        has_sub_recipe = self.sub_recipe_id is not None
        if has_product == has_sub_recipe:
            raise InvalidEntityError(
                "RecipeIngredient must reference exactly one of product_id or sub_recipe_id"
            )

    @property
    def is_sub_recipe(self) -> bool:
        return self.sub_recipe_id is not None

    @property
    def is_product(self) -> bool:
        return self.product_id is not None
