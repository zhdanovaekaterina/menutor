from abc import ABC, abstractmethod

from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId, UserId


class RecipeRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: RecipeId) -> Recipe | None: ...

    @abstractmethod
    def find_by_category_id(
        self, category_id: RecipeCategoryId, user_id: UserId
    ) -> list[Recipe]: ...

    @abstractmethod
    def find_all(self, user_id: UserId) -> list[Recipe]: ...

    @abstractmethod
    def count(
        self,
        user_id: UserId,
        search: str = "",
        category_id: RecipeCategoryId | None = None,
    ) -> int: ...

    @abstractmethod
    def find_page(
        self,
        user_id: UserId,
        search: str,
        limit: int,
        offset: int,
        category_id: RecipeCategoryId | None = None,
    ) -> list[Recipe]: ...

    @abstractmethod
    def save(self, recipe: Recipe) -> Recipe: ...

    @abstractmethod
    def delete(self, ids: list[RecipeId]) -> None: ...

    @abstractmethod
    def find_parents_of(
        self, sub_recipe_id: RecipeId, user_id: UserId
    ) -> list[Recipe]: ...

    @abstractmethod
    def find_by_name(self, name: str, user_id: UserId) -> Recipe | None: ...
