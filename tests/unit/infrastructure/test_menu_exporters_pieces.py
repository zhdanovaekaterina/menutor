import json
from unittest.mock import MagicMock

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import MenuId, RecipeId, UserId
from backend.infrastructure.export.menu_json_exporter import MenuJsonExporter
from backend.infrastructure.import_.menu_json_importer import MenuJsonImporter

UID = UserId(1)


def _menu_with_pieces_override() -> WeeklyMenu:
    return WeeklyMenu(
        id=MenuId(1),
        name="Меню",
        slots=[
            MenuSlot(
                day=0,
                meal_type="обед",
                recipe_id=RecipeId(1),
                position=0,
                pieces_override=5,
            ),
        ],
        user_id=UID,
    )


def _menu_without_pieces_override() -> WeeklyMenu:
    return WeeklyMenu(
        id=MenuId(2),
        name="Меню обычное",
        slots=[
            MenuSlot(day=1, meal_type="завтрак", recipe_id=RecipeId(2), position=0),
        ],
        user_id=UID,
    )


def _mock_repo(existing: WeeklyMenu | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda m: m
    return repo


def _make_json(*rows: dict) -> bytes:
    return json.dumps(list(rows), ensure_ascii=False).encode("utf-8")


def _slot_row(pieces_override=None, **kwargs) -> dict:
    defaults = dict(
        day=0, meal_type="обед", recipe_id=1, product_id=None,
        quantity=None, unit=None, servings_override=None,
        pieces_override=pieces_override, position=0,
    )
    defaults.update(kwargs)
    return defaults


def _menu_row(slots=None, **kwargs) -> dict:
    defaults = dict(name="Меню", slots=slots or [_slot_row(pieces_override=5)])
    defaults.update(kwargs)
    return defaults


# --- Export tests ---

def test_export_slot_with_pieces_override_field_present_in_json() -> None:
    item = json.loads(MenuJsonExporter().export_bytes([_menu_with_pieces_override()]))[0]
    slot = item["slots"][0]
    assert "pieces_override" in slot
    assert slot["pieces_override"] == 5


def test_export_slot_without_pieces_override_field_is_null() -> None:
    item = json.loads(MenuJsonExporter().export_bytes([_menu_without_pieces_override()]))[0]
    slot = item["slots"][0]
    assert "pieces_override" in slot
    assert slot["pieces_override"] is None


# --- Import tests ---

def test_import_menu_with_pieces_override_slot_has_correct_value() -> None:
    repo = _mock_repo()
    result = MenuJsonImporter(repo).import_from_bytes(_make_json(_menu_row()), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: WeeklyMenu = repo.save.call_args[0][0]
    assert saved.slots[0].pieces_override == 5


def test_import_menu_with_null_pieces_override() -> None:
    repo = _mock_repo()
    row = _menu_row(slots=[_slot_row(pieces_override=None)])
    result = MenuJsonImporter(repo).import_from_bytes(_make_json(row), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: WeeklyMenu = repo.save.call_args[0][0]
    assert saved.slots[0].pieces_override is None


def test_import_menu_old_format_without_pieces_override_backward_compat() -> None:
    # Old format: slot dict has no pieces_override key at all
    old_slot = dict(
        day=0, meal_type="завтрак", recipe_id=1, product_id=None,
        quantity=None, unit=None, servings_override=None, position=0,
    )
    row = dict(name="Старое меню", slots=[old_slot])
    repo = _mock_repo()
    result = MenuJsonImporter(repo).import_from_bytes(_make_json(row), UID)
    assert result == ImportResult(created=1, updated=0)
    saved: WeeklyMenu = repo.save.call_args[0][0]
    assert saved.slots[0].pieces_override is None
