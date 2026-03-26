from unittest.mock import MagicMock, call

import pytest

from backend.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    DeleteRecipeWithDependents,
    EditRecipe,
    GetRecipe,
    ListRecipes,
    RecipeData,
)
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import CircularDependencyError, EntityNotFoundError
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId, UserId

UID = UserId(1)


def _data(**kwargs) -> RecipeData:
    defaults = dict(
        name="Паста",
        category_id=RecipeCategoryId(1),
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))],
        steps=[CookingStep(1, "Варить")],
    )
    defaults.update(kwargs)
    return RecipeData(**defaults)


def _saved_recipe(id: int = 1) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name="Паста",
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))],
        category_id=RecipeCategoryId(1),
        user_id=UID,
    )


# ---- CreateRecipe ----

def test_create_recipe_calls_save_and_returns_result() -> None:
    repo = MagicMock()
    repo.find_by_name.return_value = None
    repo.save.return_value = _saved_recipe()

    result = CreateRecipe(repo).execute(_data(), UID)

    repo.save.assert_called_once()
    assert result == _saved_recipe()


def test_create_recipe_builds_entity_with_correct_fields() -> None:
    repo = MagicMock()
    repo.find_by_name.return_value = None
    repo.save.side_effect = lambda r: r

    result = CreateRecipe(repo).execute(_data(name="Борщ", servings=6), UID)

    assert result.name == "Борщ"
    assert result.servings == 6


# ---- EditRecipe ----

def test_edit_recipe_updates_fields_and_saves() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_recipe()
    repo.save.side_effect = lambda r: r

    result = EditRecipe(repo).execute(RecipeId(1), _data(name="Новое имя"), UID)

    repo.save.assert_called_once()
    assert result.name == "Новое имя"
    assert result.id == RecipeId(1)


def test_edit_recipe_raises_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(EntityNotFoundError, match="не найден"):
        EditRecipe(repo).execute(RecipeId(999), _data(), UID)


# ---- DeleteRecipe ----

def test_delete_recipe_calls_repo_delete() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_recipe()

    DeleteRecipe(repo).execute(RecipeId(1), UID)

    repo.delete.assert_called_once_with([RecipeId(1)])


# ---- GetRecipe ----

def test_get_recipe_returns_entity() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_recipe()

    result = GetRecipe(repo).execute(RecipeId(1), UID)

    assert result == _saved_recipe()


def test_get_recipe_returns_none_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    assert GetRecipe(repo).execute(RecipeId(999), UID) is None


# ---- ListRecipes ----

def test_list_recipes_returns_all() -> None:
    repo = MagicMock()
    repo.find_all.return_value = [_saved_recipe(1), _saved_recipe(2)]

    result = ListRecipes(repo).execute(UID)

    assert result.total == 2
    assert len(result.items) == 2


# ---- CreateRecipe with sub-recipe validation (Task 2.2) ----

def _sub_recipe_ingredient(sub_recipe_id: int = 10) -> RecipeIngredient:
    return RecipeIngredient(sub_recipe_id=RecipeId(sub_recipe_id), quantity=Quantity(1.0, "serv"))


def _sub_recipe(id: int = 10, user_id: UserId = UID) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name="Соус",
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(2), quantity=Quantity(100.0, "g"))],
        category_id=RecipeCategoryId(1),
        user_id=user_id,
    )


def test_create_recipe_with_sub_recipe_calls_validator() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.find_by_name.return_value = None
    repo.get_by_id.return_value = _sub_recipe()
    repo.save.side_effect = lambda r: r

    data = _data(ingredients=[_sub_recipe_ingredient()])
    CreateRecipe(repo, validator).execute(data, UID)

    validator.validate.assert_called_once()


def test_create_recipe_sub_recipe_not_found_raises() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.find_by_name.return_value = None
    repo.get_by_id.return_value = None

    data = _data(ingredients=[_sub_recipe_ingredient()])
    with pytest.raises(EntityNotFoundError, match="не найден"):
        CreateRecipe(repo, validator).execute(data, UID)


def test_create_recipe_sub_recipe_wrong_user_raises() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.find_by_name.return_value = None
    other_uid = UserId(99)
    repo.get_by_id.return_value = _sub_recipe(user_id=other_uid)

    data = _data(ingredients=[_sub_recipe_ingredient()])
    with pytest.raises(EntityNotFoundError, match="не найден"):
        CreateRecipe(repo, validator).execute(data, UID)


def test_create_recipe_circular_dependency_raises() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.find_by_name.return_value = None
    repo.get_by_id.return_value = _sub_recipe()
    validator.validate.side_effect = CircularDependencyError("цикл")

    data = _data(ingredients=[_sub_recipe_ingredient()])
    with pytest.raises(CircularDependencyError):
        CreateRecipe(repo, validator).execute(data, UID)


def test_create_recipe_without_sub_recipes_skips_validation() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.find_by_name.return_value = None
    repo.save.side_effect = lambda r: r

    # product-only ingredients
    data = _data(ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))])
    CreateRecipe(repo, validator).execute(data, UID)

    validator.validate.assert_not_called()


def test_edit_recipe_with_sub_recipe_calls_validator() -> None:
    repo = MagicMock()
    validator = MagicMock()
    repo.get_by_id.side_effect = lambda rid: (
        _saved_recipe() if rid == RecipeId(1) else _sub_recipe()
    )
    repo.save.side_effect = lambda r: r

    data = _data(ingredients=[_sub_recipe_ingredient()])
    EditRecipe(repo, validator).execute(RecipeId(1), data, UID)

    validator.validate.assert_called_once()


# ---- DeleteRecipeWithDependents (Task 2.3) ----

def _parent_recipe_with_sub(sub_id: int = 10) -> Recipe:
    """A parent recipe that has one product ingredient and one sub-recipe ingredient."""
    return Recipe(
        id=RecipeId(2),
        name="Паста с соусом",
        servings=2,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g")),
            RecipeIngredient(sub_recipe_id=RecipeId(sub_id), quantity=Quantity(1.0, "serv")),
        ],
        category_id=RecipeCategoryId(1),
        user_id=UID,
    )


def test_check_dependents_returns_parent_recipes() -> None:
    repo = MagicMock()
    parent = _parent_recipe_with_sub()
    repo.find_parents_of.return_value = [parent]

    result = DeleteRecipeWithDependents(repo).check_dependents(RecipeId(10), UID)

    repo.find_parents_of.assert_called_once_with(RecipeId(10), UID)
    assert result == [parent]


def test_delete_removes_sub_recipe_from_parents() -> None:
    repo = MagicMock()
    sub_id = RecipeId(10)
    parent = _parent_recipe_with_sub(sub_id=10)

    # get_by_id for the recipe being deleted → returns it (same user)
    repo.get_by_id.return_value = _sub_recipe(id=10)
    # find_parents_of returns the parent
    repo.find_parents_of.return_value = [parent]
    repo.save.side_effect = lambda r: r

    DeleteRecipeWithDependents(repo).execute(sub_id, UID)

    # parent should be saved with sub-recipe ingredient removed
    repo.save.assert_called_once()
    saved_parent = repo.save.call_args[0][0]
    assert len(saved_parent.ingredients) == 1
    assert saved_parent.ingredients[0].is_product

    # then delete the recipe itself
    repo.delete.assert_called_once_with([sub_id])


def test_delete_recipe_with_no_dependents_works() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _sub_recipe(id=10)
    repo.find_parents_of.return_value = []

    DeleteRecipeWithDependents(repo).execute(RecipeId(10), UID)

    repo.save.assert_not_called()
    repo.delete.assert_called_once_with([RecipeId(10)])


def test_delete_nonexistent_is_no_op() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    DeleteRecipeWithDependents(repo).execute(RecipeId(999), UID)

    repo.delete.assert_not_called()
    repo.find_parents_of.assert_not_called()
