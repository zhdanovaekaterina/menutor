from abc import ABC, abstractmethod

from src.domain.value_objects.category import ActiveCategory, Category


class RecipeCategoryRepository(ABC):
    @abstractmethod
    def find_active(self) -> list[ActiveCategory]: ...

    @abstractmethod
    def find_all(self) -> list[Category]: ...

    @abstractmethod
    def save(self, name: str, category_id: int | None = None) -> int: ...

    @abstractmethod
    def delete(self, category_id: int) -> None: ...

    @abstractmethod
    def has_recipes(self, category_id: int) -> bool: ...
