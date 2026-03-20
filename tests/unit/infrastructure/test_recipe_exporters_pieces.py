import csv
import io
import json

from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId, UserId
from backend.infrastructure.export.recipe_csv_exporter import RecipeCsvExporter
from backend.infrastructure.export.recipe_json_exporter import RecipeJsonExporter


def _pieces_recipe() -> Recipe:
    return Recipe(
        id=RecipeId(1),
        name="Котлеты",
        servings=5,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(500, "g"), order=0)],
        steps=[CookingStep(order=1, description="Лепить")],
        category_id=RecipeCategoryId(1),
        weight=400,
        user_id=UserId(1),
        total_pieces=10,
        pieces_per_portion=2,
    )


def _normal_recipe() -> Recipe:
    return Recipe(
        id=RecipeId(2),
        name="Борщ",
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(2), quantity=Quantity(300, "g"), order=0)],
        steps=[CookingStep(order=1, description="Варить")],
        category_id=RecipeCategoryId(1),
        weight=600,
        user_id=UserId(1),
    )


def _parse_csv(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8"))))


# --- JSON exporter tests ---

def test_json_export_pieces_recipe_contains_pieces_fields() -> None:
    item = json.loads(RecipeJsonExporter().export_bytes([_pieces_recipe()]))[0]
    assert item["total_pieces"] == 10
    assert item["pieces_per_portion"] == 2


def test_json_export_normal_recipe_pieces_fields_are_null() -> None:
    item = json.loads(RecipeJsonExporter().export_bytes([_normal_recipe()]))[0]
    assert item["total_pieces"] is None
    assert item["pieces_per_portion"] is None


def test_json_export_compact_pieces_recipe_contains_pieces_fields() -> None:
    item = json.loads(RecipeJsonExporter(compact=True).export_bytes([_pieces_recipe()]))[0]
    assert item["total_pieces"] == 10
    assert item["pieces_per_portion"] == 2


def test_json_export_compact_normal_recipe_omits_pieces_fields() -> None:
    item = json.loads(RecipeJsonExporter(compact=True).export_bytes([_normal_recipe()]))[0]
    assert "total_pieces" not in item
    assert "pieces_per_portion" not in item


# --- CSV exporter tests ---

def test_csv_export_headers_include_pieces_columns() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([]))
    assert "total_pieces" in rows[0]
    assert "pieces_per_portion" in rows[0]


def test_csv_export_pieces_recipe_columns_have_values() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([_pieces_recipe()]))
    header = rows[0]
    data_row = rows[1]
    tp_idx = header.index("total_pieces")
    ppp_idx = header.index("pieces_per_portion")
    assert data_row[tp_idx] == "10"
    assert data_row[ppp_idx] == "2"


def test_csv_export_normal_recipe_pieces_columns_are_empty() -> None:
    rows = _parse_csv(RecipeCsvExporter().export_bytes([_normal_recipe()]))
    header = rows[0]
    data_row = rows[1]
    tp_idx = header.index("total_pieces")
    ppp_idx = header.index("pieces_per_portion")
    assert data_row[tp_idx] == ""
    assert data_row[ppp_idx] == ""


def test_csv_example_bytes_includes_pieces_columns() -> None:
    rows = _parse_csv(RecipeCsvExporter().example_bytes())
    assert "total_pieces" in rows[0]
    assert "pieces_per_portion" in rows[0]
