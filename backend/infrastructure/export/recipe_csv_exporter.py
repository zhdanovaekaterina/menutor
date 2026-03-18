import csv
import io
import json
from typing import Any

from backend.domain.entities.recipe import Recipe


class RecipeCsvExporter:
    """Exports Recipe entities to CSV bytes (ingredients and steps as JSON columns)."""

    _HEADERS = ["id", "name", "category_id", "servings", "weight", "ingredients_json", "steps_json"]

    def export_bytes(self, entities: list[Any]) -> bytes:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        for r in entities:
            recipe: Recipe = r
            ingredients: list[dict[str, Any]] = []
            for ing in recipe.ingredients:
                d: dict[str, Any] = {
                    "quantity_amount": ing.quantity.amount,
                    "quantity_unit": ing.quantity.unit,
                    "order": ing.order,
                }
                if ing.is_product:
                    assert ing.product_id is not None
                    d["product_id"] = int(ing.product_id)
                elif ing.is_sub_recipe:
                    assert ing.sub_recipe_id is not None
                    d["sub_recipe_id"] = int(ing.sub_recipe_id)
                ingredients.append(d)
            steps = [
                {"order": s.order, "description": s.description}
                for s in recipe.steps
            ]
            writer.writerow([
                recipe.id,
                recipe.name,
                recipe.category_id,
                recipe.servings,
                recipe.weight,
                json.dumps(ingredients, ensure_ascii=False),
                json.dumps(steps, ensure_ascii=False),
            ])
        return buf.getvalue().encode("utf-8")

    def example_bytes(self) -> bytes:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        writer.writerow([
            1, "Блины", 1, 4, 600,
            json.dumps([{"product_id": 1, "quantity_amount": 200, "quantity_unit": "g", "order": 0}]),
            json.dumps([{"order": 1, "description": "Смешать ингредиенты"}]),
        ])
        return buf.getvalue().encode("utf-8")

    def content_type(self) -> str:
        return "text/csv; charset=utf-8"

    def file_extension(self) -> str:
        return "csv"
