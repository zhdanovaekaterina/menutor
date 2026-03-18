import dataclasses
from dataclasses import dataclass, field
from typing import Any

from backend.application.use_cases.crud_base import (
    CreateEntity,
    EditEntity,
    GetEntity,
    ListEntities,
)
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.recipe_category_repository import RecipeCategoryRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.services.recipe_dependency_validator import (
    RecipeDependencyValidator,
)
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


def _validate_sub_recipe_ingredients(
    recipe: Recipe,
    user_id: UserId,
    repo: RecipeRepository,
    validator: RecipeDependencyValidator,
) -> None:
    """Validate sub-recipe references: existence, ownership, and no cycles."""
    sub_recipe_ids: list[RecipeId] = []
    for ing in recipe.ingredients:
        if ing.is_sub_recipe:
            assert ing.sub_recipe_id is not None
            sub = repo.get_by_id(ing.sub_recipe_id)
            if sub is None or sub.user_id != user_id:
                raise EntityNotFoundError(
                    f"Рецепт-ингредиент {ing.sub_recipe_id} не найден"
                )
            sub_recipe_ids.append(ing.sub_recipe_id)
    if sub_recipe_ids:
        validator.validate(recipe.id, sub_recipe_ids)


class CreateRecipe(CreateEntity):
    def __init__(
        self,
        repo: RecipeRepository,
        validator: RecipeDependencyValidator | None = None,
    ) -> None:
        super().__init__(repo)
        self._validator = validator

    def _build_entity(self, data: Any, user_id: UserId) -> Recipe:
        return _build_recipe(RecipeId(0), data, user_id)

    def execute(self, data: Any, user_id: UserId) -> Any:
        entity = self._build_entity(data, user_id)
        if self._validator is not None:
            _validate_sub_recipe_ingredients(entity, user_id, self._repo, self._validator)
        return self._repo.save(entity)


class EditRecipe(EditEntity):
    _label = "Рецепт"

    def __init__(
        self,
        repo: RecipeRepository,
        validator: RecipeDependencyValidator | None = None,
    ) -> None:
        super().__init__(repo)
        self._validator = validator

    def _build_entity(self, id: Any, data: Any, user_id: UserId) -> Recipe:
        return _build_recipe(id, data, user_id)

    def execute(self, id: Any, data: Any, user_id: UserId) -> Any:
        from backend.application.use_cases.crud_base import load_owned
        load_owned(self._repo, id, user_id, self._label)
        entity = self._build_entity(id, data, user_id)
        if self._validator is not None:
            _validate_sub_recipe_ingredients(entity, user_id, self._repo, self._validator)
        return self._repo.save(entity)


class DeleteRecipeWithDependents:
    """Deletes recipes, removing sub-recipe references from parent recipes first."""

    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def check_dependents(
        self, recipe_id: RecipeId, user_id: UserId
    ) -> list[Recipe]:
        """Return parent recipes that reference this recipe as a sub-ingredient."""
        return self._repo.find_parents_of(recipe_id, user_id)

    def execute(
        self,
        ids: RecipeId | list[RecipeId],
        user_id: UserId,
    ) -> None:
        if not isinstance(ids, list):
            ids = [ids]
        owned: list[RecipeId] = []
        for id in ids:
            existing = self._repo.get_by_id(id)
            if existing is not None and existing.user_id == user_id:
                owned.append(id)
        if not owned:
            return
        # Remove sub-recipe references from parent recipes before deleting
        for recipe_id in owned:
            parents = self._repo.find_parents_of(recipe_id, user_id)
            for parent in parents:
                updated_ingredients = [
                    ing for ing in parent.ingredients
                    if not (ing.is_sub_recipe and ing.sub_recipe_id == recipe_id)
                ]
                if len(updated_ingredients) != len(parent.ingredients):
                    updated_parent = dataclasses.replace(
                        parent, ingredients=updated_ingredients
                    )
                    self._repo.save(updated_parent)
        self._repo.delete(owned)


# Keep alias for backward compatibility
DeleteRecipe = DeleteRecipeWithDependents
GetRecipe = GetEntity
ListRecipes = ListEntities


class ListRecipeCategories:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[ActiveCategory]:
        return self._repo.find_active()
