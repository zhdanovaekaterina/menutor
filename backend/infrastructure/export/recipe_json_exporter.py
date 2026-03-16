import json
from typing import Any

from backend.domain.entities.recipe import Recipe


class RecipeJsonExporter:
    """Exports Recipe entities to JSON bytes.

    compact=False (default): full format matching RecipeResponse schema.
    compact=True: only id, name, servings, and simplified ingredients (no steps, category, weight).
    """

    def __init__(self, compact: bool = False) -> None:
        self._compact = compact

    def _to_dict(self, recipe: Recipe) -> dict[str, Any]:
        ingredients = [
            {
                "product_id": ing.product_id,
                "quantity_amount": ing.quantity.amount,
                "quantity_unit": ing.quantity.unit,
                "order": ing.order,
            }
            for ing in recipe.ingredients
        ]
        if self._compact:
            return {
                "id": recipe.id,
                "name": recipe.name,
                "servings": recipe.servings,
                "ingredients": [
                    {
                        "product_id": ing["product_id"],
                        "quantity_amount": ing["quantity_amount"],
                        "quantity_unit": ing["quantity_unit"],
                    }
                    for ing in ingredients
                ],
            }
        return {
            "id": recipe.id,
            "name": recipe.name,
            "category_id": recipe.category_id,
            "servings": recipe.servings,
            "weight": recipe.weight,
            "ingredients": ingredients,
            "steps": [
                {"order": s.order, "description": s.description}
                for s in recipe.steps
            ],
        }

    def export_bytes(self, entities: list[Any]) -> bytes:
        data = [self._to_dict(r) for r in entities]
        return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    def example_bytes(self) -> bytes:
        if self._compact:
            examples: list[dict[str, Any]] = [
                {
                    "id": 1, "name": "Блины", "servings": 4,
                    "ingredients": [{"product_id": 1, "quantity_amount": 200, "quantity_unit": "g"}],
                }
            ]
        else:
            examples = [
                {
                    "id": 1, "name": "Блины", "category_id": 1, "servings": 4, "weight": 600,
                    "ingredients": [
                        {"product_id": 1, "quantity_amount": 200, "quantity_unit": "g", "order": 0}
                    ],
                    "steps": [{"order": 1, "description": "Смешать ингредиенты"}],
                }
            ]
        return json.dumps(examples, ensure_ascii=False, indent=2).encode("utf-8")

    def content_type(self) -> str:
        return "application/json"

    def file_extension(self) -> str:
        return "json"
