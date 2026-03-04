from abc import ABC, abstractmethod

from src.domain.entities.product import Product
from src.domain.value_objects.types import ProductId


class ProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: ProductId) -> Product | None: ...

    @abstractmethod
    def find_by_category(self, category: str) -> list[Product]: ...

    @abstractmethod
    def find_all(self) -> list[Product]: ...

    @abstractmethod
    def save(self, product: Product) -> Product: ...

    @abstractmethod
    def delete(self, id: ProductId) -> None: ...
