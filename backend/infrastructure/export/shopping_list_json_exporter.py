import json
from typing import Any

from backend.domain.entities.shopping_list import ShoppingList

_UNIT_RU: dict[str, str] = {
    "g": "г", "kg": "кг", "ml": "мл", "l": "л",
    "pcs": "шт", "pack": "упак", "box": "кор",
    "tsp": "ч.л.", "tbsp": "ст.л.",
}


def _to_display(code: str) -> str:
    return _UNIT_RU.get(code, code)


class ShoppingListJsonExporter:
    """Exports a shopping list to structured JSON with Russian unit labels."""

    def _to_dict(self, shopping_list: ShoppingList) -> dict[str, Any]:
        categories: list[dict[str, Any]] = []
        for category, items in sorted(shopping_list.items_by_category().items()):
            category_items: list[dict[str, Any]] = []
            for item in items:
                rq = item.recipe_quantity if item.recipe_quantity is not None else item.quantity
                bq = item.buy_quantity
                entry: dict[str, Any] = {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "recipe_quantity": {
                        "amount": rq.amount,
                        "unit": rq.unit,
                        "unit_ru": _to_display(rq.unit),
                    },
                    "buy_quantity": {
                        "amount": bq.amount,
                        "unit": bq.unit,
                        "unit_ru": _to_display(bq.unit),
                    },
                    "cost": {
                        "amount": f"{item.cost.amount:.2f}",
                        "currency": item.cost.currency,
                    },
                    "purchased": item.purchased,
                }
                category_items.append(entry)
            categories.append({"category": category, "items": category_items})

        total = shopping_list.total_cost()
        return {
            "title": "Список покупок",
            "categories": categories,
            "total_cost": {
                "amount": f"{total.amount:.2f}",
                "currency": total.currency,
            },
        }

    def export_bytes(self, entities: list[Any]) -> bytes:
        shopping_list: ShoppingList = entities[0]
        return json.dumps(self._to_dict(shopping_list), ensure_ascii=False, indent=2).encode("utf-8")

    def example_bytes(self) -> bytes:
        example: dict[str, Any] = {
            "title": "Список покупок",
            "categories": [
                {
                    "category": "Молочные",
                    "items": [
                        {
                            "product_id": 1,
                            "product_name": "Молоко",
                            "recipe_quantity": {"amount": 1000.0, "unit": "ml", "unit_ru": "мл"},
                            "buy_quantity": {"amount": 1, "unit": "l", "unit_ru": "л"},
                            "cost": {"amount": "80.00", "currency": "RUB"},
                            "purchased": False,
                        }
                    ],
                }
            ],
            "total_cost": {"amount": "80.00", "currency": "RUB"},
        }
        return json.dumps(example, ensure_ascii=False, indent=2).encode("utf-8")

    def content_type(self) -> str:
        return "application/json"

    def file_extension(self) -> str:
        return "json"
