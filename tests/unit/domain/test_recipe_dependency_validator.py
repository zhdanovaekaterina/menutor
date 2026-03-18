"""Tests for RecipeDependencyValidator domain service."""

import pytest
from unittest.mock import MagicMock

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import CircularDependencyError, NestingDepthExceededError
from backend.domain.services.recipe_dependency_validator import RecipeDependencyValidator
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeId


def _make_recipe(rid: int, sub_ids: list[int] | None = None,
                 prod_ids: list[int] | None = None) -> Recipe:
    """Helper: recipe with optional sub-recipe and product ingredients."""
    ingredients: list[RecipeIngredient] = []
    for sub_id in (sub_ids or []):
        ingredients.append(RecipeIngredient(sub_recipe_id=RecipeId(sub_id), quantity=Quantity(1, "serv")))
    for pid in (prod_ids or []):
        ingredients.append(RecipeIngredient(product_id=ProductId(pid), quantity=Quantity(100, "g")))
    return Recipe(id=RecipeId(rid), name=f"Recipe{rid}", servings=2, ingredients=ingredients)


def _repo_returning(recipes: dict[int, Recipe]) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.side_effect = lambda rid: recipes.get(int(rid))
    return repo


def test_no_sub_recipes_passes() -> None:
    repo = MagicMock()
    validator = RecipeDependencyValidator(repo)
    validator.validate(RecipeId(1), [])  # no sub-recipe ids — should not raise


def test_self_reference_raises() -> None:
    repo = MagicMock()
    validator = RecipeDependencyValidator(repo)
    with pytest.raises(CircularDependencyError):
        validator.validate(RecipeId(1), [RecipeId(1)])


def test_direct_cycle_raises() -> None:
    # A uses B; B tries to use A
    recipe_b = _make_recipe(2, sub_ids=[1])
    repo = _repo_returning({2: recipe_b})
    validator = RecipeDependencyValidator(repo)
    with pytest.raises(CircularDependencyError):
        validator.validate(RecipeId(1), [RecipeId(2)])


def test_transitive_cycle_raises() -> None:
    # A uses B; B uses C; C tries to use A
    recipe_b = _make_recipe(2, sub_ids=[3])
    recipe_c = _make_recipe(3, sub_ids=[1])
    repo = _repo_returning({2: recipe_b, 3: recipe_c})
    validator = RecipeDependencyValidator(repo)
    with pytest.raises(CircularDependencyError):
        validator.validate(RecipeId(1), [RecipeId(2)])


def test_diamond_no_cycle_passes() -> None:
    # A uses B and C; C also uses B — diamond shape, not a cycle
    recipe_b = _make_recipe(2, prod_ids=[10])
    recipe_c = _make_recipe(3, sub_ids=[2])  # C uses B
    repo = _repo_returning({2: recipe_b, 3: recipe_c})
    validator = RecipeDependencyValidator(repo)
    # A is recipe 1, uses B (2) and C (3); C uses B (2) — no cycle
    validator.validate(RecipeId(1), [RecipeId(2), RecipeId(3)])


def test_depth_6_raises() -> None:
    # Chain: A→B→C→D→E→F→G (7 levels, depth 6 from A)
    # A(1) → B(2) → C(3) → D(4) → E(5) → F(6) → G(7)
    recipes = {
        2: _make_recipe(2, sub_ids=[3]),
        3: _make_recipe(3, sub_ids=[4]),
        4: _make_recipe(4, sub_ids=[5]),
        5: _make_recipe(5, sub_ids=[6]),
        6: _make_recipe(6, sub_ids=[7]),
        7: _make_recipe(7, prod_ids=[99]),
    }
    repo = _repo_returning(recipes)
    validator = RecipeDependencyValidator(repo)
    with pytest.raises(NestingDepthExceededError):
        validator.validate(RecipeId(1), [RecipeId(2)])


def test_depth_at_max_5_passes() -> None:
    # Chain: A(1)→B(2)→C(3)→D(4)→E(5)→F(6), depth=5 from A, exactly at max
    recipes = {
        2: _make_recipe(2, sub_ids=[3]),
        3: _make_recipe(3, sub_ids=[4]),
        4: _make_recipe(4, sub_ids=[5]),
        5: _make_recipe(5, sub_ids=[6]),
        6: _make_recipe(6, prod_ids=[99]),
    }
    repo = _repo_returning(recipes)
    validator = RecipeDependencyValidator(repo)
    validator.validate(RecipeId(1), [RecipeId(2)])  # should not raise


def test_nonexistent_sub_recipe_passes() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None
    validator = RecipeDependencyValidator(repo)
    validator.validate(RecipeId(1), [RecipeId(99)])  # repo returns None — no crash


def test_compute_depth_flat_recipe() -> None:
    recipe = _make_recipe(1, prod_ids=[10, 20])
    repo = _repo_returning({1: recipe})
    validator = RecipeDependencyValidator(repo)
    assert validator.compute_depth(RecipeId(1)) == 0


def test_compute_depth_one_level() -> None:
    sub = _make_recipe(2, prod_ids=[10])
    parent = _make_recipe(1, sub_ids=[2])
    repo = _repo_returning({1: parent, 2: sub})
    validator = RecipeDependencyValidator(repo)
    assert validator.compute_depth(RecipeId(1)) == 1


def test_compute_depth_nested() -> None:
    # A→B→C: depth 2
    recipe_c = _make_recipe(3, prod_ids=[10])
    recipe_b = _make_recipe(2, sub_ids=[3])
    recipe_a = _make_recipe(1, sub_ids=[2])
    repo = _repo_returning({1: recipe_a, 2: recipe_b, 3: recipe_c})
    validator = RecipeDependencyValidator(repo)
    assert validator.compute_depth(RecipeId(1)) == 2
