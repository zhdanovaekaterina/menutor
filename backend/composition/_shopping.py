"""Wire shopping list use cases."""

from typing import Any

from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.composition._infrastructure import _Infrastructure


def _wire_shopping(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "generate_shopping_list": GenerateShoppingList(
            menu_repo=infra.menu_repo,
            builder=infra.builder,
        ),
    }
