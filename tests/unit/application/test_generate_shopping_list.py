import pytest
from unittest.mock import MagicMock

from src.domain.entities.family_member import FamilyMember
from src.domain.entities.menu import WeeklyMenu
from src.domain.entities.shopping_list import ShoppingList
from src.domain.value_objects.types import FamilyMemberId, MenuId
from src.application.use_cases.generate_shopping_list import GenerateShoppingList


def _uc(menu_repo: MagicMock, family_repo: MagicMock,
        builder: MagicMock) -> GenerateShoppingList:
    return GenerateShoppingList(
        menu_repo=menu_repo,
        family_repo=family_repo,
        builder=builder,
    )


def test_generate_calls_builder_with_menu_and_members() -> None:
    menu = WeeklyMenu(MenuId(1), "Неделя", [])
    members = [FamilyMember(FamilyMemberId(1), "Алиса")]
    shopping_list = ShoppingList()

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    family_repo = MagicMock()
    family_repo.find_all.return_value = members
    builder = MagicMock()
    builder.build.return_value = shopping_list

    result = _uc(menu_repo, family_repo, builder).execute(MenuId(1))

    builder.build.assert_called_once_with(menu, members)
    assert result is shopping_list


def test_generate_raises_when_menu_not_found() -> None:
    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = None
    family_repo = MagicMock()
    builder = MagicMock()

    with pytest.raises(ValueError, match="не найдено"):
        _uc(menu_repo, family_repo, builder).execute(MenuId(999))


def test_generate_passes_empty_members_when_no_family() -> None:
    menu = WeeklyMenu(MenuId(1), "Неделя", [])
    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    family_repo = MagicMock()
    family_repo.find_all.return_value = []
    builder = MagicMock()
    builder.build.return_value = ShoppingList()

    _uc(menu_repo, family_repo, builder).execute(MenuId(1))

    builder.build.assert_called_once_with(menu, [])
