"""Unit tests for GenerateFilteredShoppingList use case."""

from unittest.mock import MagicMock, call

import pytest

from backend.application.use_cases.generate_filtered_shopping_list import (
    GenerateFilteredShoppingList,
)
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.saved_shopping_list import SavedShoppingList
from backend.domain.entities.shopping_list import ShoppingList
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import MealTypeId, MenuId, RecipeId, SavedShoppingListId, UserId

UID = UserId(1)
OTHER_UID = UserId(2)


def _uc(
    menu_repo: MagicMock,
    builder: MagicMock,
    saved_list_repo: MagicMock,
) -> GenerateFilteredShoppingList:
    return GenerateFilteredShoppingList(menu_repo, builder, saved_list_repo)


def _make_menu(name: str = "Неделя", user_id: UserId = UID) -> WeeklyMenu:
    slots = [
        MenuSlot(day=0, meal_type_id=MealTypeId(2), recipe_id=RecipeId(1)),
        MenuSlot(day=1, meal_type_id=MealTypeId(3), recipe_id=RecipeId(2)),
    ]
    return WeeklyMenu(MenuId(1), name, slots, user_id=user_id)


def test_execute_calls_build_filtered_with_indices() -> None:
    menu = _make_menu()
    indices = {0, 1}

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build_filtered.return_value = ShoppingList(items=[])
    saved_list_repo = MagicMock()
    saved_list_repo.save.return_value = MagicMock(spec=SavedShoppingList)

    _uc(menu_repo, builder, saved_list_repo).execute(MenuId(1), UID, indices)

    builder.build_filtered.assert_called_once_with(menu, indices, None)


def test_execute_raises_when_menu_not_found() -> None:
    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = None
    builder = MagicMock()
    saved_list_repo = MagicMock()

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        _uc(menu_repo, builder, saved_list_repo).execute(MenuId(999), UID, {0})


def test_execute_raises_when_wrong_user() -> None:
    menu = _make_menu(user_id=OTHER_UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    saved_list_repo = MagicMock()

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        _uc(menu_repo, builder, saved_list_repo).execute(MenuId(1), UID, {0})


def test_execute_saves_to_repo() -> None:
    menu = _make_menu()
    saved = MagicMock(spec=SavedShoppingList)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build_filtered.return_value = ShoppingList(items=[])
    saved_list_repo = MagicMock()
    saved_list_repo.save.return_value = saved

    result = _uc(menu_repo, builder, saved_list_repo).execute(MenuId(1), UID, {0})

    saved_list_repo.save.assert_called_once()
    assert result is saved


def test_execute_name_includes_menu_name() -> None:
    menu = _make_menu(name="Моё меню")

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build_filtered.return_value = ShoppingList(items=[])
    saved_list_repo = MagicMock()
    saved_list_repo.save.return_value = MagicMock(spec=SavedShoppingList)

    _uc(menu_repo, builder, saved_list_repo).execute(MenuId(1), UID, {0})

    saved_arg = saved_list_repo.save.call_args[0][0]
    assert "Моё меню" in saved_arg.name


def test_execute_passes_excluded_sub_recipe_ids_to_builder() -> None:
    menu = _make_menu()
    indices = {0, 1}
    excluded_ids = {5, 7}

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build_filtered.return_value = ShoppingList(items=[])
    saved_list_repo = MagicMock()
    saved_list_repo.save.return_value = MagicMock(spec=SavedShoppingList)

    _uc(menu_repo, builder, saved_list_repo).execute(MenuId(1), UID, indices, excluded_ids)

    call_args = builder.build_filtered.call_args
    assert call_args is not None
    # Third positional argument is excluded_sub_recipe_ids (as set[RecipeId])
    passed_exclusions = call_args[0][2]
    assert passed_exclusions == {RecipeId(5), RecipeId(7)}


def test_execute_defaults_to_no_exclusions_when_not_provided() -> None:
    menu = _make_menu()

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build_filtered.return_value = ShoppingList(items=[])
    saved_list_repo = MagicMock()
    saved_list_repo.save.return_value = MagicMock(spec=SavedShoppingList)

    _uc(menu_repo, builder, saved_list_repo).execute(MenuId(1), UID, {0})

    call_args = builder.build_filtered.call_args
    assert call_args is not None
    # Third positional argument should be None when no exclusions are provided
    passed_exclusions = call_args[0][2]
    assert passed_exclusions is None
