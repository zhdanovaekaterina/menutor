from abc import ABC, abstractmethod

from backend.domain.value_objects.category import ActiveCategory, Category


class CategoryRepository(ABC):
    @abstractmethod
    def find_active(self) -> list[ActiveCategory]: ...

    @abstractmethod
    def find_all(self) -> list[Category]: ...

    @abstractmethod
    def save(self, name: str, category_id: int | None = None) -> int: ...

    @abstractmethod
    def delete(self, category_id: int) -> None: ...

    @abstractmethod
    def hard_delete(self, category_id: int) -> None: ...

    @abstractmethod
    def activate(self, category_id: int) -> None: ...

    @abstractmethod
    def is_used(self, category_id: int) -> bool: ...

    @abstractmethod
    def move_and_delete(self, from_id: int, to_id: int) -> None:
        """Move all linked rows from `from_id` category to `to_id`, then delete `from_id`. Transactional."""
