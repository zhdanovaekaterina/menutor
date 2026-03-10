"""Tests for CategoryPanel widget — set_categories, form population, signal emission."""

from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from backend.domain.value_objects.category import Category
from backend.presentation.widgets.category_panel import CategoryPanel


def _categories() -> list[Category]:
    return [
        Category(1, "Бакалея", True),
        Category(2, "Молочные", True),
        Category(3, "Архив", False),
    ]


class TestCategoryPanelSetCategories:
    def test_sets_table_rows(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        assert panel._table.rowCount() == 3

    def test_displays_names(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        assert panel._table.item(0, 0).text() == "Бакалея"
        assert panel._table.item(1, 0).text() == "Молочные"

    def test_displays_active_status(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        assert panel._table.item(0, 1).text() == "Активна"
        assert panel._table.item(2, 1).text() == "Скрыта"

    def test_replaces_previous_data(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel.set_categories([Category(1, "Единственная", True)])
        assert panel._table.rowCount() == 1


class TestCategoryPanelRowSelection:
    def test_selecting_row_populates_form(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel._table.setCurrentCell(1, 0)
        assert panel._name_edit.text() == "Молочные"
        assert panel._selected_id == 2

    def test_selecting_row_updates_selected_id(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel._table.setCurrentCell(0, 0)
        assert panel._selected_id == 1
        panel._table.setCurrentCell(2, 0)
        assert panel._selected_id == 3


class TestCategoryPanelSave:
    def test_save_new_emits_create_requested(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        spy = MagicMock()
        panel.create_requested.connect(spy)

        panel._name_edit.setText("Новая категория")
        panel._on_save()

        spy.assert_called_once_with("Новая категория")

    def test_save_existing_emits_edit_requested(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        spy = MagicMock()
        panel.edit_requested.connect(spy)

        panel._table.setCurrentCell(0, 0)
        panel._name_edit.setText("Бакалея обновлённая")
        panel._on_save()

        spy.assert_called_once_with(1, "Бакалея обновлённая")

    @patch("backend.presentation.widgets.category_panel.QMessageBox.warning")
    def test_save_empty_name_does_not_emit(
        self, mock_warning: MagicMock, qapp: QApplication,
    ) -> None:
        panel = CategoryPanel("Тест")
        spy = MagicMock()
        panel.create_requested.connect(spy)

        panel._name_edit.setText("")
        panel._on_save()

        spy.assert_not_called()
        mock_warning.assert_called_once()

    @patch("backend.presentation.widgets.category_panel.QMessageBox.warning")
    def test_save_whitespace_name_does_not_emit(
        self, mock_warning: MagicMock, qapp: QApplication,
    ) -> None:
        panel = CategoryPanel("Тест")
        spy = MagicMock()
        panel.create_requested.connect(spy)

        panel._name_edit.setText("   ")
        panel._on_save()

        spy.assert_not_called()
        mock_warning.assert_called_once()


class TestCategoryPanelActivateButton:
    def test_activate_hidden_for_active_category(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel._table.setCurrentCell(0, 0)  # "Бакалея", active
        assert panel._activate_btn.isHidden()

    def test_activate_shown_for_hidden_category(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel._table.setCurrentCell(2, 0)  # "Архив", inactive
        assert not panel._activate_btn.isHidden()

    def test_activate_emits_signal(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel._table.setCurrentCell(2, 0)
        spy = MagicMock()
        panel.activate_requested.connect(spy)

        panel._on_activate()

        spy.assert_called_once_with(3)

    def test_activate_clears_form(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel._table.setCurrentCell(2, 0)

        panel._on_activate()

        assert panel._selected_id is None
        assert panel._activate_btn.isHidden()


class TestCategoryPanelClear:
    def test_clear_resets_form(self, qapp: QApplication) -> None:
        panel = CategoryPanel("Тест")
        panel.set_categories(_categories())
        panel._table.setCurrentCell(0, 0)

        panel._clear_form()

        assert panel._name_edit.text() == ""
        assert panel._selected_id is None
        assert panel._activate_btn.isHidden()
