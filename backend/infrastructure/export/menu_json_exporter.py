import json
from typing import Any

from backend.domain.entities.menu import WeeklyMenu


class MenuJsonExporter:
    """Exports WeeklyMenu entities to JSON bytes."""

    def _slot_to_dict(self, slot: Any) -> dict[str, Any]:
        return {
            "day": slot.day,
            "meal_type": slot.meal_type,
            "recipe_id": slot.recipe_id,
            "product_id": slot.product_id,
            "quantity": slot.quantity,
            "unit": slot.unit,
            "servings_override": slot.servings_override,
            "position": slot.position,
        }

    def _to_dict(self, menu: WeeklyMenu) -> dict[str, Any]:
        return {
            "id": menu.id,
            "name": menu.name,
            "slots": [self._slot_to_dict(s) for s in menu.slots],
        }

    def export_bytes(self, entities: list[Any]) -> bytes:
        data = [self._to_dict(m) for m in entities]
        return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    def example_bytes(self) -> bytes:
        examples = [
            {
                "id": 1,
                "name": "Меню на неделю",
                "slots": [
                    {
                        "day": 0, "meal_type": "завтрак",
                        "recipe_id": 1, "product_id": None,
                        "quantity": None, "unit": None,
                        "servings_override": None, "position": 0,
                    },
                    {
                        "day": 0, "meal_type": "обед",
                        "recipe_id": None, "product_id": 2,
                        "quantity": 250.0, "unit": "g",
                        "servings_override": None, "position": 0,
                    },
                ],
            }
        ]
        return json.dumps(examples, ensure_ascii=False, indent=2).encode("utf-8")

    def content_type(self) -> str:
        return "application/json"

    def file_extension(self) -> str:
        return "json"
