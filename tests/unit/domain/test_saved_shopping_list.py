from datetime import datetime
from decimal import Decimal

from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import (
    ProductId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)


def _item(
    item_id: int = 1,
    product_id: int | None = 1,
    product_name: str = "Молоко",
    category: str = "Молочные",
    quantity_amount: float = 1.0,
    quantity_unit: str = "l",
    buy_quantity_amount: float = 1.0,
    buy_quantity_unit: str = "l",
    buy_quantity_overridden: bool = False,
    cost_amount: str = "89.90",
    purchased: bool = False,
    recipe_quantity_amount: float | None = None,
    recipe_quantity_unit: str | None = None,
    item_order: int = 0,
) -> SavedShoppingListItem:
    return SavedShoppingListItem(
        id=SavedShoppingListItemId(item_id),
        product_id=ProductId(product_id) if product_id is not None else None,
        product_name=product_name,
        category=category,
        quantity=Quantity(quantity_amount, quantity_unit),
        buy_quantity=Quantity(buy_quantity_amount, buy_quantity_unit),
        buy_quantity_overridden=buy_quantity_overridden,
        cost=Money(Decimal(cost_amount)),
        purchased=purchased,
        recipe_quantity=Quantity(recipe_quantity_amount, recipe_quantity_unit)
        if recipe_quantity_amount is not None and recipe_quantity_unit is not None
        else None,
        item_order=item_order,
    )


def _shopping_list(
    list_id: int = 1,
    user_id: int = 1,
    name: str = "Список на неделю",
    items: list[SavedShoppingListItem] | None = None,
) -> SavedShoppingList:
    return SavedShoppingList(
        id=SavedShoppingListId(list_id),
        user_id=UserId(user_id),
        name=name,
        items=items if items is not None else [],
        created_at=datetime(2026, 3, 21, 12, 0, 0),
        updated_at=datetime(2026, 3, 21, 12, 0, 0),
    )


class TestSavedShoppingListCreation:
    def test_create_with_items(self) -> None:
        items = [
            _item(item_id=1, product_name="Молоко", category="Молочные"),
            _item(item_id=2, product_name="Хлеб", category="Выпечка", cost_amount="45.00"),
        ]
        sl = _shopping_list(items=items)

        assert sl.id == SavedShoppingListId(1)
        assert sl.user_id == UserId(1)
        assert sl.name == "Список на неделю"
        assert len(sl.items) == 2
        assert sl.items[0].product_name == "Молоко"
        assert sl.items[1].product_name == "Хлеб"

    def test_create_empty_list(self) -> None:
        sl = _shopping_list(items=[])
        assert sl.items == []
        assert sl.name == "Список на неделю"


class TestTotalCost:
    def test_total_cost_sums_items(self) -> None:
        items = [
            _item(item_id=1, cost_amount="89.90"),
            _item(item_id=2, cost_amount="45.00"),
            _item(item_id=3, cost_amount="120.50"),
        ]
        sl = _shopping_list(items=items)

        total = sl.total_cost()
        assert total.amount == Decimal("255.40")
        assert total.currency == "RUB"

    def test_total_cost_empty_list(self) -> None:
        sl = _shopping_list(items=[])
        total = sl.total_cost()
        assert total.amount == Decimal("0")


class TestItemsByCategory:
    def test_groups_correctly(self) -> None:
        items = [
            _item(item_id=1, product_name="Молоко", category="Молочные"),
            _item(item_id=2, product_name="Сыр", category="Молочные"),
            _item(item_id=3, product_name="Хлеб", category="Выпечка"),
        ]
        sl = _shopping_list(items=items)

        by_cat = sl.items_by_category()
        assert len(by_cat) == 2
        assert len(by_cat["Молочные"]) == 2
        assert len(by_cat["Выпечка"]) == 1
        assert by_cat["Молочные"][0].product_name == "Молоко"
        assert by_cat["Молочные"][1].product_name == "Сыр"

    def test_empty_list_returns_empty_dict(self) -> None:
        sl = _shopping_list(items=[])
        assert sl.items_by_category() == {}


class TestSavedShoppingListItemNullProduct:
    def test_item_with_none_product_id(self) -> None:
        item = _item(product_id=None, product_name="Удаленный продукт")
        assert item.product_id is None
        assert item.product_name == "Удаленный продукт"
