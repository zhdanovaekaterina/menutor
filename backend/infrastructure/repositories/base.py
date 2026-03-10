"""Base ORM repository — shared save/delete/get_by_id/find_all logic."""

from abc import abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from backend.domain.exceptions import RepositoryError

E = TypeVar("E")   # Domain entity type
I = TypeVar("I", bound=int)  # Typed ID (NewType over int)


class BaseOrmRepository(Generic[E, I]):
    _row_class: type  # SQLAlchemy ORM model class, e.g. RecipeRow

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _get_entity_id(self, entity: E) -> int:
        """Return the entity's ID (0 for new entities)."""
        ...

    @abstractmethod
    def _wrap_id(self, raw_id: int) -> I:
        """Wrap a raw int into the typed domain ID, e.g. RecipeId(raw_id)."""
        ...

    @abstractmethod
    def _make_new_row(self, entity: E) -> Any:
        """Create a new ORM row object ready to be added to the session."""
        ...

    @abstractmethod
    def _update_row(self, row: Any, entity: E) -> None:
        """Update an existing ORM row's fields in-place."""
        ...

    @abstractmethod
    def _row_to_entity(self, row: Any) -> E:
        """Convert an ORM row to a domain entity."""
        ...

    # ------------------------------------------------------------------
    # Shared CRUD
    # ------------------------------------------------------------------

    def save(self, entity: E) -> E:
        entity_id = self._get_entity_id(entity)
        if entity_id == 0:
            row = self._make_new_row(entity)
            self._session.add(row)
            self._session.flush()
            new_id = self._wrap_id(row.id)
        else:
            row = self._session.get(self._row_class, entity_id)
            if row is None:
                raise RepositoryError(
                    f"Entity {entity_id} not found in {self._row_class.__tablename__}"
                )
            self._update_row(row, entity)
            new_id = self._wrap_id(entity_id)
        self._session.commit()
        result = self.get_by_id(new_id)
        if result is None:
            raise RepositoryError(
                f"Failed to reload {self._row_class.__tablename__} {new_id} after save"
            )
        return result

    def delete(self, id: I) -> None:
        row = self._session.get(self._row_class, int(id))
        if row is not None:
            self._session.delete(row)
            self._session.commit()

    def get_by_id(self, id: I) -> E | None:
        row = self._session.get(self._row_class, int(id))
        if row is None:
            return None
        self._session.refresh(row)
        return self._row_to_entity(row)

    def find_all(self) -> list[E]:
        rows = self._session.query(self._row_class).all()
        return [self._row_to_entity(r) for r in rows]
