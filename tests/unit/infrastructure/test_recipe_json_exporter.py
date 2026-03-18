import json

from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId, UserId
from backend.infrastructure.export.recipe_json_exporter import RecipeJsonExporter


def _recipe() -> Recipe:
    return Recipe(
        id=RecipeId(1),
        name="Блины",
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200, "g"), order=0)],
        steps=[CookingStep(order=1, description="Смешать")],
        category_id=RecipeCategoryId(1),
        weight=600,
        user_id=UserId(1),
    )


def test_full_export_fields() -> None:
    item = json.loads(RecipeJsonExporter().export_bytes([_recipe()]))[0]
    assert item["id"] == 1
    assert item["name"] == "Блины"
    assert item["category_id"] == 1
    assert item["servings"] == 4
    assert item["weight"] == 600
    assert len(item["ingredients"]) == 1
    assert item["ingredients"][0]["order"] == 0
    assert len(item["steps"]) == 1


def test_full_export_ingredient_fields() -> None:
    item = json.loads(RecipeJsonExporter().export_bytes([_recipe()]))[0]
    ing = item["ingredients"][0]
    assert ing["product_id"] == 1
    assert ing["quantity_amount"] == 200
    assert ing["quantity_unit"] == "g"


def test_compact_export_no_steps_or_category() -> None:
    item = json.loads(RecipeJsonExporter(compact=True).export_bytes([_recipe()]))[0]
    assert "steps" not in item
    assert "category_id" not in item
    assert "weight" not in item


def test_compact_export_ingredient_no_order() -> None:
    item = json.loads(RecipeJsonExporter(compact=True).export_bytes([_recipe()]))[0]
    ing = item["ingredients"][0]
    assert "order" not in ing
    assert ing["product_id"] == 1


def test_export_empty() -> None:
    assert json.loads(RecipeJsonExporter().export_bytes([])) == []


def test_example_bytes_full_is_parseable() -> None:
    data = json.loads(RecipeJsonExporter().example_bytes())
    assert len(data) == 1
    assert "steps" in data[0]


def test_example_bytes_compact_is_parseable() -> None:
    data = json.loads(RecipeJsonExporter(compact=True).example_bytes())
    assert len(data) == 1
    assert "steps" not in data[0]


def test_content_type() -> None:
    assert RecipeJsonExporter().content_type() == "application/json"


def test_file_extension() -> None:
    assert RecipeJsonExporter().file_extension() == "json"


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


def test_export_recipe_with_sub_recipe_includes_sub_recipe_id() -> None:
    item = json.loads(RecipeJsonExporter().export_bytes([_recipe_with_sub_recipe()]))[0]
    ing = item["ingredients"][0]
    assert ing["sub_recipe_id"] == 10
    assert "product_id" not in ing


def test_export_product_only_recipe_unchanged() -> None:
    item = json.loads(RecipeJsonExporter().export_bytes([_recipe()]))[0]
    ing = item["ingredients"][0]
    assert ing["product_id"] == 1
    assert "sub_recipe_id" not in ing
