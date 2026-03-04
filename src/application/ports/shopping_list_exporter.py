from typing import Protocol

from src.domain.entities.shopping_list import ShoppingList


class TextShoppingListExporter(Protocol):
    def export(self, shopping_list: ShoppingList) -> str: ...


class CsvShoppingListExporter(Protocol):
    def export(self, shopping_list: ShoppingList, filepath: str) -> None: ...
