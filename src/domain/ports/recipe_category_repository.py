from abc import ABC, abstractmethod


class RecipeCategoryRepository(ABC):
    @abstractmethod
    def find_active(self) -> list[tuple[int, str]]: ...
