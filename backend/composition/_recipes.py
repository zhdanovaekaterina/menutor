"""Wire recipe use cases."""

from typing import Any

from backend.application.use_cases.flatten_recipe_products import FlattenRecipeProducts
from backend.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipeWithDependents,
    EditRecipe,
    GetRecipe,
    ListRecipeCategories,
    ListRecipes,
)
from backend.application.use_cases.preview_flattened_products import (
    PreviewFlattenedProducts,
)
from backend.application.use_cases.validate_sub_recipe import ValidateSubRecipe
from backend.composition._infrastructure import _Infrastructure
from backend.domain.services.recipe_dependency_validator import (
    RecipeDependencyValidator,
)


def _wire_recipes(infra: _Infrastructure) -> dict[str, Any]:
    validator = RecipeDependencyValidator(infra.recipe_repo)
    return {
        "create_recipe": CreateRecipe(infra.recipe_repo, validator),
        "edit_recipe": EditRecipe(infra.recipe_repo, validator),
        "delete_recipe": DeleteRecipeWithDependents(infra.recipe_repo),
        "get_recipe": GetRecipe(infra.recipe_repo),
        "list_recipes": ListRecipes(infra.recipe_repo),
        "list_recipe_categories": ListRecipeCategories(infra.recipe_category_repo),
        "validate_sub_recipe": ValidateSubRecipe(infra.recipe_repo, validator),
        "flatten_recipe_products": FlattenRecipeProducts(
            infra.recipe_repo, infra.product_repo, infra.builder
        ),
        "preview_flattened_products": PreviewFlattenedProducts(
            infra.product_repo, infra.builder
        ),
    }
