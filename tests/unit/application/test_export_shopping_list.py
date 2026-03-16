from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.export_shopping_list import ExportShoppingList
from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import MenuId, ProductId, UserId
from backend.infrastructure.export.registry import ExportRegistry

UID = UserId(1)
MID = MenuId(1)


def _shopping_list() -> ShoppingList:
    return ShoppingList(items=[
        ShoppingListItem(
            product_id=ProductId(1),
            product_name="Молоко",
            category="Молочные",
            quantity=Quantity(1.0, "l"),
            cost=Money(Decimal("80")),
        )
    ])


def _make_use_case(
    exporter: MagicMock | None = None,
    shopping_list: ShoppingList | None = None,
    format: str = "txt",
) -> ExportShoppingList:
    registry = ExportRegistry()
    if exporter:
        registry.register("shopping_list", format, exporter)

    generate = MagicMock()
    generate.execute.return_value = shopping_list or _shopping_list()

    return ExportShoppingList(registry, generate)


def _mock_exporter(ext: str = "txt", ct: str = "text/plain; charset=utf-8") -> MagicMock:
    m = MagicMock()
    m.export_bytes.return_value = "Список покупок".encode("utf-8")
    m.content_type.return_value = ct
    m.file_extension.return_value = ext
    return m


def test_execute_returns_bytes_content_type_filename() -> None:
    exporter = _mock_exporter()
    uc = _make_use_case(exporter=exporter)
    data, ct, filename = uc.execute(MID, UID, "txt")
    assert data == "Список покупок".encode("utf-8")
    assert ct == "text/plain; charset=utf-8"
    assert filename == "shopping_list.txt"


def test_execute_calls_generate_with_menu_id_and_user_id() -> None:
    exporter = _mock_exporter()
    generate = MagicMock()
    generate.execute.return_value = _shopping_list()
    registry = ExportRegistry()
    registry.register("shopping_list", "txt", exporter)
    uc = ExportShoppingList(registry, generate)
    uc.execute(MID, UID, "txt")
    generate.execute.assert_called_once_with(MID, UID)


def test_execute_passes_shopping_list_to_exporter() -> None:
    exporter = _mock_exporter()
    sl = _shopping_list()
    uc = _make_use_case(exporter=exporter, shopping_list=sl)
    uc.execute(MID, UID, "txt")
    exporter.export_bytes.assert_called_once_with([sl])


def test_execute_unknown_format_raises() -> None:
    uc = _make_use_case()
    with pytest.raises(ImportValidationError, match="pdf"):
        uc.execute(MID, UID, "pdf")
