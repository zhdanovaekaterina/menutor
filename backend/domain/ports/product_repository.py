from abc import ABC, abstractmethod

from backend.domain.entities.product import Product
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId


class ProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: ProductId) -> Product | None: ...

    @abstractmethod
    def find_by_category_id(
        self, category_id: ProductCategoryId, user_id: UserId
    ) -> list[Product]: ...

    @abstractmethod
    def find_all(self, user_id: UserId) -> list[Product]: ...

    @abstractmethod
    def save(self, product: Product) -> Product: ...

    @abstractmethod
    def delete(self, id: ProductId) -> None: ...
