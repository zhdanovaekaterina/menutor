from decimal import Decimal
from unittest.mock import MagicMock

from src.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from src.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductId


def _list_with_item() -> ShoppingList:
    return ShoppingList(items=[
        ShoppingListItem(
            product_id=ProductId(1),
            product_name="Мука",
            category="Сыпучие",
            quantity=Quantity(0.5, "kg"),
            cost=Money(Decimal("40")),
        )
    ])


def test_export_as_text_delegates_to_exporter() -> None:
    exporter = MagicMock()
    exporter.export.return_value = "Сыпучие:\n- Мука 0.5 kg"
    shopping_list = _list_with_item()

    result = ExportShoppingListAsText(exporter).execute(shopping_list)

    exporter.export.assert_called_once_with(shopping_list)
    assert result == "Сыпучие:\n- Мука 0.5 kg"


def test_export_as_csv_delegates_to_exporter() -> None:
    exporter = MagicMock()
    shopping_list = _list_with_item()

    ExportShoppingListAsCsv(exporter).execute(shopping_list, "/tmp/list.csv")

    exporter.export.assert_called_once_with(shopping_list, "/tmp/list.csv")
