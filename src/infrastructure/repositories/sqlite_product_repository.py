import sqlite3
from decimal import Decimal

from src.domain.entities.product import Product
from src.domain.ports.product_repository import ProductRepository
from src.domain.value_objects.money import Money
from src.domain.value_objects.types import ProductCategoryId, ProductId


class SqliteProductRepository(ProductRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ---- read ----

    def get_by_id(self, id: ProductId) -> Product | None:
        row = self._conn.execute(
            "SELECT * FROM products WHERE id = ?", (id,)
        ).fetchone()
        return self._row_to_entity(row) if row else None

    def find_by_category_id(self, category_id: ProductCategoryId) -> list[Product]:
        rows = self._conn.execute(
            "SELECT * FROM products WHERE category_id = ?", (category_id,)
        ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def find_all(self) -> list[Product]:
        rows = self._conn.execute("SELECT * FROM products").fetchall()
        return [self._row_to_entity(r) for r in rows]

    # ---- write ----

    def save(self, product: Product) -> Product:
        product_id: ProductId
        with self._conn:
            if product.id == 0:
                cursor = self._conn.execute(
                    "INSERT INTO products "
                    "(name, category_id, brand, supplier, recipe_unit, purchase_unit, "
                    "price_per_purchase_unit, weight_per_piece_g, conversion_factor) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        product.name, product.category_id, product.brand,
                        product.supplier, product.recipe_unit, product.purchase_unit,
                        float(product.price_per_purchase_unit.amount),
                        product.weight_per_piece_g,
                        product.conversion_factor,
                    ),
                )
                last_id = cursor.lastrowid
                if last_id is None:
                    raise RuntimeError("INSERT products did not return lastrowid")
                product_id = ProductId(last_id)
            else:
                self._conn.execute(
                    "UPDATE products SET name=?, category_id=?, brand=?, supplier=?, "
                    "recipe_unit=?, purchase_unit=?, price_per_purchase_unit=?, "
                    "weight_per_piece_g=?, conversion_factor=? WHERE id=?",
                    (
                        product.name, product.category_id, product.brand,
                        product.supplier, product.recipe_unit, product.purchase_unit,
                        float(product.price_per_purchase_unit.amount),
                        product.weight_per_piece_g,
                        product.conversion_factor,
                        product.id,
                    ),
                )
                product_id = product.id

        result = self.get_by_id(product_id)
        if result is None:
            raise RuntimeError(f"Failed to retrieve product {product_id} after save")
        return result

    def delete(self, id: ProductId) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM products WHERE id = ?", (id,))

    # ---- mapping ----

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
