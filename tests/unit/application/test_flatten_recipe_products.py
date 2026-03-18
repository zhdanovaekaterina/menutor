from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.flatten_recipe_products import (
    FlattenRecipeProducts,
    FlattenedProduct,
)
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
    UserId,
)

UID = UserId(1)


def _product(id: int = 1, name: str = "Мука") -> Product:
    return Product(
        id=ProductId(id),
        name=name,
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(50, "RUB"),
        conversion_factor=1000.0,
        category_id=ProductCategoryId(1),
        user_id=UID,
    )


def _recipe_with_products() -> Recipe:
    return Recipe(
        id=RecipeId(1),
        name="Блины",
        servings=4,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g")),
            RecipeIngredient(product_id=ProductId(2), quantity=Quantity(100.0, "ml")),
        ],
        category_id=RecipeCategoryId(1),
        user_id=UID,
    )


def test_flatten_recipe_with_sub_recipes() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    builder = MagicMock()

    recipe = _recipe_with_products()
    recipe_repo.get_by_id.return_value = recipe

    # builder.flatten_recipe_products returns resolved leaf products
    pid1 = ProductId(1)
    pid2 = ProductId(2)
    builder.flatten_recipe_products.return_value = {
        pid1: Quantity(200.0, "g"),
        pid2: Quantity(100.0, "ml"),
    }

    product_repo.get_by_id.side_effect = lambda pid: (
        _product(id=int(pid), name="Мука" if pid == pid1 else "Молоко")
    )

    result = FlattenRecipeProducts(recipe_repo, product_repo, builder).execute(RecipeId(1), UID)

    builder.flatten_recipe_products.assert_called_once_with(recipe)
    assert len(result) == 2
    names = {fp.product_name for fp in result}
    assert "Мука" in names
    assert "Молоко" in names


def test_flatten_recipe_without_sub_recipes() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    builder = MagicMock()

    recipe = _recipe_with_products()
    recipe_repo.get_by_id.return_value = recipe

    pid1 = ProductId(1)
    builder.flatten_recipe_products.return_value = {pid1: Quantity(200.0, "g")}
    product_repo.get_by_id.return_value = _product(id=1)

    result = FlattenRecipeProducts(recipe_repo, product_repo, builder).execute(RecipeId(1), UID)

    assert len(result) == 1
    assert result[0].product_id == pid1
    assert result[0].product_name == "Мука"
    assert result[0].quantity == Quantity(200.0, "g")


def test_flatten_recipe_not_found_raises() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    builder = MagicMock()

    recipe_repo.get_by_id.return_value = None

    with pytest.raises(EntityNotFoundError, match="не найден"):
        FlattenRecipeProducts(recipe_repo, product_repo, builder).execute(RecipeId(999), UID)


def test_flatten_recipe_wrong_user_raises() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    builder = MagicMock()

    other_uid = UserId(99)
    recipe = Recipe(
        id=RecipeId(1),
        name="Блины",
        servings=4,
        ingredients=[],
        category_id=RecipeCategoryId(1),
        user_id=other_uid,
    )
    recipe_repo.get_by_id.return_value = recipe

    with pytest.raises(EntityNotFoundError, match="не найден"):
        FlattenRecipeProducts(recipe_repo, product_repo, builder).execute(RecipeId(1), UID)
