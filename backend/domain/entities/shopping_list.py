from dataclasses import dataclass, field
from decimal import Decimal

from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId


@dataclass
class ShoppingListItem:
    product_id: ProductId
    product_name: str
    category: str
    quantity: Quantity
    cost: Money
    purchased: bool = field(default=False)
    recipe_quantity: Quantity | None = field(default=None)


@dataclass
class ShoppingList:
    items: list[ShoppingListItem] = field(default_factory=list)

    def total_cost(self) -> Money:
        if not self.items:
            return Money(Decimal("0"))
        total = self.items[0].cost
        for item in self.items[1:]:
            total = total + item.cost
        return total

    def items_by_category(self) -> dict[str, list[ShoppingListItem]]:
        result: dict[str, list[ShoppingListItem]] = {}
        for item in self.items:
            result.setdefault(item.category, []).append(item)
        return result
