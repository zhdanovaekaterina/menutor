"""Unit tests for saved shopping list use cases."""

import re
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from backend.application.use_cases.generate_and_save_shopping_list import (
    GenerateAndSaveShoppingList,
)
from backend.application.use_cases.manage_saved_shopping_list import (
    CopySavedShoppingList,
    CreateSavedShoppingList,
    DeleteSavedShoppingList,
    GetSavedShoppingList,
    ListSavedShoppingLists,
    RenameSavedShoppingList,
    SavedShoppingListItemData,
    ToggleItemPurchased,
    UpdateSavedShoppingList,
)
from backend.domain.entities.menu import WeeklyMenu
from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import (
    MenuId,
    ProductId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)

UID = UserId(1)
OTHER_UID = UserId(2)
LIST_ID = SavedShoppingListId(10)
ITEM_ID = SavedShoppingListItemId(5)

_CREATED_AT = datetime(2026, 3, 21, 12, 0, 0, tzinfo=UTC)


def _make_item(
    id: int = 5,
    purchased: bool = False,
) -> SavedShoppingListItem:
    return SavedShoppingListItem(
        id=SavedShoppingListItemId(id),
        product_id=ProductId(1),
        product_name="Мука",
        category="Бакалея",
        quantity=Quantity(amount=500.0, unit="g"),
        buy_quantity=Quantity(amount=1.0, unit="kg"),
        buy_quantity_overridden=False,
        cost=Money(Decimal("80")),
        purchased=purchased,
        recipe_quantity=None,
        item_order=0,
    )


def _make_list(
    id: int = 10,
    user_id: UserId = UID,
    name: str = "Список 12:00 21.03.2026",
    items: list[SavedShoppingListItem] | None = None,
) -> SavedShoppingList:
    return SavedShoppingList(
        id=SavedShoppingListId(id),
        user_id=user_id,
        name=name,
        items=items if items is not None else [],
        source_menu_id=None,
        created_at=_CREATED_AT,
        updated_at=_CREATED_AT,
    )


def _make_item_data() -> SavedShoppingListItemData:
    return SavedShoppingListItemData(
        product_id=1,
        product_name="Мука",
        category="Бакалея",
        quantity_amount=500.0,
        quantity_unit="g",
        buy_quantity_amount=1.0,
        buy_quantity_unit="kg",
        buy_quantity_overridden=False,
        cost_amount=80.0,
        cost_currency="RUB",
        purchased=False,
        recipe_quantity_amount=None,
        recipe_quantity_unit=None,
        item_order=0,
    )


# --------------------------------------------------------------------------- #
# CreateSavedShoppingList
# --------------------------------------------------------------------------- #

def test_create_saved_shopping_list_saves_and_returns() -> None:
    repo = MagicMock()
    saved = _make_list()
    repo.save.return_value = saved

    result = CreateSavedShoppingList(repo).execute(UID)

    repo.save.assert_called_once()
    assert result is saved


def test_create_saved_shopping_list_default_name_format() -> None:
    repo = MagicMock()
    repo.save.side_effect = lambda x: x

    fixed_now = datetime(2026, 3, 21, 9, 5, 0, tzinfo=UTC)
    with patch(
        "backend.application.use_cases.manage_saved_shopping_list._now",
        return_value=fixed_now,
    ):
        result = CreateSavedShoppingList(repo).execute(UID)

    assert result.name == "Список 09:05 21.03.2026"


def test_create_saved_shopping_list_starts_empty() -> None:
    repo = MagicMock()
    repo.save.side_effect = lambda x: x

    result = CreateSavedShoppingList(repo).execute(UID)

    assert result.items == []
    assert result.user_id == UID
    assert result.id == SavedShoppingListId(0)


# --------------------------------------------------------------------------- #
# GetSavedShoppingList
# --------------------------------------------------------------------------- #

def test_get_saved_shopping_list_returns_list() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list()

    result = GetSavedShoppingList(repo).execute(LIST_ID, UID)

    assert result.id == LIST_ID


def test_get_saved_shopping_list_raises_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(EntityNotFoundError, match="не найден"):
        GetSavedShoppingList(repo).execute(LIST_ID, UID)


def test_get_saved_shopping_list_raises_for_wrong_user() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list(user_id=OTHER_UID)

    with pytest.raises(EntityNotFoundError):
        GetSavedShoppingList(repo).execute(LIST_ID, UID)


# --------------------------------------------------------------------------- #
# ListSavedShoppingLists
# --------------------------------------------------------------------------- #

def test_list_saved_shopping_lists_returns_all() -> None:
    repo = MagicMock()
    lists = [_make_list(id=1), _make_list(id=2)]
    repo.find_all.return_value = lists

    result = ListSavedShoppingLists(repo).execute(UID)

    repo.find_all.assert_called_once_with(UID)
    assert result == lists


def test_list_saved_shopping_lists_returns_empty_when_none() -> None:
    repo = MagicMock()
    repo.find_all.return_value = []

    result = ListSavedShoppingLists(repo).execute(UID)

    assert result == []


# --------------------------------------------------------------------------- #
# UpdateSavedShoppingList
# --------------------------------------------------------------------------- #

def test_update_saved_shopping_list_updates_name_and_items() -> None:
    repo = MagicMock()
    existing = _make_list()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda x: x

    result = UpdateSavedShoppingList(repo).execute(
        id=LIST_ID,
        name="Новое название",
        items=[_make_item_data()],
        user_id=UID,
    )

    assert result.name == "Новое название"
    assert len(result.items) == 1
    assert result.items[0].product_name == "Мука"
    repo.save.assert_called_once()


def test_update_saved_shopping_list_updates_updated_at() -> None:
    repo = MagicMock()
    existing = _make_list()
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda x: x

    before = datetime.now(UTC)
    result = UpdateSavedShoppingList(repo).execute(
        id=LIST_ID,
        name="X",
        items=[],
        user_id=UID,
    )

    assert result.updated_at >= before


def test_update_saved_shopping_list_raises_for_wrong_user() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list(user_id=OTHER_UID)

    with pytest.raises(EntityNotFoundError):
        UpdateSavedShoppingList(repo).execute(
            id=LIST_ID,
            name="X",
            items=[],
            user_id=UID,
        )


# --------------------------------------------------------------------------- #
# RenameSavedShoppingList
# --------------------------------------------------------------------------- #

def test_rename_saved_shopping_list_updates_only_name() -> None:
    repo = MagicMock()
    existing = _make_list(items=[_make_item()])
    repo.get_by_id.return_value = existing
    repo.save.side_effect = lambda x: x

    result = RenameSavedShoppingList(repo).execute(
        id=LIST_ID,
        name="Переименованный список",
        user_id=UID,
    )

    assert result.name == "Переименованный список"
    assert len(result.items) == 1


def test_rename_saved_shopping_list_raises_for_wrong_user() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list(user_id=OTHER_UID)

    with pytest.raises(EntityNotFoundError):
        RenameSavedShoppingList(repo).execute(
            id=LIST_ID,
            name="X",
            user_id=UID,
        )


# --------------------------------------------------------------------------- #
# DeleteSavedShoppingList
# --------------------------------------------------------------------------- #

def test_delete_saved_shopping_list_deletes_own() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list()

    DeleteSavedShoppingList(repo).execute(LIST_ID, UID)

    repo.delete.assert_called_once_with([LIST_ID])


def test_delete_saved_shopping_list_noop_for_wrong_user() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list(user_id=OTHER_UID)

    DeleteSavedShoppingList(repo).execute(LIST_ID, UID)

    repo.delete.assert_not_called()


def test_delete_saved_shopping_list_noop_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    DeleteSavedShoppingList(repo).execute(LIST_ID, UID)

    repo.delete.assert_not_called()


# --------------------------------------------------------------------------- #
# CopySavedShoppingList
# --------------------------------------------------------------------------- #

def test_copy_saved_shopping_list_name_has_suffix() -> None:
    repo = MagicMock()
    source = _make_list(name="Список покупок")
    repo.get_by_id.return_value = source
    repo.save.side_effect = lambda x: x

    result = CopySavedShoppingList(repo).execute(LIST_ID, UID)

    assert result.name == "Список покупок (копия)"


def test_copy_saved_shopping_list_has_zero_id() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list()
    repo.save.side_effect = lambda x: x

    result = CopySavedShoppingList(repo).execute(LIST_ID, UID)

    assert result.id == SavedShoppingListId(0)


def test_copy_saved_shopping_list_copies_items_with_zero_ids() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list(items=[_make_item(id=5)])
    repo.save.side_effect = lambda x: x

    result = CopySavedShoppingList(repo).execute(LIST_ID, UID)

    assert len(result.items) == 1
    assert result.items[0].id == SavedShoppingListItemId(0)


def test_copy_saved_shopping_list_raises_for_wrong_user() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list(user_id=OTHER_UID)

    with pytest.raises(EntityNotFoundError):
        CopySavedShoppingList(repo).execute(LIST_ID, UID)


# --------------------------------------------------------------------------- #
# ToggleItemPurchased
# --------------------------------------------------------------------------- #

def test_toggle_item_purchased_false_to_true() -> None:
    item = _make_item(id=5, purchased=False)
    shopping_list = _make_list(items=[item])
    repo = MagicMock()
    repo.get_by_id.return_value = shopping_list
    repo.save.side_effect = lambda x: x

    result = ToggleItemPurchased(repo).execute(LIST_ID, ITEM_ID, UID)

    assert result.items[0].purchased is True
    repo.save.assert_called_once()


def test_toggle_item_purchased_true_to_false() -> None:
    item = _make_item(id=5, purchased=True)
    shopping_list = _make_list(items=[item])
    repo = MagicMock()
    repo.get_by_id.return_value = shopping_list
    repo.save.side_effect = lambda x: x

    result = ToggleItemPurchased(repo).execute(LIST_ID, ITEM_ID, UID)

    assert result.items[0].purchased is False


def test_toggle_item_purchased_raises_when_item_not_found() -> None:
    shopping_list = _make_list(items=[_make_item(id=99)])
    repo = MagicMock()
    repo.get_by_id.return_value = shopping_list

    with pytest.raises(EntityNotFoundError):
        ToggleItemPurchased(repo).execute(LIST_ID, SavedShoppingListItemId(5), UID)


def test_toggle_item_purchased_raises_for_wrong_user() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _make_list(user_id=OTHER_UID)

    with pytest.raises(EntityNotFoundError):
        ToggleItemPurchased(repo).execute(LIST_ID, ITEM_ID, UID)


# --------------------------------------------------------------------------- #
# GenerateAndSaveShoppingList
# --------------------------------------------------------------------------- #

def _make_shopping_list_item() -> ShoppingListItem:
    return ShoppingListItem(
        product_id=ProductId(1),
        product_name="Мука",
        category="Бакалея",
        quantity=Quantity(amount=500.0, unit="g"),
        cost=Money(Decimal("80")),
        purchased=False,
        recipe_quantity=None,
    )


def test_generate_and_save_shopping_list_saves_and_returns() -> None:
    menu = WeeklyMenu(MenuId(7), "Неделя 1", [], user_id=UID)
    shopping_list = ShoppingList(items=[_make_shopping_list_item()])

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build.return_value = shopping_list
    saved_list_repo = MagicMock()
    saved = _make_list()
    saved_list_repo.save.return_value = saved

    result = GenerateAndSaveShoppingList(menu_repo, builder, saved_list_repo).execute(
        MenuId(7), UID
    )

    saved_list_repo.save.assert_called_once()
    assert result is saved


def test_generate_and_save_name_format() -> None:
    menu = WeeklyMenu(MenuId(7), "Июньское меню", [], user_id=UID)
    shopping_list = ShoppingList(items=[])

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build.return_value = shopping_list
    saved_list_repo = MagicMock()
    saved_list_repo.save.side_effect = lambda x: x

    fixed_now = datetime(2026, 6, 5, 14, 30, 0, tzinfo=UTC)
    with patch(
        "backend.application.use_cases.generate_and_save_shopping_list.datetime",
    ) as mock_dt:
        mock_dt.now.return_value = fixed_now

        result = GenerateAndSaveShoppingList(menu_repo, builder, saved_list_repo).execute(
            MenuId(7), UID
        )

    assert result.name == 'Создано из меню «Июньское меню» 14:30 05.06.2026'


def test_generate_and_save_source_menu_id_set() -> None:
    menu = WeeklyMenu(MenuId(7), "Меню", [], user_id=UID)
    shopping_list = ShoppingList(items=[])

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build.return_value = shopping_list
    saved_list_repo = MagicMock()
    saved_list_repo.save.side_effect = lambda x: x

    result = GenerateAndSaveShoppingList(menu_repo, builder, saved_list_repo).execute(
        MenuId(7), UID
    )

    assert result.source_menu_id == MenuId(7)


def test_generate_and_save_items_converted_correctly() -> None:
    menu = WeeklyMenu(MenuId(7), "Меню", [], user_id=UID)
    shopping_item = _make_shopping_list_item()
    shopping_list = ShoppingList(items=[shopping_item])

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    builder = MagicMock()
    builder.build.return_value = shopping_list
    saved_list_repo = MagicMock()
    saved_list_repo.save.side_effect = lambda x: x

    result = GenerateAndSaveShoppingList(menu_repo, builder, saved_list_repo).execute(
        MenuId(7), UID
    )

    assert len(result.items) == 1
    saved_item = result.items[0]
    assert saved_item.product_name == "Мука"
    assert saved_item.buy_quantity_overridden is False
    assert saved_item.purchased is False
    assert saved_item.item_order == 0
    assert saved_item.id == SavedShoppingListItemId(0)


def test_generate_and_save_raises_when_menu_not_found() -> None:
    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = None
    builder = MagicMock()
    saved_list_repo = MagicMock()

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        GenerateAndSaveShoppingList(menu_repo, builder, saved_list_repo).execute(
            MenuId(999), UID
        )
