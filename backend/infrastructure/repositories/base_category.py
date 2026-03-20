"""Base ORM repository for category tables (product_categories, recipe_categories)."""

from typing import Any, ClassVar

from sqlalchemy.orm import Session

from backend.domain.exceptions import AppError
from backend.domain.value_objects.category import ActiveCategory, Category


class BaseOrmCategoryRepository:
    _cat_class: ClassVar[Any]     # ORM row class for the category table
    _linked_class: ClassVar[Any]  # ORM row class with a category_id FK
    _linked_fk_col: ClassVar[str]  # Attribute name on _linked_class, e.g. "category_id"

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _linked_fk_attr(self) -> Any:
        return getattr(self._linked_class, self._linked_fk_col)

    # ------------------------------------------------------------------
    # Public API (mirrors the CategoryRepository port)
    # ------------------------------------------------------------------

    def find_active(self) -> list[ActiveCategory]:
        rows: list[Any] = (
            self._session.query(self._cat_class)
            .filter(self._cat_class.active == True)  # noqa: E712
            .order_by(self._cat_class.name)
            .all()
        )
        return [ActiveCategory(r.id, r.name) for r in rows]

    def find_all(self) -> list[Category]:
        rows: list[Any] = (
            self._session.query(self._cat_class)
            .order_by(self._cat_class.name)
            .all()
        )
        return [Category(r.id, r.name, bool(r.active)) for r in rows]

    def save(self, name: str, category_id: int | None = None) -> int:
        if category_id is None:
            row = self._cat_class(name=name)
            self._session.add(row)
            self._session.flush()
            new_id: int = row.id
            self._session.commit()
            return new_id
        row = self._session.get(self._cat_class, category_id)
        if row is not None:
            row.name = name
            row.active = True
        self._session.commit()
        return category_id

    def delete(self, category_id: int) -> None:
        row = self._session.get(self._cat_class, category_id)
        if row is not None:
            row.active = False
            self._session.commit()

    def hard_delete(self, category_id: int) -> None:
        self._session.query(self._linked_class).filter(
            self._linked_fk_attr() == category_id
        ).delete(synchronize_session=False)
        row = self._session.get(self._cat_class, category_id)
        if row is not None:
            self._session.delete(row)
        self._session.commit()

    def activate(self, category_id: int) -> None:
        row = self._session.get(self._cat_class, category_id)
        if row is not None:
            row.active = True
            self._session.commit()

    def is_used(self, category_id: int) -> bool:
        count = (
            self._session.query(self._linked_class)
            .filter(self._linked_fk_attr() == category_id)
            .count()
        )
        return count > 0

    def move_and_delete(self, from_id: int, to_id: int) -> None:
        try:
            target = self._session.get(self._cat_class, to_id)
            if target is None:
                raise AppError(
                    f"Категория назначения с id={to_id} не найдена"
                )
            self._session.query(self._linked_class).filter(
                self._linked_fk_attr() == from_id
            ).update({self._linked_fk_col: to_id}, synchronize_session=False)
            row = self._session.get(self._cat_class, from_id)
            if row is not None:
                self._session.delete(row)
            self._session.commit()
        except AppError:
            self._session.rollback()
            raise
        except Exception:
            self._session.rollback()
            raise
