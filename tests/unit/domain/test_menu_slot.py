import pytest

from src.domain.entities.menu import MenuSlot
from src.domain.exceptions import InvalidEntityError
from src.domain.value_objects.types import ProductId, RecipeId


def test_recipe_slot_valid() -> None:
    slot = MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1))
    assert slot.recipe_id == RecipeId(1)
    assert slot.product_id is None


def test_product_slot_valid() -> None:
    slot = MenuSlot(day=0, meal_type="обед", product_id=ProductId(1),
                    quantity=200.0, unit="g")
    assert slot.product_id == ProductId(1)
    assert slot.recipe_id is None


def test_neither_recipe_nor_product_raises() -> None:
    with pytest.raises(InvalidEntityError, match="ровно одно"):
        MenuSlot(day=0, meal_type="обед")


def test_both_recipe_and_product_raises() -> None:
    with pytest.raises(InvalidEntityError, match="ровно одно"):
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1),
                 product_id=ProductId(2))
