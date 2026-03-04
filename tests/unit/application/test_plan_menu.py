import pytest
from unittest.mock import MagicMock

from src.domain.entities.menu import MenuSlot, WeeklyMenu
from src.domain.value_objects.types import MenuId, RecipeId
from src.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
    RemoveDishFromSlot,
    SaveMenu,
)


def _menu(id: int = 1, slots: list[MenuSlot] | None = None) -> WeeklyMenu:
    return WeeklyMenu(MenuId(id), "Неделя", slots or [])


def _slot(day: int = 0, meal: str = "обед") -> MenuSlot:
    return MenuSlot(day=day, meal_type=meal, recipe_id=RecipeId(1))


# ---- CreateMenu ----

def test_create_menu_saves_empty_menu() -> None:
    repo = MagicMock()
    repo.save.side_effect = lambda m: m

    result = CreateMenu(repo).execute("Моё меню")

    repo.save.assert_called_once()
    assert result.name == "Моё меню"
    assert result.slots == []


# ---- SaveMenu ----

def test_save_menu_delegates_to_repo() -> None:
    repo = MagicMock()
    menu = _menu()
    repo.save.return_value = menu

    result = SaveMenu(repo).execute(menu)

    repo.save.assert_called_once_with(menu)
    assert result == menu


# ---- LoadMenu ----

def test_load_menu_returns_menu() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu()

    result = LoadMenu(repo).execute(MenuId(1))

    assert result is not None
    assert result.id == MenuId(1)


def test_load_menu_returns_none_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    assert LoadMenu(repo).execute(MenuId(999)) is None


# ---- DeleteMenu ----

def test_delete_menu_calls_repo_delete() -> None:
    repo = MagicMock()

    DeleteMenu(repo).execute(MenuId(1))

    repo.delete.assert_called_once_with(MenuId(1))


# ---- ListMenus ----

def test_list_menus_returns_all() -> None:
    repo = MagicMock()
    repo.find_all.return_value = [_menu(1), _menu(2)]

    assert len(ListMenus(repo).execute()) == 2


# ---- AddDishToSlot ----

def test_add_slot_appends_new_slot() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu()
    repo.save.side_effect = lambda m: m

    result = AddDishToSlot(repo).execute(MenuId(1), _slot(day=0, meal="обед"))

    assert len(result.slots) == 1
    assert result.slots[0].day == 0


def test_add_slot_replaces_existing_same_day_and_meal() -> None:
    existing = _slot(day=0, meal="обед")
    replacement = MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(2))
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[existing])
    repo.save.side_effect = lambda m: m

    result = AddDishToSlot(repo).execute(MenuId(1), replacement)

    assert len(result.slots) == 1
    assert result.slots[0].recipe_id == RecipeId(2)


def test_add_slot_raises_when_menu_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="не найдено"):
        AddDishToSlot(repo).execute(MenuId(999), _slot())


# ---- RemoveDishFromSlot ----

def test_remove_slot_removes_matching_day_and_meal() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[_slot(0, "обед"), _slot(1, "ужин")])
    repo.save.side_effect = lambda m: m

    result = RemoveDishFromSlot(repo).execute(MenuId(1), day=0, meal_type="обед")

    assert len(result.slots) == 1
    assert result.slots[0].day == 1


def test_remove_slot_no_op_when_slot_absent() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[_slot(1, "ужин")])
    repo.save.side_effect = lambda m: m

    result = RemoveDishFromSlot(repo).execute(MenuId(1), day=0, meal_type="обед")

    assert len(result.slots) == 1


def test_remove_slot_raises_when_menu_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="не найдено"):
        RemoveDishFromSlot(repo).execute(MenuId(999), 0, "обед")


# ---- ClearMenu ----

def test_clear_menu_removes_all_slots() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[_slot(0), _slot(1), _slot(2)])
    repo.save.side_effect = lambda m: m

    result = ClearMenu(repo).execute(MenuId(1))

    assert result.slots == []
    repo.save.assert_called_once()


def test_clear_menu_raises_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="не найдено"):
        ClearMenu(repo).execute(MenuId(999))
