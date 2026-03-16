import csv
import io
import json
from unittest.mock import MagicMock

import pytest

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId, UserId
from backend.infrastructure.import_.recipe_csv_importer import RecipeCsvImporter

UID = UserId(1)


def _make_csv(*rows: dict) -> bytes:
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _row(**kwargs) -> dict:
    defaults = dict(
        id="", name="Блины", category_id="1", servings="4", weight="600",
        ingredients_json=json.dumps([
            {"product_id": 1, "quantity_amount": 200, "quantity_unit": "g", "order": 0}
        ]),
        steps_json=json.dumps([{"order": 1, "description": "Смешать"}]),
    )
    defaults.update(kwargs)
    return defaults


def _mock_repo(existing: Recipe | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda r: r
    return repo


def _existing_recipe(id: int = 1) -> Recipe:
    return Recipe(
        id=RecipeId(id), name="Блины", servings=4,
        category_id=RecipeCategoryId(1), user_id=UID,
    )


def test_create_new_recipe() -> None:
    result = RecipeCsvImporter(_mock_repo()).import_from_bytes(_make_csv(_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    repo = _mock_repo()
    RecipeCsvImporter(repo).import_from_bytes(_make_csv(_row()), UID)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.id == RecipeId(0)
    assert saved.name == "Блины"
    assert len(saved.ingredients) == 1
    assert len(saved.steps) == 1


def test_update_existing_recipe() -> None:
    repo = _mock_repo(existing=_existing_recipe(id=5))
    result = RecipeCsvImporter(repo).import_from_bytes(_make_csv(_row(id="5")), UID)
    assert result == ImportResult(created=0, updated=1)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.id == RecipeId(5)


def test_id_belonging_to_other_user_creates_new() -> None:
    other = Recipe(
        id=RecipeId(5), name="Блины", servings=4,
        category_id=RecipeCategoryId(1), user_id=UserId(99),
    )
    repo = _mock_repo(existing=other)
    result = RecipeCsvImporter(repo).import_from_bytes(_make_csv(_row(id="5")), UID)
    assert result == ImportResult(created=1, updated=0)


def test_mixed_create_and_update() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _existing_recipe(id=1)
    repo.save.side_effect = lambda r: r
    result = RecipeCsvImporter(repo).import_from_bytes(
        _make_csv(_row(id="1"), _row(name="Суп")), UID
    )
    assert result == ImportResult(created=1, updated=1)


def test_missing_required_field_raises() -> None:
    row = _row()
    del row["name"]
    with pytest.raises(ImportValidationError, match="name"):
        RecipeCsvImporter(_mock_repo()).import_from_bytes(_make_csv(row), UID)


def test_invalid_ingredients_json_raises() -> None:
    with pytest.raises(ImportValidationError, match="ingredients_json"):
        RecipeCsvImporter(_mock_repo()).import_from_bytes(
            _make_csv(_row(ingredients_json="not_json")), UID
        )


def test_empty_bytes_returns_zero() -> None:
    result = RecipeCsvImporter(_mock_repo()).import_from_bytes(b"", UID)
    assert result == ImportResult(created=0, updated=0)


def test_supported_extensions() -> None:
    assert RecipeCsvImporter(_mock_repo()).supported_extensions() == ["csv"]
