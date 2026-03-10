from backend.domain.entities.shopping_list import ShoppingList
from backend.presentation.units import to_display


class ShoppingListTextExporter:
    """Formats a shopping list as human-readable text (messenger-friendly)."""

    def export(self, shopping_list: ShoppingList) -> str:
        lines: list[str] = ["Список покупок", ""]

        for category, items in sorted(shopping_list.items_by_category().items()):
            lines.append(f"{category}:")
            for item in items:
                qty_str = f"{item.quantity.amount:g} {to_display(item.quantity.unit)}"
                cost_str = f"{item.cost.amount:.2f} руб"
                lines.append(f"• {item.product_name} — {qty_str} — {cost_str}")
            lines.append("")

        total = shopping_list.total_cost()
        lines.append(f"Итого: {total.amount:.2f} руб")
        return "\n".join(lines)
