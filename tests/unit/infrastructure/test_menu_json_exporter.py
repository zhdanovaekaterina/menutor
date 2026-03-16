import json

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.value_objects.types import MenuId, RecipeId, UserId
from backend.infrastructure.export.menu_json_exporter import MenuJsonExporter


def _menu() -> WeeklyMenu:
    return WeeklyMenu(
        id=MenuId(1),
        name="Меню на неделю",
        slots=[
            MenuSlot(day=0, meal_type="завтрак", recipe_id=RecipeId(1), position=0),
        ],
        user_id=UserId(1),
    )


def test_export_bytes_returns_list() -> None:
    data = json.loads(MenuJsonExporter().export_bytes([_menu()]))
    assert isinstance(data, list)
    assert len(data) == 1


def test_export_bytes_fields() -> None:
    item = json.loads(MenuJsonExporter().export_bytes([_menu()]))[0]
    assert item["id"] == 1
    assert item["name"] == "Меню на неделю"
    assert len(item["slots"]) == 1


def test_export_bytes_slot_fields() -> None:
    slot = json.loads(MenuJsonExporter().export_bytes([_menu()]))[0]["slots"][0]
    assert slot["day"] == 0
    assert slot["meal_type"] == "завтрак"
    assert slot["recipe_id"] == 1
    assert slot["product_id"] is None
    assert slot["position"] == 0


def test_export_bytes_empty() -> None:
    data = json.loads(MenuJsonExporter().export_bytes([]))
    assert data == []


def test_example_bytes_is_parseable() -> None:
    data = json.loads(MenuJsonExporter().example_bytes())
    assert len(data) == 1
    assert len(data[0]["slots"]) == 2


def test_content_type() -> None:
    assert MenuJsonExporter().content_type() == "application/json"


def test_file_extension() -> None:
    assert MenuJsonExporter().file_extension() == "json"
