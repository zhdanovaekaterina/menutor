from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import (
    MenuId,
    ProductId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)


@dataclass
class SavedShoppingListItem:
    id: SavedShoppingListItemId
    product_id: ProductId | None
    product_name: str
    category: str
    quantity: Quantity
    buy_quantity: Quantity
    buy_quantity_overridden: bool
    cost: Money
    purchased: bool
    recipe_quantity: Quantity | None
    item_order: int


@dataclass
class SavedShoppingList:
    id: SavedShoppingListId
    user_id: UserId
    name: str
    items: list[SavedShoppingListItem] = field(default_factory=list)
    source_menu_id: MenuId | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def total_cost(self) -> Money:
        if not self.items:
            return Money(Decimal("0"))
        total = self.items[0].cost
        for item in self.items[1:]:
            total = total + item.cost
        return total

    def items_by_category(self) -> dict[str, list[SavedShoppingListItem]]:
        result: dict[str, list[SavedShoppingListItem]] = {}
        for item in self.items:
            result.setdefault(item.category, []).append(item)
        return result
