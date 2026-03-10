from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSortFilterProxyModel, Qt


class SortableProxyModel(QSortFilterProxyModel):
    """Proxy model that sorts numeric columns by value, text columns alphabetically."""

    def lessThan(
        self,
        left: QModelIndex | QPersistentModelIndex,
        right: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        left_data = self.sourceModel().data(left, Qt.ItemDataRole.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.ItemDataRole.DisplayRole)
        try:
            return float(left_data) < float(right_data)
        except (ValueError, TypeError):
            return str(left_data or "") < str(right_data or "")
