from dataclasses import dataclass, field

from src.domain.entities.recipe import Recipe
from src.domain.ports.recipe_category_repository import RecipeCategoryRepository
from src.domain.ports.recipe_repository import RecipeRepository
from src.domain.value_objects.cooking_step import CookingStep
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import RecipeCategoryId, RecipeId


@dataclass
class RecipeData:
    name: str
    category_id: RecipeCategoryId
    servings: int
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    steps: list[CookingStep] = field(default_factory=list)
    dietary_tags: list[str] = field(default_factory=list)


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
            dietary_tags=list(data.dietary_tags),
            category_id=data.category_id,
        )
        return self._repo.save(recipe)


class EditRecipe:
    def __init__(self, repo: RecipeRepository) -> None:
        self._repo = repo

    def execute(self, id: RecipeId, data: RecipeData) -> Recipe:
        if self._repo.get_by_id(id) is None:
            raise ValueError(f"Рецепт {id} не найден")
        recipe = Recipe(
            id=id,
            name=data.name,
            servings=data.servings,
            ingredients=list(data.ingredients),
            steps=list(data.steps),
            dietary_tags=list(data.dietary_tags),
            category_id=data.category_id,
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

    def execute(self) -> list[tuple[int, str]]:
        return self._repo.find_active()
