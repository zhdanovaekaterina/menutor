from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.domain.entities.shopping_list import ShoppingList


class ShoppingListView(QWidget):
    """Экран «Список покупок» (Screen 2)."""

    export_text_requested = Signal()
    export_csv_requested = Signal(str)  # filepath

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shopping_list: ShoppingList | None = None

        # --- Shopping list table ---
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["", "Категория", "Продукт", "Количество", "Сумма, руб."]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setColumnWidth(0, 30)  # checkbox column

        # --- Summary panel ---
        summary_box = QGroupBox("Итого")
        summary_layout = QVBoxLayout(summary_box)

        self._total_label = QLabel("0.00 руб.")
        self._total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._items_label = QLabel("Позиций: 0")
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("Куплено: %v%")

        summary_layout.addWidget(QLabel("Сумма корзины:"))
        summary_layout.addWidget(self._total_label)
        summary_layout.addWidget(self._items_label)
        summary_layout.addWidget(QLabel("Прогресс покупок:"))
        summary_layout.addWidget(self._progress_bar)
        summary_layout.addStretch()

        export_btn_text = QPushButton("Экспорт (текст)")
        export_btn_csv = QPushButton("Экспорт (CSV)")
        export_btn_text.clicked.connect(self._on_export_text)
        export_btn_csv.clicked.connect(self._on_export_csv)
        summary_layout.addWidget(export_btn_text)
        summary_layout.addWidget(export_btn_csv)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self._table, 2)
        main_layout.addWidget(summary_box, 1)

        self._table.itemChanged.connect(self._on_item_changed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_shopping_list(self, shopping_list: ShoppingList) -> None:
        self._shopping_list = shopping_list
        self._table.blockSignals(True)
        self._table.setRowCount(0)

        for category, items in shopping_list.items_by_category().items():
            for item in items:
                row = self._table.rowCount()
                self._table.insertRow(row)

                check_item = QTableWidgetItem()
                check_item.setCheckState(
                    Qt.CheckState.Checked if item.purchased else Qt.CheckState.Unchecked
                )
                self._table.setItem(row, 0, check_item)
                self._table.setItem(row, 1, QTableWidgetItem(category))
                self._table.setItem(row, 2, QTableWidgetItem(item.product_name))
                qty_text = f"{item.quantity.amount:.2f} {item.quantity.unit}"
                self._table.setItem(row, 3, QTableWidgetItem(qty_text))
                cost_text = f"{item.cost.amount:.2f}"
                self._table.setItem(row, 4, QTableWidgetItem(cost_text))

        self._table.blockSignals(False)
        self._update_summary()

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)

    def show_text_export(self, text: str) -> None:
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPlainTextEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("Список покупок (текст)")
        dialog.resize(500, 400)
        text_edit = QPlainTextEdit(text)
        text_edit.setReadOnly(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout = QVBoxLayout(dialog)
        layout.addWidget(text_edit)
        layout.addWidget(buttons)
        dialog.exec()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_export_text(self) -> None:
        if not self._shopping_list or not self._shopping_list.items:
            QMessageBox.information(self, "Экспорт", "Список покупок пуст.")
            return
        self.export_text_requested.emit()

    def _on_export_csv(self) -> None:
        if not self._shopping_list or not self._shopping_list.items:
            QMessageBox.information(self, "Экспорт", "Список покупок пуст.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить список покупок", "", "CSV файлы (*.csv)"
        )
        if filepath:
            self.export_csv_requested.emit(filepath)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        self._update_summary()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _update_summary(self) -> None:
        if self._shopping_list is None:
            return
        total = self._shopping_list.total_cost()
        total_items = self._table.rowCount()
        checked = sum(
            1
            for row in range(total_items)
            if self._table.item(row, 0)
            and self._table.item(row, 0).checkState() == Qt.CheckState.Checked
        )
        self._total_label.setText(f"{total.amount:.2f} руб.")
        self._items_label.setText(f"Позиций: {total_items}")
        pct = int(checked / total_items * 100) if total_items > 0 else 0
        self._progress_bar.setValue(pct)
