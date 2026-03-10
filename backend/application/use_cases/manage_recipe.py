from dataclasses import dataclass, field

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.recipe_category_repository import RecipeCategoryRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId


@dataclass
class RecipeData:
    name: str
    category_id: RecipeCategoryId
    servings: int
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    steps: list[CookingStep] = field(default_factory=list)
    weight: int = 0


class CreateRecipe:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def execute(self, data: RecipeData) -> Recipe:
        recipe = Recipe(
            id=RecipeId(0),
            name=data.name,
            servings=data.servings,
            ingredients=list(data.ingredients),
            steps=list(data.steps),
            category_id=data.category_id,
            weight=data.weight,
        )
        return self._repo.save(recipe)


class EditRecipe:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def execute(self, id: RecipeId, data: RecipeData) -> Recipe:
        if self._repo.get_by_id(id) is None:
            raise EntityNotFoundError(f"Рецепт {id} не найден")
        recipe = Recipe(
            id=id,
            name=data.name,
            servings=data.servings,
            ingredients=list(data.ingredients),
            steps=list(data.steps),
            category_id=data.category_id,
            weight=data.weight,
        )
        return self._repo.save(recipe)


class DeleteRecipe:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def execute(self, id: RecipeId) -> None:
        self._repo.delete(id)


class GetRecipe:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def execute(self, id: RecipeId) -> Recipe | None:
        return self._repo.get_by_id(id)


class ListRecipes:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Recipe]:
        return self._repo.find_all()


class ListRecipeCategories:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[ActiveCategory]:
        return self._repo.find_active()
