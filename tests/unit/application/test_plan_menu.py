from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
    RemoveDishFromSlot,
    RemoveItemFromSlot,
    SaveMenu,
)
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId


def _menu(id: int = 1, slots: list[MenuSlot] | None = None) -> WeeklyMenu:
    return WeeklyMenu(MenuId(id), "Неделя", slots or [])


def _slot(day: int = 0, meal: str = "обед", recipe_id: int = 1) -> MenuSlot:
    return MenuSlot(day=day, meal_type=meal, recipe_id=RecipeId(recipe_id))


def _product_slot(day: int = 0, meal: str = "обед", product_id: int = 1,
                  quantity: float = 100.0, unit: str = "g") -> MenuSlot:
    return MenuSlot(day=day, meal_type=meal, product_id=ProductId(product_id),
                    quantity=quantity, unit=unit)


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


def test_add_slot_appends_different_items_to_same_cell() -> None:
    """Different items with same (day, meal_type) should coexist."""
    existing = _slot(day=0, meal="обед", recipe_id=1)
    new_item = _slot(day=0, meal="обед", recipe_id=2)
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[existing])
    repo.save.side_effect = lambda m: m

    result = AddDishToSlot(repo).execute(MenuId(1), new_item)

    assert len(result.slots) == 2
    ids = {s.recipe_id for s in result.slots}
    assert ids == {RecipeId(1), RecipeId(2)}


def test_add_slot_replaces_duplicate_recipe_in_same_cell() -> None:
    """Adding same recipe to same (day, meal_type) replaces the existing one."""
    existing = MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1),
                        servings_override=1.0)
    updated = MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1),
                       servings_override=3.0)
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[existing])
    repo.save.side_effect = lambda m: m

    result = AddDishToSlot(repo).execute(MenuId(1), updated)

    assert len(result.slots) == 1
    assert result.slots[0].servings_override == 3.0


def test_add_slot_replaces_duplicate_product_in_same_cell() -> None:
    """Adding same product to same (day, meal_type) replaces the existing one."""
    existing = _product_slot(day=0, meal="обед", product_id=1, quantity=100.0, unit="g")
    updated = _product_slot(day=0, meal="обед", product_id=1, quantity=250.0, unit="g")
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[existing])
    repo.save.side_effect = lambda m: m

    result = AddDishToSlot(repo).execute(MenuId(1), updated)

    assert len(result.slots) == 1
    assert result.slots[0].quantity == 250.0


def test_add_slot_same_recipe_different_cell_no_conflict() -> None:
    """Same recipe in different (day, meal_type) should not conflict."""
    existing = _slot(day=0, meal="обед", recipe_id=1)
    new_item = _slot(day=1, meal="обед", recipe_id=1)
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[existing])
    repo.save.side_effect = lambda m: m

    result = AddDishToSlot(repo).execute(MenuId(1), new_item)

    assert len(result.slots) == 2


def test_add_product_slot() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu()
    repo.save.side_effect = lambda m: m

    result = AddDishToSlot(repo).execute(MenuId(1), _product_slot(day=0, meal="обед"))

    assert len(result.slots) == 1
    assert result.slots[0].product_id == ProductId(1)
    assert result.slots[0].recipe_id is None


def test_add_slot_raises_when_menu_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(EntityNotFoundError, match="не найдено"):
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

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        RemoveDishFromSlot(repo).execute(MenuId(999), 0, "обед")


# ---- RemoveItemFromSlot ----

def test_remove_item_removes_specific_recipe() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[
        _slot(0, "обед", recipe_id=1),
        _slot(0, "обед", recipe_id=2),
    ])
    repo.save.side_effect = lambda m: m

    result = RemoveItemFromSlot(repo).execute(
        MenuId(1), day=0, meal_type="обед", recipe_id=RecipeId(1)
    )

    assert len(result.slots) == 1
    assert result.slots[0].recipe_id == RecipeId(2)


def test_remove_item_removes_specific_product() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _menu(slots=[
        _slot(0, "обед", recipe_id=1),
        _product_slot(0, "обед", product_id=5),
    ])
    repo.save.side_effect = lambda m: m

    result = RemoveItemFromSlot(repo).execute(
        MenuId(1), day=0, meal_type="обед", product_id=ProductId(5)
    )

    assert len(result.slots) == 1
    assert result.slots[0].recipe_id == RecipeId(1)


def test_remove_item_raises_when_menu_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        RemoveItemFromSlot(repo).execute(MenuId(999), 0, "обед", recipe_id=RecipeId(1))


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

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        ClearMenu(repo).execute(MenuId(999))
