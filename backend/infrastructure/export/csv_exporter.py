import csv

from backend.domain.entities.shopping_list import ShoppingList


class ShoppingListCsvExporter:
    """Exports a shopping list to a UTF-8 CSV file."""

    def export(self, shopping_list: ShoppingList, filepath: str) -> None:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["category", "name", "quantity", "unit", "cost", "purchased"])
            for item in shopping_list.items:
                writer.writerow([
                    item.category,
                    item.product_name,
                    f"{item.quantity.amount:g}",
                    item.quantity.unit,
                    f"{item.cost.amount:.2f}",
                    item.purchased,
                ])
