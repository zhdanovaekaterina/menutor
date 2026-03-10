from abc import ABC, abstractmethod

from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId


class RecipeRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: RecipeId) -> Recipe | None: ...

    @abstractmethod
    def find_by_category_id(self, category_id: RecipeCategoryId) -> list[Recipe]: ...

    @abstractmethod
    def find_all(self) -> list[Recipe]: ...

    @abstractmethod
    def save(self, recipe: Recipe) -> Recipe: ...

    @abstractmethod
    def delete(self, id: RecipeId) -> None: ...
