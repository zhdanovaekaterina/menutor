import csv
import io
import json

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import ImportValidationError
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    ProductId,
    RecipeCategoryId,
    RecipeId,
    UserId,
)

_REQUIRED = {"name", "category_id", "servings"}


class RecipeCsvImporter:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def import_from_bytes(self, data: bytes, user_id: UserId) -> ImportResult:
        if not data.strip():
            return ImportResult(created=0, updated=0)

        try:
            reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
        except Exception as e:
            raise ImportValidationError(f"Не удалось прочитать CSV: {e}") from e

        created = updated = 0
        errors: list[str] = []
        for i, row in enumerate(reader, start=2):
            missing = _REQUIRED - set(row.keys())
            if missing:
                raise ImportValidationError(
                    f"Строка {i}: отсутствуют обязательные поля: {', '.join(sorted(missing))}"
                )
            if not row.get("name", "").strip():
                raise ImportValidationError(f"Строка {i}: поле 'name' не может быть пустым")

            try:
                servings = int(row["servings"])
            except ValueError:
                raise ImportValidationError(f"Строка {i}: некорректное значение 'servings'")

            try:
                category_id = int(row["category_id"])
            except ValueError:
                raise ImportValidationError(f"Строка {i}: некорректное значение 'category_id'")

            try:
                weight = int(row.get("weight") or 0)
            except ValueError:
                raise ImportValidationError(f"Строка {i}: некорректное значение 'weight'")

            try:
                raw_ingredients = json.loads(row.get("ingredients_json") or "[]")
                ingredients: list[RecipeIngredient] = []
                for ing_data in raw_ingredients:
                    if ing_data.get("product_id") is not None:
                        ingredients.append(RecipeIngredient(
                            product_id=ProductId(int(ing_data["product_id"])),
                            quantity=Quantity(
                                float(ing_data["quantity_amount"]),
                                ing_data["quantity_unit"],
                            ),
                            order=int(ing_data.get("order", 0)),
                        ))
                    elif "sub_recipe_id" in ing_data:
                        sub_id = RecipeId(int(ing_data["sub_recipe_id"]))
                        sub = self._repo.get_by_id(sub_id)
                        if sub is not None and sub.user_id == user_id:
                            ingredients.append(RecipeIngredient(
                                sub_recipe_id=sub_id,
                                quantity=Quantity(
                                    float(ing_data["quantity_amount"]),
                                    ing_data["quantity_unit"],
                                ),
                                order=int(ing_data.get("order", 0)),
                            ))
                        else:
                            errors.append(
                                f"Рецепт-ингредиент с ID {sub_id} не найден, пропущен"
                            )
            except Exception as e:
                raise ImportValidationError(f"Строка {i}: некорректный 'ingredients_json': {e}") from e

            try:
                raw_steps = json.loads(row.get("steps_json") or "[]")
                steps = [
                    CookingStep(order=int(s["order"]), description=str(s["description"]))
                    for s in raw_steps
                ]
            except Exception as e:
                raise ImportValidationError(f"Строка {i}: некорректный 'steps_json': {e}") from e

            raw_id = int(row.get("id") or 0)
            existing = self._repo.get_by_id(RecipeId(raw_id)) if raw_id > 0 else None
            if existing is not None and existing.user_id == user_id:
                entity_id = existing.id
                updated += 1
            else:
                entity_id = RecipeId(0)
                created += 1

            recipe = Recipe(
                id=entity_id,
                name=row["name"].strip(),
                servings=servings,
                ingredients=ingredients,
                steps=steps,
                category_id=RecipeCategoryId(category_id),
                weight=weight,
                user_id=user_id,
                total_pieces=int(row["total_pieces"]) if row.get("total_pieces") else None,
                pieces_per_portion=int(row["pieces_per_portion"]) if row.get("pieces_per_portion") else None,
            )
            self._repo.save(recipe)

        return ImportResult(created=created, updated=updated, errors=errors)

    def supported_extensions(self) -> list[str]:
        return ["csv"]
