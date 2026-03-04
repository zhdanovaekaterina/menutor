from src.domain.entities.recipe import Recipe
from src.domain.value_objects.cooking_step import CookingStep
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import ProductId, RecipeId


def _make_recipe(servings: int = 2) -> Recipe:
    return Recipe(
        id=RecipeId(1),
        name="Test Recipe",
        servings=servings,
        ingredients=[
            RecipeIngredient(ProductId(1), Quantity(100.0, "g")),
            RecipeIngredient(ProductId(2), Quantity(200.0, "ml")),
        ],
        steps=[CookingStep(order=1, description="Mix")],
        dietary_tags=["vegetarian"],
    )


def test_scale_to_doubles_quantities() -> None:
    scaled = _make_recipe(servings=2).scale_to(4)
    assert scaled.ingredients[0].quantity == Quantity(200.0, "g")
    assert scaled.ingredients[1].quantity == Quantity(400.0, "ml")


def test_scale_to_halves_quantities() -> None:
    scaled = _make_recipe(servings=4).scale_to(2)
    assert scaled.ingredients[0].quantity == Quantity(50.0, "g")
    assert scaled.ingredients[1].quantity == Quantity(100.0, "ml")


def test_scale_to_float_target() -> None:
    scaled = _make_recipe(servings=2).scale_to(5.0)
    assert scaled.ingredients[0].quantity == Quantity(250.0, "g")


def test_scale_to_does_not_mutate_original() -> None:
    recipe = _make_recipe(servings=2)
    _ = recipe.scale_to(10)
    assert recipe.ingredients[0].quantity == Quantity(100.0, "g")
    assert recipe.servings == 2


def test_scale_to_returns_new_instance() -> None:
    recipe = _make_recipe(servings=2)
    scaled = recipe.scale_to(4)
    assert scaled is not recipe


def test_scale_to_preserves_metadata() -> None:
    recipe = _make_recipe(servings=2)
    scaled = recipe.scale_to(4)
    assert scaled.id == recipe.id
    assert scaled.name == recipe.name
    assert scaled.category_id == recipe.category_id
    assert scaled.dietary_tags == recipe.dietary_tags
    assert scaled.steps == recipe.steps


def test_scale_to_updates_servings() -> None:
    scaled = _make_recipe(servings=2).scale_to(6)
    assert scaled.servings == 6
