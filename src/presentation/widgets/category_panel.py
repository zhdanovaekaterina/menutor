"""Reusable category management panel (for both product and recipe categories)."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.domain.value_objects.category import Category


class CategoryPanel(QWidget):
    """Универсальная панель управления категориями (продуктов или рецептов)."""

    create_requested = Signal(str)
    edit_requested = Signal(int, str)
    delete_requested = Signal(int)
    activate_requested = Signal(int)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_id: int | None = None
        self._categories: list[Category] = []

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Название", "Статус"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.selectionModel().currentRowChanged.connect(self._on_row_selected)

        self._name_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("Название:*", self._name_edit)

        btns = QHBoxLayout()
        self._save_btn = QPushButton("Сохранить")
        self._delete_btn = QPushButton("Удалить")
        self._activate_btn = QPushButton("Активировать")
        self._clear_btn = QPushButton("Очистить")
        self._save_btn.clicked.connect(self._on_save)
        self._delete_btn.clicked.connect(self._on_delete)
        self._activate_btn.clicked.connect(self._on_activate)
        self._clear_btn.clicked.connect(self._clear_form)
        self._activate_btn.setVisible(False)
        btns.addWidget(self._save_btn)
        btns.addWidget(self._delete_btn)
        btns.addWidget(self._activate_btn)
        btns.addWidget(self._clear_btn)

        form_box = QGroupBox("Добавить / редактировать")
        form_layout = QVBoxLayout(form_box)
        form_layout.addLayout(form)
        form_layout.addLayout(btns)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(title))
        layout.addWidget(self._table)
        layout.addWidget(form_box)

    def set_categories(self, categories: list[Category]) -> None:
        self._categories = categories
        self._table.setRowCount(0)
        for cat_id, name, active in categories:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(name))
            self._table.setItem(
                row, 1, QTableWidgetItem("Активна" if active else "Скрыта")
            )

    def _on_row_selected(self, current, _previous) -> None:  # type: ignore[no-untyped-def]
        row = current.row()
        if 0 <= row < len(self._categories):
            cat_id, name, active = self._categories[row]
            self._selected_id = cat_id
            self._name_edit.setText(name)
            self._activate_btn.setVisible(not active)

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название категории.")
            return
        if self._selected_id is not None:
            self.edit_requested.emit(self._selected_id, name)
        else:
            self.create_requested.emit(name)

    def _on_delete(self) -> None:
        if self._selected_id is None:
            QMessageBox.information(self, "Удаление", "Выберите категорию для удаления.")
            return
        self.delete_requested.emit(self._selected_id)
        self._clear_form()

    def _on_activate(self) -> None:
        if self._selected_id is None:
            return
        self.activate_requested.emit(self._selected_id)
        self._clear_form()

    def _clear_form(self) -> None:
        self._selected_id = None
        self._name_edit.clear()
        self._activate_btn.setVisible(False)
