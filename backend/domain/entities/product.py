from dataclasses import dataclass, field

from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductCategoryId, ProductId


@dataclass
class Product:
    id: ProductId
    name: str
    recipe_unit: str
    purchase_unit: str
    price_per_purchase_unit: Money
    brand: str = field(default="")
    supplier: str = field(default="")
    weight_per_piece_g: float | None = field(default=None)
    conversion_factor: float = field(default=1.0)
    category_id: ProductCategoryId = field(default=ProductCategoryId(0))

    def compute_purchase(self, recipe_amount: float) -> tuple[Quantity, Money]:
        """Конвертирует количество в единицах рецепта в закупочную единицу и стоимость."""
        purchase_amount = recipe_amount / self.conversion_factor
        return (
            Quantity(purchase_amount, self.purchase_unit),
            self.price_per_purchase_unit * purchase_amount,
        )

    def purchase_cost(self, purchase_amount: float) -> Money:
        """Вычисляет стоимость для заданного количества в закупочных единицах."""
        return self.price_per_purchase_unit * purchase_amount
