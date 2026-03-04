import csv
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductId
from src.infrastructure.export.csv_exporter import ShoppingListCsvExporter


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
    assert rows[0] == ["category", "name", "quantity", "unit", "cost", "purchased"]


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
    assert rows[1][4] == "80.50"


def test_csv_empty_list_only_header(tmp_path: Path) -> None:
    fp = str(tmp_path / "list.csv")
    ShoppingListCsvExporter().export(ShoppingList(), fp)
    rows = _read_csv(fp)
    assert len(rows) == 1
