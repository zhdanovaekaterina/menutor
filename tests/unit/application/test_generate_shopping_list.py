import pytest
from unittest.mock import MagicMock

from src.domain.entities.menu import WeeklyMenu
from src.domain.entities.shopping_list import ShoppingList
from src.domain.value_objects.types import MenuId
from src.application.use_cases.generate_shopping_list import GenerateShoppingList


def _uc(menu_repo: MagicMock, builder: MagicMock) -> GenerateShoppingList:
    return GenerateShoppingList(menu_repo=menu_repo, builder=builder)


def test_generate_calls_builder_with_menu() -> None:
    menu = WeeklyMenu(MenuId(1), "Неделя", [])
    shopping_list = ShoppingList()

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build.return_value = shopping_list

    result = _uc(menu_repo, builder).execute(MenuId(1))

    builder.build.assert_called_once_with(menu)
    assert result is shopping_list


def test_generate_raises_when_menu_not_found() -> None:
    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = None
    builder = MagicMock()

    with pytest.raises(ValueError, match="не найдено"):
        _uc(menu_repo, builder).execute(MenuId(999))
