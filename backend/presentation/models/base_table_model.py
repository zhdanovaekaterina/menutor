"""Base class for CRUD table models — eliminates rowCount/filter/headerData boilerplate."""

from abc import abstractmethod
from typing import Generic, TypeVar

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

E = TypeVar("E")


class BaseCrudTableModel(QAbstractTableModel, Generic[E]):
    _columns: list[str]

    def __init__(self, items: list[E] | None = None) -> None:
        super().__init__()
        self._all_items: list[E] = items or []
        self._items: list[E] = list(self._all_items)
        self._category_map: dict[int, str] = {}

    @abstractmethod
    def _display_value(self, entity: E, column: int) -> str: ...

    @abstractmethod
    def _entity_id(self, entity: E) -> int: ...

    @abstractmethod
    def _entity_name(self, entity: E) -> str: ...

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._columns[section]
        return None

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        entity = self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_value(entity, index.column())
        if role == Qt.ItemDataRole.UserRole:
            return self._entity_id(entity)
        return None

    def set_category_map(self, category_map: dict[int, str]) -> None:
        self._category_map = category_map

    def set_items(self, items: list[E]) -> None:
        self.beginResetModel()
        self._all_items = list(items)
        self._items = list(items)
        self.endResetModel()

    def filter(self, query: str) -> None:
        q = query.strip().lower()
        self.beginResetModel()
        self._items = (
            self._all_items
            if not q
            else [e for e in self._all_items if q in self._entity_name(e).lower()]
        )
        self.endResetModel()

    def item_at(self, row: int) -> E | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None
