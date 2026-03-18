from dataclasses import dataclass

from backend.application.use_cases.flatten_recipe_products import FlattenedProduct
from backend.domain.entities.recipe import Recipe
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
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
class IngredientData:
    product_id: int | None
    sub_recipe_id: int | None
    quantity_amount: float
    quantity_unit: str


class PreviewFlattenedProducts:
    """Compute flattened products for unsaved ingredient data without touching the DB."""

    def __init__(
        self,
        product_repo: ProductRepository,
        builder: ShoppingListBuilder,
    ) -> None:
        self._product_repo = product_repo
        self._builder = builder

    def execute(
        self,
        recipe_id: RecipeId,
        user_id: UserId,
        ingredients_data: list[IngredientData],
    ) -> list[FlattenedProduct]:
        ingredients: list[RecipeIngredient] = []
        for ing in ingredients_data:
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
            # skip rows where both or neither are set (invalid — mirrors schema validator)

        temp_recipe = Recipe(
            id=recipe_id,
            name="",
            servings=1,
            ingredients=ingredients,
            user_id=user_id,
            category_id=RecipeCategoryId(0),
        )

        resolved = self._builder.flatten_recipe_products(temp_recipe)
        result: list[FlattenedProduct] = []
        for pid, qty in resolved.items():
            product = self._product_repo.get_by_id(pid)
            if product is not None:
                result.append(
                    FlattenedProduct(
                        product_id=pid,
                        product_name=product.name,
                        quantity=qty,
                    )
                )
        return result
