from dataclasses import dataclass

from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId, RecipeId, UserId


@dataclass
class FlattenedProduct:
    product_id: ProductId
    product_name: str
    quantity: Quantity


class FlattenRecipeProducts:
    def __init__(
        self,
        recipe_repo: RecipeRepository,
        product_repo: ProductRepository,
        builder: ShoppingListBuilder,
    ) -> None:
        self._recipe_repo = recipe_repo
        self._product_repo = product_repo
        self._builder = builder

    def execute(
        self, recipe_id: RecipeId, user_id: UserId
    ) -> list[FlattenedProduct]:
        recipe = self._recipe_repo.get_by_id(recipe_id)
        if recipe is None or recipe.user_id != user_id:
            raise EntityNotFoundError(f"Рецепт {recipe_id} не найден")
        resolved = self._builder.flatten_recipe_products(recipe)
        result: list[FlattenedProduct] = []
        for pid, qty in resolved.items():
            product = self._product_repo.get_by_id(pid)
            if product is not None:
                result.append(FlattenedProduct(
                    product_id=pid,
                    product_name=product.name,
                    quantity=qty,
                ))
        return result
