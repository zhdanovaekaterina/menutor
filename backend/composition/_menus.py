"""Wire menu use cases."""

from typing import Any

from backend.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
    MoveSlotInMenu,
    RemoveItemFromSlot,
    SaveMenu,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_menus(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "create_menu": CreateMenu(infra.menu_repo),
        "save_menu": SaveMenu(infra.menu_repo),
        "load_menu": LoadMenu(infra.menu_repo),
        "delete_menu": DeleteMenu(infra.menu_repo),
        "list_menus": ListMenus(infra.menu_repo),
        "add_dish_to_slot": AddDishToSlot(infra.menu_repo),
        "move_slot_in_menu": MoveSlotInMenu(infra.menu_repo),
        "remove_item_from_slot": RemoveItemFromSlot(infra.menu_repo),
        "clear_menu": ClearMenu(infra.menu_repo),
    }
