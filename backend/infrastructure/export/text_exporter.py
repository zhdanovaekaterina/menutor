from typing import Any

from backend.domain.entities.shopping_list import ShoppingList

_UNIT_RU: dict[str, str] = {
    "g": "г", "kg": "кг", "ml": "мл", "l": "л",
    "pcs": "шт", "pack": "упак", "box": "кор",
    "tsp": "ч.л.", "tbsp": "ст.л.",
}


def _to_display(code: str) -> str:
    return _UNIT_RU.get(code, code)


class ShoppingListTextExporter:
    """Formats a shopping list as human-readable text (messenger-friendly)."""

    def export(self, shopping_list: ShoppingList) -> str:
        lines: list[str] = ["Список покупок", ""]

        for category, items in sorted(shopping_list.items_by_category().items()):
            lines.append(f"{category}:")
            for item in items:
                rq = item.recipe_quantity if item.recipe_quantity is not None else item.quantity
                bq = item.buy_quantity
                recipe_qty_str = f"{rq.amount:g} {_to_display(rq.unit)}"
                buy_qty_str = f"{bq.amount:g} {_to_display(bq.unit)}"
                cost_str = f"{item.cost.amount:.2f} руб"
                lines.append(
                    f"• {item.product_name} — купить: {buy_qty_str} (рецепт: {recipe_qty_str}) — {cost_str}"
                )
            lines.append("")

        total = shopping_list.total_cost()
        lines.append(f"Итого: {total.amount:.2f} руб")
        return "\n".join(lines)

    def export_bytes(self, entities: list[Any]) -> bytes:
        shopping_list: ShoppingList = entities[0]
        return self.export(shopping_list).encode("utf-8")

    def example_bytes(self) -> bytes:
        return (
            "Список покупок\n\nМолочные:\n• Молоко — 1 л — 80.00 руб\n\nИтого: 80.00 руб"
        ).encode("utf-8")

    def content_type(self) -> str:
        return "text/plain; charset=utf-8"

    def file_extension(self) -> str:
        return "txt"
