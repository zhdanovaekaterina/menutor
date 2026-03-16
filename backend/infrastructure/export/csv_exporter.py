import csv
import io
from typing import Any

from backend.domain.entities.shopping_list import ShoppingList

_HEADERS = ["category", "name", "quantity", "unit", "cost", "purchased"]


class ShoppingListCsvExporter:
    """Exports a shopping list to CSV."""

    def _write_rows(self, writer: csv.writer, shopping_list: ShoppingList) -> None:  # type: ignore[type-arg]
        writer.writerow(_HEADERS)
        for item in shopping_list.items:
            writer.writerow([
                item.category,
                item.product_name,
                f"{item.quantity.amount:g}",
                item.quantity.unit,
                f"{item.cost.amount:.2f}",
                item.purchased,
            ])

    def export(self, shopping_list: ShoppingList, filepath: str) -> None:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            self._write_rows(csv.writer(f), shopping_list)

    def export_bytes(self, entities: list[Any]) -> bytes:
        shopping_list: ShoppingList = entities[0]
        buf = io.StringIO()
        self._write_rows(csv.writer(buf), shopping_list)
        return buf.getvalue().encode("utf-8")

    def example_bytes(self) -> bytes:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(_HEADERS)
        writer.writerow(["Молочные", "Молоко", "1", "l", "80.00", False])
        return buf.getvalue().encode("utf-8")

    def content_type(self) -> str:
        return "text/csv; charset=utf-8"

    def file_extension(self) -> str:
        return "csv"
