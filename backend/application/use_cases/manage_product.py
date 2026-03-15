from dataclasses import dataclass, field
from typing import Any

from backend.application.use_cases.crud_base import (
    CreateEntity,
    DeleteEntity,
    EditEntity,
    GetEntity,
    ListEntities,
    load_owned,
)
from backend.domain.entities.product import Product
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
    conversion_factor: float = field(default=1.0)


def _build_product(id: ProductId, data: ProductData, user_id: UserId) -> Product:
    return Product(
        id=id,
        name=data.name,
        recipe_unit=data.recipe_unit,
        purchase_unit=data.purchase_unit,
        price_per_purchase_unit=data.price,
        brand=data.brand,
        supplier=data.supplier,
        conversion_factor=data.conversion_factor,
        category_id=data.category_id,
        user_id=user_id,
    )


class CreateProduct(CreateEntity):
    def __init__(self, repo: ProductRepository) -> None:
        super().__init__(repo)

    def _build_entity(self, data: Any, user_id: UserId) -> Product:
        return _build_product(ProductId(0), data, user_id)


class EditProduct(EditEntity):
    _label = "Продукт"

    def __init__(self, repo: ProductRepository) -> None:
        super().__init__(repo)

    def _build_entity(self, id: Any, data: Any, user_id: UserId) -> Product:
        return _build_product(id, data, user_id)


DeleteProduct = DeleteEntity
GetProduct = GetEntity
ListProducts = ListEntities


class UpdateProductPrice:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def execute(self, id: ProductId, price: Money, user_id: UserId) -> Product:
        product = load_owned(self._repo, id, user_id, "Продукт")
        product.price_per_purchase_unit = price
        return self._repo.save(product)


class ListProductCategories:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[ActiveCategory]:
        return self._repo.find_active()
