from dataclasses import dataclass

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import SubRecipeWeightError
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.services.recipe_cost_calculator import (
    RecipeCostCalculator,
    RecipeCostResult,
)
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    ProductId,
    RecipeCategoryId,
    RecipeId,
    UserId,
)


@dataclass
class CostPreviewIngredient:
    product_id: int | None
    sub_recipe_id: int | None
    quantity_amount: float
    quantity_unit: str


@dataclass
class CostPreviewRequest:
    ingredients: list[CostPreviewIngredient]
    servings: int
    total_pieces: int | None = None
    pieces_per_portion: int | None = None


class PreviewRecipeCost:
    def __init__(
        self,
        product_repo: ProductRepository,
        builder: ShoppingListBuilder,
        calculator: RecipeCostCalculator,
    ) -> None:
        self._product_repo = product_repo
        self._builder = builder
        self._calculator = calculator

    def execute(
        self,
        recipe_id: RecipeId,
        user_id: UserId,
        request: CostPreviewRequest,
    ) -> RecipeCostResult:
        """Calculate cost from unsaved ingredient data."""
        ingredients: list[RecipeIngredient] = []
        for ing in request.ingredients:
            if ing.product_id is not None and ing.sub_recipe_id is None:
                ingredients.append(
                    RecipeIngredient(
                        product_id=ProductId(ing.product_id),
                        quantity=Quantity(ing.quantity_amount, ing.quantity_unit),
                    )
                )
            elif ing.sub_recipe_id is not None and ing.product_id is None:
                ingredients.append(
                    RecipeIngredient(
                        sub_recipe_id=RecipeId(ing.sub_recipe_id),
                        quantity=Quantity(ing.quantity_amount, ing.quantity_unit),
                    )
                )

        temp_recipe = Recipe(
            id=recipe_id,
            name="",
            servings=request.servings,
            ingredients=ingredients,
            user_id=user_id,
            category_id=RecipeCategoryId(0),
            total_pieces=request.total_pieces,
            pieces_per_portion=request.pieces_per_portion,
        )

        try:
            flat_products = self._builder.flatten_recipe_products(temp_recipe)
        except SubRecipeWeightError:
            return RecipeCostResult(
                cost_per_portion=None,
                total_cost=None,
                currency=None,
                is_partial=True,
                computed_servings=temp_recipe.computed_servings,
                ingredient_costs=[],
            )

        product_lookup = {}
        for pid in flat_products:
            product = self._product_repo.get_by_id(pid)
            if product is not None:
                product_lookup[pid] = product

        return self._calculator.calculate(temp_recipe, flat_products, product_lookup)
