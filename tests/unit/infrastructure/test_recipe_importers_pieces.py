import csv
import io
import json
from unittest.mock import MagicMock

from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId, UserId
from backend.infrastructure.import_.recipe_csv_importer import RecipeCsvImporter
from backend.infrastructure.import_.recipe_json_importer import RecipeJsonImporter

UID = UserId(1)


def _mock_repo(existing: Recipe | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda r: r
    return repo


# --- JSON importer helpers ---

def _make_json(*rows: dict) -> bytes:
    return json.dumps(list(rows), ensure_ascii=False).encode("utf-8")


def _json_row(**kwargs) -> dict:
    defaults = dict(
        name="Котлеты", category_id=1, servings=5, weight=400,
        total_pieces=10, pieces_per_portion=2,
        ingredients=[{"product_id": 1, "quantity_amount": 500, "quantity_unit": "g", "order": 0}],
        steps=[{"order": 1, "description": "Лепить"}],
    )
    defaults.update(kwargs)
    return defaults


def _json_row_normal(**kwargs) -> dict:
    defaults = dict(
        name="Борщ", category_id=1, servings=4, weight=600,
        ingredients=[{"product_id": 2, "quantity_amount": 300, "quantity_unit": "g", "order": 0}],
        steps=[{"order": 1, "description": "Варить"}],
    )
    defaults.update(kwargs)
    return defaults


# --- JSON importer tests ---

def test_json_import_with_pieces_fields_creates_pieces_recipe() -> None:
    repo = _mock_repo()
    result = RecipeJsonImporter(repo).import_from_bytes(_make_json(_json_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.total_pieces == 10
    assert saved.pieces_per_portion == 2
    assert saved.is_pieces_mode is True


def test_json_import_without_pieces_fields_creates_normal_recipe() -> None:
    repo = _mock_repo()
    result = RecipeJsonImporter(repo).import_from_bytes(_make_json(_json_row_normal()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.total_pieces is None
    assert saved.pieces_per_portion is None
    assert saved.is_pieces_mode is False


def test_json_import_backward_compat_missing_pieces_keys() -> None:
    # Old format: no total_pieces/pieces_per_portion keys at all
    row = dict(
        name="Суп", category_id=1, servings=3, weight=0,
        ingredients=[],
        steps=[],
    )
    repo = _mock_repo()
    result = RecipeJsonImporter(repo).import_from_bytes(_make_json(row), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.total_pieces is None
    assert saved.pieces_per_portion is None


# --- CSV importer helpers ---

def _make_csv(*rows: dict) -> bytes:
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _csv_row(**kwargs) -> dict:
    defaults = dict(
        id="", name="Котлеты", category_id="1", servings="5", weight="400",
        total_pieces="10", pieces_per_portion="2",
        ingredients_json=json.dumps([
            {"product_id": 1, "quantity_amount": 500, "quantity_unit": "g", "order": 0}
        ]),
        steps_json=json.dumps([{"order": 1, "description": "Лепить"}]),
    )
    defaults.update(kwargs)
    return defaults


def _csv_row_old_format(**kwargs) -> dict:
    """Old CSV format without total_pieces and pieces_per_portion columns."""
    defaults = dict(
        id="", name="Блины", category_id="1", servings="4", weight="600",
        ingredients_json=json.dumps([
            {"product_id": 1, "quantity_amount": 200, "quantity_unit": "g", "order": 0}
        ]),
        steps_json=json.dumps([{"order": 1, "description": "Смешать"}]),
    )
    defaults.update(kwargs)
    return defaults


# --- CSV importer tests ---

def test_csv_import_with_pieces_fields() -> None:
    repo = _mock_repo()
    result = RecipeCsvImporter(repo).import_from_bytes(_make_csv(_csv_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.total_pieces == 10
    assert saved.pieces_per_portion == 2
    assert saved.is_pieces_mode is True


def test_csv_import_old_format_without_pieces_columns_does_not_crash() -> None:
    repo = _mock_repo()
    result = RecipeCsvImporter(repo).import_from_bytes(_make_csv(_csv_row_old_format()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.total_pieces is None
    assert saved.pieces_per_portion is None


def test_csv_import_empty_pieces_columns_creates_normal_recipe() -> None:
    repo = _mock_repo()
    row = _csv_row(total_pieces="", pieces_per_portion="")
    result = RecipeCsvImporter(repo).import_from_bytes(_make_csv(row), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: Recipe = repo.save.call_args[0][0]
    assert saved.total_pieces is None
    assert saved.pieces_per_portion is None
