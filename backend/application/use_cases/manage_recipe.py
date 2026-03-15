from dataclasses import dataclass, field
from typing import Any

from backend.application.use_cases.crud_base import (
    CreateEntity,
    DeleteEntity,
    EditEntity,
    GetEntity,
    ListEntities,
)
from backend.domain.entities.recipe import Recipe
from backend.domain.ports.recipe_category_repository import RecipeCategoryRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId, UserId


@dataclass
class RecipeData:
    name: str
    category_id: RecipeCategoryId
    servings: int
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    steps: list[CookingStep] = field(default_factory=list)
    weight: int = 0


def _build_recipe(id: RecipeId, data: RecipeData, user_id: UserId) -> Recipe:
    return Recipe(
        id=id,
        name=data.name,
        servings=data.servings,
        ingredients=list(data.ingredients),
        steps=list(data.steps),
        category_id=data.category_id,
        weight=data.weight,
        user_id=user_id,
    )


class CreateRecipe(CreateEntity):
    def __init__(self, repo: RecipeRepository) -> None:
        super().__init__(repo)

    def _build_entity(self, data: Any, user_id: UserId) -> Recipe:
        return _build_recipe(RecipeId(0), data, user_id)


class EditRecipe(EditEntity):
    _label = "Рецепт"

    def __init__(self, repo: RecipeRepository) -> None:
        super().__init__(repo)

    def _build_entity(self, id: Any, data: Any, user_id: UserId) -> Recipe:
        return _build_recipe(id, data, user_id)


DeleteRecipe = DeleteEntity
GetRecipe = GetEntity
ListRecipes = ListEntities


class ListRecipeCategories:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[ActiveCategory]:
        return self._repo.find_active()
