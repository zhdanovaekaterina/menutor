"""Generic CRUD use case base classes.

Eliminates boilerplate across Recipe, Product, and FamilyMember domains.
Create/Edit require subclassing with a concrete _build_entity method.
Delete, Get, List are fully generic and can be used as aliases.
"""

from abc import ABC, abstractmethod
from typing import Any

from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import UserId


def load_owned(
    repo: Any, id: Any, user_id: UserId,
    label: str = "Объект", *, not_found: str = "не найден",
) -> Any:
    """Load entity by id and verify ownership. Raises EntityNotFoundError."""
    entity = repo.get_by_id(id)
    if entity is None or entity.user_id != user_id:
        raise EntityNotFoundError(f"{label} {id} {not_found}")
    return entity


class CreateEntity(ABC):
    """Base for creating a user-owned entity."""

    def __init__(self, repo: Any) -> None:
        self._repo = repo

    @abstractmethod
    def _build_entity(self, data: Any, user_id: UserId) -> Any: ...

    def execute(self, data: Any, user_id: UserId) -> Any:
        entity = self._build_entity(data, user_id)
        return self._repo.save(entity)


class EditEntity(ABC):
    """Base for editing a user-owned entity with ownership check."""

    _label: str = "Объект"

    def __init__(self, repo: Any) -> None:
        self._repo = repo

    @abstractmethod
    def _build_entity(self, id: Any, data: Any, user_id: UserId) -> Any: ...

    def execute(self, id: Any, data: Any, user_id: UserId) -> Any:
        load_owned(self._repo, id, user_id, self._label)
        return self._repo.save(self._build_entity(id, data, user_id))


class DeleteEntity:
    """Deletes user-owned entities. Accepts a single ID or a list of IDs."""

    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, ids: Any, user_id: UserId) -> None:
        if not isinstance(ids, list):
            ids = [ids]
        owned: list[Any] = []
        for id in ids:
            existing = self._repo.get_by_id(id)
            if existing is not None and existing.user_id == user_id:
                owned.append(id)
        if owned:
            self._repo.delete(owned)


class GetEntity:
    """Returns a user-owned entity or None if not found / not owned."""

    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, id: Any, user_id: UserId) -> Any:
        entity = self._repo.get_by_id(id)
        if entity is not None and entity.user_id != user_id:
            return None
        return entity


class ListEntities:
    """Lists all entities belonging to a user, optionally filtered by category."""

    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, user_id: UserId, category_id: Any = None) -> list[Any]:
        if category_id is not None:
            return self._repo.find_by_category_id(category_id, user_id)
        return self._repo.find_all(user_id)


class PaginatedListEntities:
    """Paginated listing of user-owned entities with optional search and category filter.

    When *page* is None the full unfiltered list is returned (for use in pickers/forms).
    When *page* is provided, returns one page of PAGE_SIZE items with search + category applied.
    """

    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        user_id: UserId,
        category_id: Any = None,
        page: int | None = None,
        search: str = "",
    ) -> Any:
        from backend.application.paginated_result import PAGE_SIZE, PaginatedResult

        if page is None:
            # Return all items without pagination (for ingredient pickers / sub-recipe pickers)
            if category_id is not None:
                all_items = self._repo.find_by_category_id(category_id, user_id)
            else:
                all_items = self._repo.find_all(user_id)
            n = len(all_items)
            return PaginatedResult(items=all_items, total=n, page=1, page_size=n)

        total = self._repo.count(user_id, search, category_id)
        offset = (page - 1) * PAGE_SIZE
        items = self._repo.find_page(user_id, search, PAGE_SIZE, offset, category_id)
        return PaginatedResult(items=items, total=total, page=page, page_size=PAGE_SIZE)
