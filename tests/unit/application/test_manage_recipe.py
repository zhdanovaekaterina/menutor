import pytest
from unittest.mock import MagicMock

from src.domain.entities.recipe import Recipe
from src.domain.value_objects.cooking_step import CookingStep
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import ProductId, RecipeId
from src.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    EditRecipe,
    GetRecipe,
    ListRecipes,
    RecipeData,
)


def _data(**kwargs) -> RecipeData:
    defaults = dict(
        name="Паста",
        category="Основные",
        servings=4,
        ingredients=[RecipeIngredient(ProductId(1), Quantity(200.0, "g"))],
        steps=[CookingStep(1, "Варить")],
        dietary_tags=["vegetarian"],
    )
    defaults.update(kwargs)
    return RecipeData(**defaults)


def _saved_recipe(id: int = 1) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name="Паста",
        category="Основные",
        servings=4,
        ingredients=[RecipeIngredient(ProductId(1), Quantity(200.0, "g"))],
    )


# ---- CreateRecipe ----

def test_create_recipe_calls_save_and_returns_result() -> None:
    repo = MagicMock()
    repo.save.return_value = _saved_recipe()

    result = CreateRecipe(repo).execute(_data())

    repo.save.assert_called_once()
    assert result == _saved_recipe()


def test_create_recipe_builds_entity_with_correct_fields() -> None:
    repo = MagicMock()
    repo.save.side_effect = lambda r: r

    result = CreateRecipe(repo).execute(_data(name="Борщ", servings=6))

    assert result.name == "Борщ"
    assert result.servings == 6


# ---- EditRecipe ----

def test_edit_recipe_updates_fields_and_saves() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_recipe()
    repo.save.side_effect = lambda r: r

    result = EditRecipe(repo).execute(RecipeId(1), _data(name="Новое имя"))

    repo.save.assert_called_once()
    assert result.name == "Новое имя"
    assert result.id == RecipeId(1)


def test_edit_recipe_raises_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="не найден"):
        EditRecipe(repo).execute(RecipeId(999), _data())


# ---- DeleteRecipe ----

def test_delete_recipe_calls_repo_delete() -> None:
    repo = MagicMock()

    DeleteRecipe(repo).execute(RecipeId(1))

    repo.delete.assert_called_once_with(RecipeId(1))


# ---- GetRecipe ----

def test_get_recipe_returns_entity() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_recipe()

    result = GetRecipe(repo).execute(RecipeId(1))

    assert result == _saved_recipe()


def test_get_recipe_returns_none_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    assert GetRecipe(repo).execute(RecipeId(999)) is None


# ---- ListRecipes ----

def test_list_recipes_returns_all() -> None:
    repo = MagicMock()
    repo.find_all.return_value = [_saved_recipe(1), _saved_recipe(2)]

    result = ListRecipes(repo).execute()

    assert len(result) == 2
