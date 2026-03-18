import json
from unittest.mock import MagicMock

import pytest

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId, UserId
from backend.infrastructure.import_.recipe_json_importer import RecipeJsonImporter

UID = UserId(1)


def _make_json(*rows: dict) -> bytes:
    return json.dumps(list(rows), ensure_ascii=False).encode("utf-8")


def _row(**kwargs) -> dict:
    defaults = dict(
        name="Блины", category_id=1, servings=4, weight=600,
        ingredients=[{"product_id": 1, "quantity_amount": 200, "quantity_unit": "g", "order": 0}],
        steps=[{"order": 1, "description": "Смешать"}],
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
    repo = _mock_repo()
    result = RecipeJsonImporter(repo).import_from_bytes(_make_json(_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.id == RecipeId(0)
    assert len(saved.ingredients) == 1
    assert len(saved.steps) == 1


def test_update_existing_recipe() -> None:
    repo = _mock_repo(existing=_existing_recipe(id=7))
    result = RecipeJsonImporter(repo).import_from_bytes(_make_json(_row(id=7)), UID)
    assert result == ImportResult(created=0, updated=1)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.id == RecipeId(7)


def test_id_belonging_to_other_user_creates_new() -> None:
    other = Recipe(
        id=RecipeId(7), name="Блины", servings=4,
        category_id=RecipeCategoryId(1), user_id=UserId(99),
    )
    repo = _mock_repo(existing=other)
    result = RecipeJsonImporter(repo).import_from_bytes(_make_json(_row(id=7)), UID)
    assert result == ImportResult(created=1, updated=0)


def test_mixed_create_and_update() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _existing_recipe(id=1)
    repo.save.side_effect = lambda r: r
    result = RecipeJsonImporter(repo).import_from_bytes(
        _make_json(_row(id=1), _row(name="Суп")), UID
    )
    assert result == ImportResult(created=1, updated=1)


def test_missing_required_field_raises() -> None:
    row = _row()
    del row["name"]
    with pytest.raises(ImportValidationError, match="name"):
        RecipeJsonImporter(_mock_repo()).import_from_bytes(_make_json(row), UID)


def test_empty_name_raises() -> None:
    with pytest.raises(ImportValidationError, match="name"):
        RecipeJsonImporter(_mock_repo()).import_from_bytes(_make_json(_row(name="")), UID)


def test_malformed_json_raises() -> None:
    with pytest.raises(ImportValidationError, match="JSON"):
        RecipeJsonImporter(_mock_repo()).import_from_bytes(b"[broken", UID)


def test_json_not_array_raises() -> None:
    with pytest.raises(ImportValidationError, match="массивом"):
        RecipeJsonImporter(_mock_repo()).import_from_bytes('{"name":"Блины"}'.encode("utf-8"), UID)


def test_empty_bytes_returns_zero() -> None:
    result = RecipeJsonImporter(_mock_repo()).import_from_bytes(b"", UID)
    assert result == ImportResult(created=0, updated=0)


def test_supported_extensions() -> None:
    assert RecipeJsonImporter(_mock_repo()).supported_extensions() == ["json"]


def _sub_recipe(id: int = 10) -> Recipe:
    return Recipe(
        id=RecipeId(id), name="Тесто", servings=4,
        category_id=RecipeCategoryId(1), user_id=UID,
    )


def _row_with_sub_recipe(**kwargs) -> dict:
    defaults = dict(
        name="Блины с тестом", category_id=1, servings=4, weight=0,
        ingredients=[{"sub_recipe_id": 10, "quantity_amount": 1, "quantity_unit": "serv", "order": 0}],
        steps=[],
    )
    defaults.update(kwargs)
    return defaults


def test_import_recipe_with_sub_recipe_by_id() -> None:
    sub = _sub_recipe(id=10)
    repo = MagicMock()
    # First call: get_by_id for the recipe row (id=0 → skipped), subsequent for sub-recipe
    repo.get_by_id.return_value = sub
    repo.save.side_effect = lambda r: r
    result = RecipeJsonImporter(repo).import_from_bytes(
        _make_json(_row_with_sub_recipe()), UID
    )
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert len(saved.ingredients) == 1
    assert saved.ingredients[0].sub_recipe_id == RecipeId(10)
    assert saved.ingredients[0].is_sub_recipe


def test_import_recipe_sub_recipe_not_found_skipped() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None
    repo.save.side_effect = lambda r: r
    result = RecipeJsonImporter(repo).import_from_bytes(
        _make_json(_row_with_sub_recipe()), UID
    )
    # Recipe is still saved, but the sub-recipe ingredient is skipped
    assert result.created == 1
    assert len(result.errors) == 1
    saved: Recipe = repo.save.call_args[0][0]
    assert len(saved.ingredients) == 0


def test_import_product_only_recipe_unchanged() -> None:
    repo = _mock_repo()
    result = RecipeJsonImporter(repo).import_from_bytes(_make_json(_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert len(saved.ingredients) == 1
    assert saved.ingredients[0].is_product
    assert saved.ingredients[0].product_id is not None
