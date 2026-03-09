"""Base class for SQLite category repositories — eliminates table-name duplication."""

import sqlite3

from src.domain.value_objects.category import ActiveCategory, Category


class BaseSqliteCategoryRepository:
    _table_name: str
    _usage_query: str  # e.g. "SELECT COUNT(*) FROM products WHERE category_id = ?"

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def find_active(self) -> list[ActiveCategory]:
        rows = self._conn.execute(
            f"SELECT id, name FROM {self._table_name} WHERE active = 1 ORDER BY name"
        ).fetchall()
        return [ActiveCategory(row[0], row[1]) for row in rows]

    def find_all(self) -> list[Category]:
        rows = self._conn.execute(
            f"SELECT id, name, active FROM {self._table_name} ORDER BY name"
        ).fetchall()
        return [Category(row[0], row[1], bool(row[2])) for row in rows]

    def save(self, name: str, category_id: int | None = None) -> int:
        with self._conn:
            if category_id is None:
                cursor = self._conn.execute(
                    f"INSERT INTO {self._table_name} (name) VALUES (?)", (name,)
                )
                return cursor.lastrowid  # type: ignore[return-value]
            self._conn.execute(
                f"UPDATE {self._table_name} SET name = ?, active = 1 WHERE id = ?",
                (name, category_id),
            )
            return category_id

    def delete(self, category_id: int) -> None:
        with self._conn:
            self._conn.execute(
                f"UPDATE {self._table_name} SET active = 0 WHERE id = ?",
                (category_id,),
            )

    def is_used(self, category_id: int) -> bool:
        row = self._conn.execute(self._usage_query, (category_id,)).fetchone()
        return row[0] > 0
