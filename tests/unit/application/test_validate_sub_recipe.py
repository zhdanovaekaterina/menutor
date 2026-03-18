from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.validate_sub_recipe import ValidateSubRecipe
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import CircularDependencyError, NestingDepthExceededError
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId, UserId

UID = UserId(1)


def _recipe(id: int = 10, user_id: UserId = UID) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name="Соус",
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100.0, "g"))],
        category_id=RecipeCategoryId(1),
        user_id=user_id,
    )


def test_validate_valid_sub_recipe() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.get_by_id.return_value = _recipe()

    result = ValidateSubRecipe(repo, validator).execute(
        parent_recipe_id=RecipeId(1),
        sub_recipe_id=RecipeId(10),
        user_id=UID,
    )

    assert result.valid is True
    assert result.error is None


def test_validate_circular_returns_invalid() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.get_by_id.return_value = _recipe()
    validator.validate.side_effect = CircularDependencyError("цикл")

    result = ValidateSubRecipe(repo, validator).execute(
        parent_recipe_id=RecipeId(1),
        sub_recipe_id=RecipeId(10),
        user_id=UID,
    )

    assert result.valid is False
    assert result.error is not None
    assert "цикл" in result.error


def test_validate_nesting_depth_exceeded_returns_invalid() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.get_by_id.return_value = _recipe()
    validator.validate.side_effect = NestingDepthExceededError("превышена глубина")

    result = ValidateSubRecipe(repo, validator).execute(
        parent_recipe_id=RecipeId(1),
        sub_recipe_id=RecipeId(10),
        user_id=UID,
    )

    assert result.valid is False
    assert result.error is not None
    assert "превышена глубина" in result.error


def test_validate_nonexistent_returns_invalid() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.get_by_id.return_value = None

    result = ValidateSubRecipe(repo, validator).execute(
        parent_recipe_id=RecipeId(1),
        sub_recipe_id=RecipeId(999),
        user_id=UID,
    )

    assert result.valid is False
    assert result.error is not None
    validator.validate.assert_not_called()


def test_validate_wrong_user_returns_invalid() -> None:
    repo = MagicMock()
    validator = MagicMock()
    other_uid = UserId(99)
    repo.get_by_id.return_value = _recipe(user_id=other_uid)

    result = ValidateSubRecipe(repo, validator).execute(
        parent_recipe_id=RecipeId(1),
        sub_recipe_id=RecipeId(10),
        user_id=UID,
    )

    assert result.valid is False
    assert result.error is not None
    validator.validate.assert_not_called()


def test_validate_new_recipe_no_parent_id() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.get_by_id.return_value = _recipe()

    result = ValidateSubRecipe(repo, validator).execute(
        parent_recipe_id=None,
        sub_recipe_id=RecipeId(10),
        user_id=UID,
    )

    assert result.valid is True
    assert result.error is None
    # cycle check must be skipped when no parent exists
    validator.validate.assert_not_called()
