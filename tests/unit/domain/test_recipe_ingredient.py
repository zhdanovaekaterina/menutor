import pytest
from dataclasses import FrozenInstanceError

from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeId


def test_product_ingredient_valid() -> None:
    ing = RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100, "g"))
    assert ing.product_id == ProductId(1)
    assert ing.sub_recipe_id is None


def test_sub_recipe_ingredient_valid() -> None:
    ing = RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1, "serv"))
    assert ing.sub_recipe_id == RecipeId(2)
    assert ing.product_id is None


def test_both_set_raises() -> None:
    with pytest.raises(InvalidEntityError):
        RecipeIngredient(product_id=ProductId(1), sub_recipe_id=RecipeId(2), quantity=Quantity(1, "g"))


def test_neither_set_raises() -> None:
    with pytest.raises(InvalidEntityError):
        RecipeIngredient(quantity=Quantity(1, "g"))


def test_is_sub_recipe_property() -> None:
    sub = RecipeIngredient(sub_recipe_id=RecipeId(3), quantity=Quantity(2, "serv"))
    prod = RecipeIngredient(product_id=ProductId(5), quantity=Quantity(100, "g"))
    assert sub.is_sub_recipe is True
    assert prod.is_sub_recipe is False


def test_is_product_property() -> None:
    sub = RecipeIngredient(sub_recipe_id=RecipeId(3), quantity=Quantity(2, "serv"))
    prod = RecipeIngredient(product_id=ProductId(5), quantity=Quantity(100, "g"))
    assert prod.is_product is True
    assert sub.is_product is False


def test_frozen() -> None:
    ing = RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100, "g"))
    with pytest.raises(FrozenInstanceError):
        ing.order = 99  # type: ignore[misc]
