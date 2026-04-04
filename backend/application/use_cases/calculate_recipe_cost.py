from backend.domain.exceptions import SubRecipeWeightError
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.services.recipe_cost_calculator import (
    RecipeCostCalculator,
    RecipeCostResult,
)
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.value_objects.types import RecipeId, UserId


class CalculateRecipeCost:
    def __init__(
        self,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        builder: ShoppingListBuilder,
        calculator: RecipeCostCalculator,
    ) -> None:
        self._recipe_repo = recipe_repo
        self._product_repo = product_repo
        self._builder = builder
        self._calculator = calculator

    def execute(self, recipe_id: RecipeId, user_id: UserId) -> RecipeCostResult | None:
        """Calculate cost for a saved recipe. Returns None if recipe not found."""
        recipe = self._recipe_repo.get_by_id(recipe_id)
        if recipe is None or recipe.user_id != user_id:
            return None

        try:
            flat_products = self._builder.flatten_recipe_products(recipe)
        except SubRecipeWeightError:
            return RecipeCostResult(
                cost_per_portion=None,
                total_cost=None,
                currency=None,
                is_partial=True,
                computed_servings=recipe.computed_servings,
                ingredient_costs=[],
            )

        product_lookup = {}
        for pid in flat_products:
            product = self._product_repo.get_by_id(pid)
            if product is not None:
                product_lookup[pid] = product

        return self._calculator.calculate(recipe, flat_products, product_lookup)
