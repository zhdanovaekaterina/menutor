from dataclasses import dataclass, field

from backend.domain.entities.product import Product
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.product_category_repository import ProductCategoryRepository
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId


@dataclass
class ProductData:
    name: str
    category_id: ProductCategoryId
    recipe_unit: str
    purchase_unit: str
    price: Money
    brand: str = field(default="")
    supplier: str = field(default="")
    weight_per_piece_g: float | None = field(default=None)
    conversion_factor: float = field(default=1.0)


class CreateProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, data: ProductData, user_id: UserId) -> Product:
        product = Product(
            id=ProductId(0),
            name=data.name,
            recipe_unit=data.recipe_unit,
            purchase_unit=data.purchase_unit,
            price_per_purchase_unit=data.price,
            brand=data.brand,
            supplier=data.supplier,
            weight_per_piece_g=data.weight_per_piece_g,
            conversion_factor=data.conversion_factor,
            category_id=data.category_id,
            user_id=user_id,
        )
        return self._repo.save(product)


class EditProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId, data: ProductData, user_id: UserId) -> Product:
        existing = self._repo.get_by_id(id)
        if existing is None or existing.user_id != user_id:
            raise EntityNotFoundError(f"Продукт {id} не найден")
        product = Product(
            id=id,
            name=data.name,
            recipe_unit=data.recipe_unit,
            purchase_unit=data.purchase_unit,
            price_per_purchase_unit=data.price,
            brand=data.brand,
            supplier=data.supplier,
            weight_per_piece_g=data.weight_per_piece_g,
            conversion_factor=data.conversion_factor,
            category_id=data.category_id,
            user_id=user_id,
        )
        return self._repo.save(product)


class DeleteProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId, user_id: UserId) -> None:
        existing = self._repo.get_by_id(id)
        if existing is not None and existing.user_id == user_id:
            self._repo.delete(id)


class UpdateProductPrice:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId, price: Money, user_id: UserId) -> Product:
        product = self._repo.get_by_id(id)
        if product is None or product.user_id != user_id:
            raise EntityNotFoundError(f"Продукт {id} не найден")
        product.price_per_purchase_unit = price
        return self._repo.save(product)


class GetProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId, user_id: UserId) -> Product | None:
        product = self._repo.get_by_id(id)
        if product is not None and product.user_id != user_id:
            return None
        return product


class ListProducts:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> list[Product]:
        return self._repo.find_all(user_id)


class ListProductCategories:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[ActiveCategory]:
        return self._repo.find_active()
