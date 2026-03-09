import sqlite3
from decimal import Decimal

from src.domain.entities.product import Product
from src.domain.exceptions import RepositoryError
from src.domain.ports.product_repository import ProductRepository
from src.domain.value_objects.money import Money
from src.domain.value_objects.types import ProductCategoryId, ProductId
from src.infrastructure.repositories.base import BaseSqliteRepository


class SqliteProductRepository(
    BaseSqliteRepository[Product, ProductId],
    ProductRepository,
):
    _table_name = "products"
    _columns = (
        "id, name, category_id, brand, supplier, recipe_unit, "
        "purchase_unit, price_per_purchase_unit, weight_per_piece_g, conversion_factor"
    )

    def _get_entity_id(self, entity: Product) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> ProductId:
        return ProductId(raw_id)

    def _insert(self, entity: Product) -> int:
        cursor = self._conn.execute(
            "INSERT INTO products "
            "(name, category_id, brand, supplier, recipe_unit, purchase_unit, "
            "price_per_purchase_unit, weight_per_piece_g, conversion_factor) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entity.name, entity.category_id, entity.brand,
                entity.supplier, entity.recipe_unit, entity.purchase_unit,
                float(entity.price_per_purchase_unit.amount),
                entity.weight_per_piece_g,
                entity.conversion_factor,
            ),
        )
        last_id = cursor.lastrowid
        if last_id is None:
            raise RepositoryError("INSERT products did not return lastrowid")
        return last_id

    def _update(self, entity: Product) -> None:
        self._conn.execute(
            "UPDATE products SET name=?, category_id=?, brand=?, supplier=?, "
            "recipe_unit=?, purchase_unit=?, price_per_purchase_unit=?, "
            "weight_per_piece_g=?, conversion_factor=? WHERE id=?",
            (
                entity.name, entity.category_id, entity.brand,
                entity.supplier, entity.recipe_unit, entity.purchase_unit,
                float(entity.price_per_purchase_unit.amount),
                entity.weight_per_piece_g,
                entity.conversion_factor,
                entity.id,
            ),
        )

    def _row_to_entity(self, row: sqlite3.Row) -> Product:
        return Product(
            id=ProductId(row["id"]),
            name=row["name"],
            recipe_unit=row["recipe_unit"],
            purchase_unit=row["purchase_unit"],
            price_per_purchase_unit=Money(
                Decimal(str(row["price_per_purchase_unit"]))
            ),
            brand=row["brand"] or "",
            supplier=row["supplier"] or "",
            weight_per_piece_g=row["weight_per_piece_g"],
            conversion_factor=row["conversion_factor"],
            category_id=ProductCategoryId(row["category_id"]),
        )

    def find_by_category_id(self, category_id: ProductCategoryId) -> list[Product]:
        rows = self._conn.execute(
            f"SELECT {self._columns} FROM products WHERE category_id = ?",
            (category_id,)
        ).fetchall()
        return [self._row_to_entity(r) for r in rows]
