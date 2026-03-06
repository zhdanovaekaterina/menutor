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

    def find_all(self) -> list[tuple[int, str, bool]]:
        rows = self._conn.execute(
            "SELECT id, name, active FROM product_categories ORDER BY name"
        ).fetchall()
        return [(row[0], row[1], bool(row[2])) for row in rows]

    def save(self, name: str, category_id: int | None = None) -> int:
        if category_id is None:
            cursor = self._conn.execute(
                "INSERT INTO product_categories (name) VALUES (?)", (name,)
            )
            self._conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]
        self._conn.execute(
            "UPDATE product_categories SET name = ?, active = 1 WHERE id = ?",
            (name, category_id),
        )
        self._conn.commit()
        return category_id

    def delete(self, category_id: int) -> None:
        self._conn.execute(
            "UPDATE product_categories SET active = 0 WHERE id = ?", (category_id,)
        )
        self._conn.commit()

    def has_products(self, category_id: int) -> bool:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM products WHERE category_id = ?", (category_id,)
        ).fetchone()
        return row[0] > 0
