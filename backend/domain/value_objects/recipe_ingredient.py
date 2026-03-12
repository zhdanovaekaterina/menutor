from dataclasses import dataclass

from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId


@dataclass(frozen=True)
class RecipeIngredient:
    product_id: ProductId
    quantity: Quantity
