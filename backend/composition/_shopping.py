"""Wire shopping list use cases."""

from typing import Any

from backend.application.use_cases.generate_and_save_shopping_list import (
    GenerateAndSaveShoppingList,
)
from backend.application.use_cases.generate_filtered_shopping_list import (
    GenerateFilteredShoppingList,
)
from backend.application.use_cases.generate_meal_summary import GenerateMealSummary
from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.application.use_cases.manage_saved_shopping_list import (
    CopySavedShoppingList,
    CreateSavedShoppingList,
    DeleteSavedShoppingList,
    GetSavedShoppingList,
    ListSavedShoppingLists,
    RenameSavedShoppingList,
    ToggleItemPurchased,
    UpdateSavedShoppingList,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_shopping(infra: _Infrastructure) -> dict[str, Any]:
    saved_repo = infra.saved_shopping_list_repo
    return {
        "generate_shopping_list": GenerateShoppingList(
            menu_repo=infra.menu_repo,
            builder=infra.builder,
        ),
        "generate_and_save_shopping_list": GenerateAndSaveShoppingList(
            menu_repo=infra.menu_repo,
            builder=infra.builder,
            saved_list_repo=saved_repo,
        ),
        "generate_meal_summary": GenerateMealSummary(
            menu_repo=infra.menu_repo,
            recipe_repo=infra.recipe_repo,
            product_repo=infra.product_repo,
            builder=infra.builder,
        ),
        "generate_filtered_shopping_list": GenerateFilteredShoppingList(
            menu_repo=infra.menu_repo,
            builder=infra.builder,
            saved_list_repo=saved_repo,
        ),
        "create_saved_shopping_list": CreateSavedShoppingList(saved_repo),
        "get_saved_shopping_list": GetSavedShoppingList(saved_repo),
        "list_saved_shopping_lists": ListSavedShoppingLists(saved_repo),
        "update_saved_shopping_list": UpdateSavedShoppingList(saved_repo),
        "rename_saved_shopping_list": RenameSavedShoppingList(saved_repo),
        "delete_saved_shopping_list": DeleteSavedShoppingList(saved_repo),
        "copy_saved_shopping_list": CopySavedShoppingList(saved_repo),
        "toggle_item_purchased": ToggleItemPurchased(saved_repo),
    }
