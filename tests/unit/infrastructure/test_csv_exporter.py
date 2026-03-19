import csv
from decimal import Decimal
from pathlib import Path

import pytest

from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId
from backend.infrastructure.export.csv_exporter import ShoppingListCsvExporter


def _item(name: str = "Мука", category: str = "Сыпучие",
          qty: float = 1.0, unit: str = "kg", cost: float = 80.0) -> ShoppingListItem:
    return ShoppingListItem(
        product_id=ProductId(1),
        product_name=name,
        category=category,
        quantity=Quantity(qty, unit),
        cost=Money(Decimal(str(cost))),
    )


def _read_csv(filepath: str) -> list[list[str]]:
    with open(filepath, encoding="utf-8") as f:
        return list(csv.reader(f))


def test_csv_creates_file(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    ShoppingListCsvExporter().export(ShoppingList(items=[_item()]), fp)
    assert Path(fp).exists()


def test_csv_header_columns(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    ShoppingListCsvExporter().export(ShoppingList(items=[_item()]), fp)
    rows = _read_csv(fp)
    assert rows[0] == ["category", "name", "recipe_quantity", "unit", "buy_quantity", "cost", "purchased"]


def test_csv_single_item_row(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    ShoppingListCsvExporter().export(ShoppingList(items=[_item("Мука", "Сыпучие")]), fp)
    rows = _read_csv(fp)
    assert len(rows) == 2   # header + 1 item
    assert rows[1][0] == "Сыпучие"
    assert rows[1][1] == "Мука"
    assert rows[1][3] == "kg"


def test_csv_two_items(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    sl = ShoppingList(items=[
        _item("Мука",   "Сыпучие"),
        _item("Молоко", "Молочные", qty=2.0, unit="l"),
    ])
    ShoppingListCsvExporter().export(sl, fp)
    rows = _read_csv(fp)
    assert len(rows) == 3


def test_csv_cost_formatted_to_two_decimals(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    ShoppingListCsvExporter().export(ShoppingList(items=[_item(cost=80.5)]), fp)
    rows = _read_csv(fp)
    assert rows[1][5] == "80.50"


def test_csv_empty_list_only_header(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    ShoppingListCsvExporter().export(ShoppingList(), fp)
    rows = _read_csv(fp)
    assert len(rows) == 1


def test_export_bytes_header() -> None:
    data = ShoppingListCsvExporter().export_bytes([ShoppingList()])
    rows = list(csv.reader(data.decode("utf-8").splitlines()))
    assert rows[0] == ["category", "name", "recipe_quantity", "unit", "buy_quantity", "cost", "purchased"]


def test_export_bytes_single_item() -> None:
    sl = ShoppingList(items=[_item("Мука", "Сыпучие")])
    data = ShoppingListCsvExporter().export_bytes([sl])
    rows = list(csv.reader(data.decode("utf-8").splitlines()))
    assert len(rows) == 2
    assert rows[1][1] == "Мука"


def test_csv_buy_quantity_rounds_up(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    ShoppingListCsvExporter().export(ShoppingList(items=[_item(qty=1.3)]), fp)
    rows = _read_csv(fp)
    assert rows[1][2] == "1.3"   # recipe_quantity: original amount
    assert rows[1][4] == "2"     # buy_quantity: ceil(1.3) == 2


def test_example_bytes_is_parseable() -> None:
    data = ShoppingListCsvExporter().example_bytes()
    rows = list(csv.reader(data.decode("utf-8").splitlines()))
    assert rows[0][0] == "category"
    assert len(rows) == 2
