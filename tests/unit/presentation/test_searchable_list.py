"""Tests for SearchableList widget — item management, filtering, selection signals."""

from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from backend.presentation.widgets.searchable_list import SearchableList


class TestSearchableList:
    def test_initial_state_empty(self, qapp: QApplication) -> None:
        widget = SearchableList()
        assert widget._source_model.rowCount() == 0

    def test_set_items(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(1, "Альфа"), (2, "Бета"), (3, "Гамма")])
        assert widget._source_model.rowCount() == 3

    def test_set_items_replaces_previous(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(1, "A"), (2, "B")])
        widget.set_items([(3, "C")])
        assert widget._source_model.rowCount() == 1

    def test_items_store_id_in_user_role(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(42, "Элемент")])
        item = widget._source_model.item(0)
        assert item is not None
        assert item.data(Qt.ItemDataRole.UserRole) == 42

    def test_items_are_not_editable(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(1, "X")])
        item = widget._source_model.item(0)
        assert item is not None
        assert not item.isEditable()

    def test_filter_by_search_text(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(1, "Молоко"), (2, "Мука"), (3, "Сахар")])
        widget._search.setText("м")
        assert widget._proxy.rowCount() == 2

    def test_filter_case_insensitive(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(1, "Молоко")])
        widget._search.setText("молоко")
        assert widget._proxy.rowCount() == 1

    def test_clear_filter_shows_all(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(1, "A"), (2, "B")])
        widget._search.setText("a")
        widget._search.setText("")
        assert widget._proxy.rowCount() == 2

    def test_selection_emits_signal(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(7, "Элемент")])

        spy = MagicMock()
        widget.item_selected.connect(spy)

        proxy_idx = widget._proxy.index(0, 0)
        widget._list_view.setCurrentIndex(proxy_idx)

        spy.assert_called_once_with(7)

    def test_clear_selection(self, qapp: QApplication) -> None:
        widget = SearchableList()
        widget.set_items([(1, "A")])
        proxy_idx = widget._proxy.index(0, 0)
        widget._list_view.setCurrentIndex(proxy_idx)

        widget.clear_selection()
        assert not widget._list_view.selectionModel().hasSelection()

    def test_drag_enabled_flag(self, qapp: QApplication) -> None:
        widget = SearchableList(drag_enabled=True)
        assert widget._list_view.dragEnabled()

    def test_drag_disabled_by_default(self, qapp: QApplication) -> None:
        widget = SearchableList()
        assert not widget._list_view.dragEnabled()
