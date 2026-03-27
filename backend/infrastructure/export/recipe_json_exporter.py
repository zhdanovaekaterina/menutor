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
        if self._compact:
            compact_ingredients: list[dict[str, Any]] = []
            for ing_dict in ingredients:
                entry: dict[str, Any] = {
                    "quantity_amount": ing_dict["quantity_amount"],
                    "quantity_unit": ing_dict["quantity_unit"],
                }
                if "product_id" in ing_dict:
                    entry["product_id"] = ing_dict["product_id"]
                elif "sub_recipe_id" in ing_dict:
                    entry["sub_recipe_id"] = ing_dict["sub_recipe_id"]
                compact_ingredients.append(entry)
            result: dict[str, Any] = {
                "id": recipe.id,
                "name": recipe.name,
                "servings": recipe.servings,
                "ingredients": compact_ingredients,
            }
            if recipe.total_pieces is not None:
                result["total_pieces"] = recipe.total_pieces
                result["pieces_per_portion"] = recipe.pieces_per_portion
            return result
        return {
            "id": recipe.id,
            "name": recipe.name,
            "category_id": recipe.category_id,
            "servings": recipe.servings,
            "weight": recipe.weight,
            "total_pieces": recipe.total_pieces,
            "pieces_per_portion": recipe.pieces_per_portion,
            "link": recipe.link,
            "comment": recipe.comment,
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
