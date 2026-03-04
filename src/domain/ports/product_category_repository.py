from abc import ABC, abstractmethod


class ProductCategoryRepository(ABC):
    @abstractmethod
    def find_active(self) -> list[tuple[int, str]]: ...
