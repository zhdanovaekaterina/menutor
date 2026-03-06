from PySide6.QtCore import QMimeData, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QDrag, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QLineEdit, QListView, QVBoxLayout, QWidget


class _DraggableListView(QListView):
    """QListView с поддержкой drag для элементов с настраиваемым MIME типом."""

    def __init__(
        self,
        source_model: QStandardItemModel,
        proxy_model: QSortFilterProxyModel,
        mime_type: str = "application/x-menutor-recipe-id",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._source = source_model
        self._proxy = proxy_model
        self._mime_type = mime_type
        self.setModel(proxy_model)

    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        idx = self.currentIndex()
        if not idx.isValid():
            return
        source_idx = self._proxy.mapToSource(idx)
        item = self._source.itemFromIndex(source_idx)
        if item is None:
            return
        item_id = item.data(Qt.ItemDataRole.UserRole)
        display = item.text()

        mime = QMimeData()
        mime.setData(
            self._mime_type, str(item_id).encode()
        )
        mime.setText(display)

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class SearchableList(QWidget):
    """QWidget с полем поиска и фильтруемым списком элементов."""

    item_selected = Signal(object)  # передаёт id выбранного элемента

    def __init__(
        self,
        drag_enabled: bool = False,
        mime_type: str = "application/x-menutor-recipe-id",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._source_model = QStandardItemModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._source_model)
        self._proxy.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )
        self._proxy.setFilterKeyColumn(0)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Поиск...")

        if drag_enabled:
            self._list_view: QListView = _DraggableListView(
                self._source_model, self._proxy, mime_type=mime_type
            )
            self._list_view.setDragEnabled(True)
        else:
            self._list_view = QListView()
            self._list_view.setModel(self._proxy)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._search)
        layout.addWidget(self._list_view)

        self._search.textChanged.connect(self._proxy.setFilterFixedString)
        self._list_view.selectionModel().currentChanged.connect(
            self._on_selection_changed
        )

    def set_items(self, items: list[tuple[object, str]]) -> None:
        """Задаёт содержимое списка. items: [(id, display_name), ...]"""
        self._source_model.clear()
        for item_id, name in items:
            row = QStandardItem(name)
            row.setData(item_id, Qt.ItemDataRole.UserRole)
            row.setEditable(False)
            self._source_model.appendRow(row)

    def clear_selection(self) -> None:
        self._list_view.clearSelection()

    def _on_selection_changed(self, current, _previous) -> None:
        if current.isValid():
            source_idx = self._proxy.mapToSource(current)
            item = self._source_model.itemFromIndex(source_idx)
            if item is not None:
                self.item_selected.emit(item.data(Qt.ItemDataRole.UserRole))
