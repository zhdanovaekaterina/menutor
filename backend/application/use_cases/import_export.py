# DEPRECATED: Use ExportShoppingList (export_shopping_list.py) instead.
# These classes will be removed once the shopping list router is fully migrated.
from backend.application.ports.shopping_list_exporter import (
    CsvShoppingListExporter,
    TextShoppingListExporter,
)
from backend.domain.entities.shopping_list import ShoppingList


class ExportShoppingListAsText:
    def __init__(self, exporter: TextShoppingListExporter) -> None:
        self._exporter = exporter

    def execute(self, shopping_list: ShoppingList) -> str:
        return self._exporter.export(shopping_list)


class ExportShoppingListAsCsv:
    def __init__(self, exporter: CsvShoppingListExporter) -> None:
        self._exporter = exporter

    def execute(self, shopping_list: ShoppingList, filepath: str) -> None:
        self._exporter.export(shopping_list, filepath)
