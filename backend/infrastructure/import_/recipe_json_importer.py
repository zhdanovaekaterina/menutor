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

_REQUIRED = {"name", "servings"}


class RecipeJsonImporter:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def import_from_bytes(self, data: bytes, user_id: UserId) -> ImportResult:
        if not data.strip():
            return ImportResult(created=0, updated=0)

        try:
            rows = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ImportValidationError(f"Некорректный JSON: {e}") from e

        if not isinstance(rows, list):
            raise ImportValidationError("JSON должен быть массивом объектов")

        created = updated = 0
        for i, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ImportValidationError(f"Элемент {i}: ожидается объект")

            missing = _REQUIRED - set(row.keys())
            if missing:
                raise ImportValidationError(
                    f"Элемент {i}: отсутствуют обязательные поля: {', '.join(sorted(missing))}"
                )
            if not str(row.get("name", "")).strip():
                raise ImportValidationError(f"Элемент {i}: поле 'name' не может быть пустым")

            try:
                servings = int(row["servings"])
            except (ValueError, TypeError):
                raise ImportValidationError(f"Элемент {i}: некорректное значение 'servings'")

            try:
                raw_ingredients = row.get("ingredients") or []
                ingredients = [
                    RecipeIngredient(
                        product_id=ProductId(int(ing["product_id"])),
                        quantity=Quantity(float(ing["quantity_amount"]), ing["quantity_unit"]),
                        order=int(ing.get("order", 0)),
                    )
                    for ing in raw_ingredients
                    if ing.get("product_id") is not None
                ]
            except Exception as e:
                raise ImportValidationError(f"Элемент {i}: некорректный ингредиент: {e}") from e

            try:
                raw_steps = row.get("steps") or []
                steps = [
                    CookingStep(order=int(s["order"]), description=str(s["description"]))
                    for s in raw_steps
                ]
            except Exception as e:
                raise ImportValidationError(f"Элемент {i}: некорректный шаг: {e}") from e

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
                name=str(row["name"]).strip(),
                servings=servings,
                ingredients=ingredients,
                steps=steps,
                category_id=RecipeCategoryId(int(row.get("category_id") or 0)),
                weight=int(row.get("weight") or 0),
                user_id=user_id,
            )
            self._repo.save(recipe)

        return ImportResult(created=created, updated=updated)

    def supported_extensions(self) -> list[str]:
        return ["json"]
