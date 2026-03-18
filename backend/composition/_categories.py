"""Wire category use cases."""

from typing import Any

from backend.application.use_cases.manage_category import CategoryBundle
from backend.composition._infrastructure import _Infrastructure


def _wire_categories(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "product_categories": CategoryBundle(infra.product_category_repo),
        "recipe_categories": CategoryBundle(infra.recipe_category_repo),
    }
