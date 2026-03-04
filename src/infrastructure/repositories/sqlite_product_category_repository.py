import sqlite3

from src.domain.ports.product_category_repository import ProductCategoryRepository


class SqliteProductCategoryRepository(ProductCategoryRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def find_active(self) -> list[tuple[int, str]]:
        rows = self._conn.execute(
            "SELECT id, name FROM product_categories WHERE active = 1 ORDER BY name"
        ).fetchall()
        return [(row[0], row[1]) for row in rows]
