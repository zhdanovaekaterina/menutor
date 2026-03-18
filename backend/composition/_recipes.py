"""Wire recipe use cases."""

from typing import Any

from backend.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    EditRecipe,
    GetRecipe,
    ListRecipeCategories,
    ListRecipes,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_recipes(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "create_recipe": CreateRecipe(infra.recipe_repo),
        "edit_recipe": EditRecipe(infra.recipe_repo),
        "delete_recipe": DeleteRecipe(infra.recipe_repo),
        "get_recipe": GetRecipe(infra.recipe_repo),
        "list_recipes": ListRecipes(infra.recipe_repo),
        "list_recipe_categories": ListRecipeCategories(infra.recipe_category_repo),
    }
