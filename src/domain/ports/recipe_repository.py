from abc import ABC, abstractmethod

from src.domain.entities.recipe import Recipe
from src.domain.value_objects.types import RecipeId


class RecipeRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: RecipeId) -> Recipe | None: ...

    @abstractmethod
    def find_by_category(self, category: str) -> list[Recipe]: ...

    @abstractmethod
    def find_all(self) -> list[Recipe]: ...

    @abstractmethod
    def save(self, recipe: Recipe) -> Recipe: ...

    @abstractmethod
    def delete(self, id: RecipeId) -> None: ...
