"""Base class for SQLite repositories — eliminates save/delete/get/find_all boilerplate."""

import sqlite3
from abc import abstractmethod
from typing import Generic, TypeVar

E = TypeVar("E")  # Entity type
I = TypeVar("I", bound=int)  # Typed ID (NewType over int)


class BaseSqliteRepository(Generic[E, I]):
    _table_name: str

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @abstractmethod
    def _get_entity_id(self, entity: E) -> int: ...

    @abstractmethod
    def _insert(self, entity: E) -> int:
        """Execute INSERT and return raw lastrowid."""
        ...

    @abstractmethod
    def _update(self, entity: E) -> None:
        """Execute UPDATE for existing entity."""
        ...

    @abstractmethod
    def _wrap_id(self, raw_id: int) -> I:
        """Wrap a raw int into the typed ID (e.g. RecipeId(raw_id))."""
        ...

    @abstractmethod
    def _row_to_entity(self, row: sqlite3.Row) -> E: ...

    def _save_children(self, entity_id: I, entity: E) -> None:
        """Override to save child records within the same transaction."""

    def save(self, entity: E) -> E:
        entity_id: I
        with self._conn:
            if self._get_entity_id(entity) == 0:
                raw_id = self._insert(entity)
                entity_id = self._wrap_id(raw_id)
            else:
                self._update(entity)
                entity_id = self._wrap_id(self._get_entity_id(entity))
            self._save_children(entity_id, entity)
        result = self.get_by_id(entity_id)
        if result is None:
            raise RuntimeError(
                f"Failed to retrieve {self._table_name} {entity_id} after save"
            )
        return result

    def delete(self, id: I) -> None:
        with self._conn:
            self._conn.execute(
                f"DELETE FROM {self._table_name} WHERE id = ?", (id,)
            )

    def get_by_id(self, id: I) -> E | None:
        row = self._conn.execute(
            f"SELECT * FROM {self._table_name} WHERE id = ?", (id,)
        ).fetchone()
        return self._row_to_entity(row) if row else None

    def find_all(self) -> list[E]:
        rows = self._conn.execute(f"SELECT * FROM {self._table_name}").fetchall()
        return [self._row_to_entity(r) for r in rows]
