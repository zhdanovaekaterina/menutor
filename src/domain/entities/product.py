from dataclasses import dataclass, field

from src.domain.value_objects.money import Money
from src.domain.value_objects.types import ProductId


@dataclass
class Product:
    id: ProductId
    name: str
    category: str
    recipe_unit: str
    purchase_unit: str
    price_per_purchase_unit: Money
    brand: str = field(default="")
    weight_per_piece_g: float | None = field(default=None)
    conversion_factor: float = field(default=1.0)
