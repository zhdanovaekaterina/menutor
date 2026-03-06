from abc import ABC, abstractmethod


class ProductCategoryRepository(ABC):
    @abstractmethod
    def find_active(self) -> list[tuple[int, str]]: ...

    @abstractmethod
    def find_all(self) -> list[tuple[int, str, bool]]: ...

    @abstractmethod
    def save(self, name: str, category_id: int | None = None) -> int: ...

    @abstractmethod
    def delete(self, category_id: int) -> None: ...

    @abstractmethod
    def has_products(self, category_id: int) -> bool: ...
