from decimal import Decimal

from src.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductId
from src.infrastructure.export.text_exporter import ShoppingListTextExporter


def _item(name: str, category: str, qty: float, unit: str, cost: float) -> ShoppingListItem:
    return ShoppingListItem(
        product_id=ProductId(1),
        product_name=name,
        category=category,
        quantity=Quantity(qty, unit),
        cost=Money(Decimal(str(cost))),
    )


def test_export_contains_category_header() -> None:
    sl = ShoppingList(items=[_item("Мука", "Сыпучие", 1.0, "kg", 80)])
    assert "Сыпучие:" in ShoppingListTextExporter().export(sl)


def test_export_contains_product_name() -> None:
    sl = ShoppingList(items=[_item("Мука", "Сыпучие", 1.0, "kg", 80)])
    assert "Мука" in ShoppingListTextExporter().export(sl)


def test_export_groups_multiple_categories() -> None:
    sl = ShoppingList(items=[
        _item("Мука",   "Сыпучие",  1.0,  "kg", 80),
        _item("Молоко", "Молочные", 2.0,  "l",  180),
    ])
    result = ShoppingListTextExporter().export(sl)
    assert "Сыпучие:" in result
    assert "Молочные:" in result


def test_export_total_cost_sum() -> None:
    sl = ShoppingList(items=[
        _item("Мука",   "Сыпучие",  1.0, "kg", 80),
        _item("Молоко", "Молочные", 2.0, "l",  180),
    ])
    assert "Итого: 260.00 руб" in ShoppingListTextExporter().export(sl)


def test_export_quantity_without_trailing_zeros() -> None:
    sl = ShoppingList(items=[_item("Мука", "Сыпучие", 1.0, "kg", 80)])
    result = ShoppingListTextExporter().export(sl)
    assert "1 kg" in result   # not "1.0 kg"


def test_export_fractional_quantity() -> None:
    sl = ShoppingList(items=[_item("Масло", "Молочные", 0.5, "kg", 90)])
    assert "0.5 kg" in ShoppingListTextExporter().export(sl)


def test_export_empty_list_shows_zero_total() -> None:
    result = ShoppingListTextExporter().export(ShoppingList())
    assert "Итого: 0.00 руб" in result
