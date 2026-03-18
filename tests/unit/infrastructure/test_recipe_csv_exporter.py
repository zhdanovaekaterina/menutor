import csv
import io
import json

from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId, UserId
from backend.infrastructure.export.recipe_csv_exporter import RecipeCsvExporter


def _recipe(id: int = 1, name: str = "Блины") -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name=name,
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200, "g"), order=0)],
        steps=[CookingStep(order=1, description="Смешать")],
        category_id=RecipeCategoryId(1),
        weight=600,
        user_id=UserId(1),
    )


def _parse_csv(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8"))))


def test_export_bytes_header() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([]))
    assert rows[0] == ["id", "name", "category_id", "servings", "weight", "ingredients_json", "steps_json"]


def test_export_bytes_single_recipe() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([_recipe()]))
    assert len(rows) == 2
    assert rows[1][0] == "1"
    assert rows[1][1] == "Блины"
    assert rows[1][3] == "4"


def test_export_bytes_ingredients_json() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([_recipe()]))
    ingredients = json.loads(rows[1][5])
    assert len(ingredients) == 1
    assert ingredients[0]["product_id"] == 1
    assert ingredients[0]["quantity_amount"] == 200
    assert ingredients[0]["quantity_unit"] == "g"
    assert ingredients[0]["order"] == 0


def test_export_bytes_steps_json() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([_recipe()]))
    steps = json.loads(rows[1][6])
    assert steps[0]["order"] == 1
    assert steps[0]["description"] == "Смешать"


def test_export_bytes_empty() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([]))
    assert len(rows) == 1


def test_example_bytes_is_parseable() -> None:
    rows = _parse_csv(RecipeCsvExporter().example_bytes())
    assert len(rows) == 2
    assert rows[1][1] == "Блины"
    json.loads(rows[1][5])  # ingredients_json must be valid JSON
    json.loads(rows[1][6])  # steps_json must be valid JSON


def test_content_type() -> None:
    assert RecipeCsvExporter().content_type() == "text/csv; charset=utf-8"


def test_file_extension() -> None:
    assert RecipeCsvExporter().file_extension() == "csv"


def _recipe_with_sub_recipe() -> Recipe:
    return Recipe(
        id=RecipeId(2),
        name="Тесто для блинов",
        servings=4,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(10), quantity=Quantity(1, "serv"), order=0)],
        steps=[],
        category_id=RecipeCategoryId(1),
        weight=0,
        user_id=UserId(1),
    )


def test_export_recipe_with_sub_recipe_ingredient_in_csv() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([_recipe_with_sub_recipe()]))
    ingredients = json.loads(rows[1][5])
    assert len(ingredients) == 1
    ing = ingredients[0]
    assert ing["sub_recipe_id"] == 10
    assert "product_id" not in ing


def test_export_product_only_recipe_csv_unchanged() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([_recipe()]))
    ingredients = json.loads(rows[1][5])
    assert len(ingredients) == 1
    ing = ingredients[0]
    assert ing["product_id"] == 1
    assert "sub_recipe_id" not in ing
