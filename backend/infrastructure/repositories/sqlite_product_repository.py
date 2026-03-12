from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.product import Product
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId
from backend.infrastructure.database.models import ProductRow
from backend.infrastructure.repositories.base import BaseOrmRepository


class SqliteProductRepository(
    BaseOrmRepository[Product, ProductId],
    ProductRepository,
):
    _row_class = ProductRow

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_entity_id(self, entity: Product) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> ProductId:
        return ProductId(raw_id)

    def _make_new_row(self, entity: Product) -> ProductRow:
        return ProductRow(
            user_id=int(entity.user_id),
            name=entity.name,
            category_id=entity.category_id,
            brand=entity.brand,
            supplier=entity.supplier,
            recipe_unit=entity.recipe_unit,
            purchase_unit=entity.purchase_unit,
            price_per_purchase_unit=float(entity.price_per_purchase_unit.amount),
            weight_per_piece_g=entity.weight_per_piece_g,
            conversion_factor=entity.conversion_factor,
        )

    def _update_row(self, row: Any, entity: Product) -> None:
        row.name = entity.name
        row.category_id = entity.category_id
        row.brand = entity.brand
        row.supplier = entity.supplier
        row.recipe_unit = entity.recipe_unit
        row.purchase_unit = entity.purchase_unit
        row.price_per_purchase_unit = float(entity.price_per_purchase_unit.amount)
        row.weight_per_piece_g = entity.weight_per_piece_g
        row.conversion_factor = entity.conversion_factor

    def _row_to_entity(self, row: Any) -> Product:
        return Product(
            id=ProductId(row.id),
            name=row.name,
            recipe_unit=row.recipe_unit,
            purchase_unit=row.purchase_unit,
            price_per_purchase_unit=Money(Decimal(str(row.price_per_purchase_unit))),
            brand=row.brand or "",
            supplier=row.supplier or "",
            weight_per_piece_g=row.weight_per_piece_g,
            conversion_factor=row.conversion_factor,
            category_id=ProductCategoryId(row.category_id),
            user_id=UserId(row.user_id),
        )

    def find_all(self, user_id: UserId) -> list[Product]:
        rows = (
            self._session.query(ProductRow)
            .filter(ProductRow.user_id == int(user_id))
            .all()
        )
        return [self._row_to_entity(r) for r in rows]

    def find_by_category_id(
        self, category_id: ProductCategoryId, user_id: UserId
    ) -> list[Product]:
        rows = (
            self._session.query(ProductRow)
            .filter(
                ProductRow.category_id == category_id,
                ProductRow.user_id == int(user_id),
            )
            .all()
        )
        return [self._row_to_entity(r) for r in rows]
