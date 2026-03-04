from dataclasses import dataclass, field

from src.domain.entities.product import Product
from src.domain.ports.product_repository import ProductRepository
from src.domain.value_objects.money import Money
from src.domain.value_objects.types import ProductId


@dataclass
class ProductData:
    name: str
    category: str
    recipe_unit: str
    purchase_unit: str
    price: Money
    brand: str = field(default="")
    weight_per_piece_g: float | None = field(default=None)
    conversion_factor: float = field(default=1.0)


class CreateProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, data: ProductData) -> Product:
        product = Product(
            id=ProductId(0),
            name=data.name,
            category=data.category,
            recipe_unit=data.recipe_unit,
            purchase_unit=data.purchase_unit,
            price_per_purchase_unit=data.price,
            brand=data.brand,
            weight_per_piece_g=data.weight_per_piece_g,
            conversion_factor=data.conversion_factor,
        )
        return self._repo.save(product)


class EditProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId, data: ProductData) -> Product:
        if self._repo.get_by_id(id) is None:
            raise ValueError(f"Продукт {id} не найден")
        product = Product(
            id=id,
            name=data.name,
            category=data.category,
            recipe_unit=data.recipe_unit,
            purchase_unit=data.purchase_unit,
            price_per_purchase_unit=data.price,
            brand=data.brand,
            weight_per_piece_g=data.weight_per_piece_g,
            conversion_factor=data.conversion_factor,
        )
        return self._repo.save(product)


class DeleteProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId) -> None:
        self._repo.delete(id)


class UpdateProductPrice:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId, price: Money) -> Product:
        product = self._repo.get_by_id(id)
        if product is None:
            raise ValueError(f"Продукт {id} не найден")
        product.price_per_purchase_unit = price
        return self._repo.save(product)


class GetProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId) -> Product | None:
        return self._repo.get_by_id(id)


class ListProducts:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Product]:
        return self._repo.find_all()
