import json
from unittest.mock import MagicMock

import pytest

from backend.domain.entities.menu import WeeklyMenu
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import MenuId, UserId
from backend.infrastructure.import_.menu_json_importer import MenuJsonImporter

UID = UserId(1)


def _make_json(*rows: dict) -> bytes:
    return json.dumps(list(rows), ensure_ascii=False).encode("utf-8")


def _row(**kwargs) -> dict:
    defaults = dict(
        name="Меню на неделю",
        slots=[
            {"day": 0, "meal_type": "завтрак", "recipe_id": 1, "product_id": None,
             "quantity": None, "unit": None, "servings_override": None, "position": 0},
        ],
    )
    defaults.update(kwargs)
    return defaults


def _mock_repo(existing: WeeklyMenu | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda m: m
    return repo


def _existing_menu(id: int = 1) -> WeeklyMenu:
    return WeeklyMenu(id=MenuId(id), name="Меню", user_id=UID)


def test_create_new_menu() -> None:
    repo = _mock_repo()
    result = MenuJsonImporter(repo).import_from_bytes(_make_json(_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: WeeklyMenu = repo.save.call_args[0][0]
    assert saved.id == MenuId(0)
    assert saved.name == "Меню на неделю"
    assert len(saved.slots) == 1


def test_update_existing_menu() -> None:
    repo = _mock_repo(existing=_existing_menu(id=4))
    result = MenuJsonImporter(repo).import_from_bytes(_make_json(_row(id=4)), UID)
    assert result == ImportResult(created=0, updated=1)
    saved: WeeklyMenu = repo.save.call_args[0][0]
    assert saved.id == MenuId(4)


def test_id_belonging_to_other_user_creates_new() -> None:
    other = WeeklyMenu(id=MenuId(4), name="Меню", user_id=UserId(99))
    repo = _mock_repo(existing=other)
    result = MenuJsonImporter(repo).import_from_bytes(_make_json(_row(id=4)), UID)
    assert result == ImportResult(created=1, updated=0)


def test_mixed_create_and_update() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _existing_menu(id=1)
    repo.save.side_effect = lambda m: m
    result = MenuJsonImporter(repo).import_from_bytes(
        _make_json(_row(id=1), _row(name="Второе меню", slots=[])), UID
    )
    assert result == ImportResult(created=1, updated=1)


def test_invalid_slot_both_ids_raises() -> None:
    row = _row(slots=[
        {"day": 0, "meal_type": "завтрак", "recipe_id": 1, "product_id": 2, "position": 0}
    ])
    with pytest.raises(ImportValidationError, match="слот"):
        MenuJsonImporter(_mock_repo()).import_from_bytes(_make_json(row), UID)


def test_invalid_slot_no_ids_raises() -> None:
    row = _row(slots=[
        {"day": 0, "meal_type": "завтрак", "recipe_id": None, "product_id": None, "position": 0}
    ])
    with pytest.raises(ImportValidationError, match="слот"):
        MenuJsonImporter(_mock_repo()).import_from_bytes(_make_json(row), UID)


def test_empty_name_raises() -> None:
    with pytest.raises(ImportValidationError, match="name"):
        MenuJsonImporter(_mock_repo()).import_from_bytes(_make_json(_row(name="")), UID)


def test_malformed_json_raises() -> None:
    with pytest.raises(ImportValidationError, match="JSON"):
        MenuJsonImporter(_mock_repo()).import_from_bytes(b"[oops", UID)


def test_json_not_array_raises() -> None:
    with pytest.raises(ImportValidationError, match="массивом"):
        MenuJsonImporter(_mock_repo()).import_from_bytes(b'{"name":"x"}', UID)


def test_empty_bytes_returns_zero() -> None:
    result = MenuJsonImporter(_mock_repo()).import_from_bytes(b"", UID)
    assert result == ImportResult(created=0, updated=0)


def test_menu_with_no_slots() -> None:
    result = MenuJsonImporter(_mock_repo()).import_from_bytes(_make_json(_row(slots=[])), UID)
    assert result == ImportResult(created=1, updated=0)


def test_supported_extensions() -> None:
    assert MenuJsonImporter(_mock_repo()).supported_extensions() == ["json"]
