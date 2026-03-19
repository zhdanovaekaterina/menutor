import pytest

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId, UserId


def _pieces_recipe(
    total_pieces: int = 10,
    pieces_per_portion: int = 2,
    servings: int = 4,
    amount: float = 500.0,
    unit: str = "g",
) -> Recipe:
    return Recipe(
        id=RecipeId(1),
        name="Pieces Recipe",
        servings=servings,
        total_pieces=total_pieces,
        pieces_per_portion=pieces_per_portion,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(amount, unit))
        ],
    )


def _normal_recipe(servings: int = 4, amount: float = 500.0) -> Recipe:
    return Recipe(
        id=RecipeId(2),
        name="Normal Recipe",
        servings=servings,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(amount, "g"))
        ],
    )


# 1. Recipe with total_pieces=10, pieces_per_portion=2 → is_pieces_mode == True
def test_is_pieces_mode_true_when_both_set() -> None:
    recipe = _pieces_recipe(total_pieces=10, pieces_per_portion=2)
    assert recipe.is_pieces_mode is True


# 2. Recipe without pieces fields → is_pieces_mode == False
def test_is_pieces_mode_false_when_fields_absent() -> None:
    recipe = _normal_recipe()
    assert recipe.is_pieces_mode is False


# 3. computed_servings for pieces recipe: 10 // 2 = 5
def test_computed_servings_pieces_mode() -> None:
    recipe = _pieces_recipe(total_pieces=10, pieces_per_portion=2)
    assert recipe.computed_servings == 5


# 4. computed_servings for normal recipe: returns servings
def test_computed_servings_normal_mode() -> None:
    recipe = _normal_recipe(servings=6)
    assert recipe.computed_servings == 6


# 5. Validation: total_pieces=0 → InvalidEntityError
def test_validation_total_pieces_zero_raises() -> None:
    with pytest.raises(InvalidEntityError):
        Recipe(
            id=RecipeId(1),
            name="Bad",
            servings=2,
            total_pieces=0,
            pieces_per_portion=1,
        )


# 6. Validation: pieces_per_portion=0 → InvalidEntityError
def test_validation_pieces_per_portion_zero_raises() -> None:
    with pytest.raises(InvalidEntityError):
        Recipe(
            id=RecipeId(1),
            name="Bad",
            servings=2,
            total_pieces=10,
            pieces_per_portion=0,
        )


# 7. Validation: total_pieces=5, pieces_per_portion=None → InvalidEntityError
def test_validation_only_total_pieces_set_raises() -> None:
    with pytest.raises(InvalidEntityError):
        Recipe(
            id=RecipeId(1),
            name="Bad",
            servings=2,
            total_pieces=5,
            pieces_per_portion=None,
        )


# 8. Validation: pieces_per_portion > total_pieces → InvalidEntityError
def test_validation_pieces_per_portion_exceeds_total_raises() -> None:
    with pytest.raises(InvalidEntityError):
        Recipe(
            id=RecipeId(1),
            name="Bad",
            servings=2,
            total_pieces=3,
            pieces_per_portion=5,
        )


# 9. scale_to(2) for pieces recipe: ingredients scale, total_pieces updates
def test_scale_to_pieces_recipe_scales_ingredients_and_total_pieces() -> None:
    # servings=4, total_pieces=10, pieces_per_portion=2, ingredient=500g
    recipe = _pieces_recipe(total_pieces=10, pieces_per_portion=2, servings=4, amount=500.0)
    # scale_to target=8 → factor = 8/4 = 2.0
    scaled = recipe.scale_to(8)
    # ingredients: 500g * 2 = 1000g
    assert scaled.ingredients[0].quantity == Quantity(1000.0, "g")
    # total_pieces: max(1, round(10 * 2)) = 20
    assert scaled.total_pieces == 20
    # pieces_per_portion unchanged
    assert scaled.pieces_per_portion == 2


# 10. scale_to for normal recipe: behavior unchanged
def test_scale_to_normal_recipe_unchanged_behavior() -> None:
    recipe = _normal_recipe(servings=2, amount=200.0)
    scaled = recipe.scale_to(4)
    assert scaled.ingredients[0].quantity == Quantity(400.0, "g")
    assert scaled.servings == 4
    assert scaled.total_pieces is None
    assert scaled.pieces_per_portion is None
