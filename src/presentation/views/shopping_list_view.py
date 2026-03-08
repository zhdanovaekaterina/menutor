from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.domain.entities.product import Product
from src.domain.entities.shopping_list import ShoppingList
from src.presentation.units import to_display


class ShoppingListView(QWidget):
    """Экран «Список покупок» (Screen 2)."""

    export_text_requested = Signal()
    export_csv_requested = Signal(str)  # filepath
    add_product_requested = Signal(int, float)  # product_id, quantity (in recipe_unit)
    quantity_edited = Signal(int, float)  # product_id, new purchase quantity
    remove_product_requested = Signal(int)  # product_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shopping_list: ShoppingList | None = None

        # --- Shopping list table ---
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["", "Продукт", "Количество", "Сумма, руб."]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
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

        self._remove_btn = QPushButton("Удалить из списка")
        self._remove_btn.clicked.connect(self._on_remove_product)
        summary_layout.addWidget(self._remove_btn)

        export_btn_text = QPushButton("Экспорт (текст)")
        export_btn_csv = QPushButton("Экспорт (CSV)")
        export_btn_text.clicked.connect(self._on_export_text)
        export_btn_csv.clicked.connect(self._on_export_csv)
        summary_layout.addWidget(export_btn_text)
        summary_layout.addWidget(export_btn_csv)

        # --- Add product panel ---
        add_box = QGroupBox("Добавить продукт")
        add_layout = QVBoxLayout(add_box)

        self._add_product_combo = QComboBox()
        add_layout.addWidget(self._add_product_combo)

        qty_row = QHBoxLayout()
        self._add_qty_spin = QDoubleSpinBox()
        self._add_qty_spin.setMinimum(0.01)
        self._add_qty_spin.setMaximum(99999.0)
        self._add_qty_spin.setDecimals(2)
        self._add_qty_spin.setValue(1.0)
        self._add_unit_label = QLabel()
        qty_row.addWidget(self._add_qty_spin, 1)
        qty_row.addWidget(self._add_unit_label)
        add_layout.addLayout(qty_row)

        self._add_product_combo.currentIndexChanged.connect(self._on_add_combo_changed)

        add_btn = QPushButton("Добавить в список")
        add_btn.clicked.connect(self._on_add_product)
        add_layout.addWidget(add_btn)

        summary_layout.addWidget(add_box)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self._table, 2)
        main_layout.addWidget(summary_box, 1)

        self._table.itemChanged.connect(self._on_item_changed)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_products(self, products: list[Product]) -> None:
        self._products = products
        current_id = self._add_product_combo.currentData()
        self._add_product_combo.clear()
        for p in products:
            self._add_product_combo.addItem(p.name, p.id)
        if current_id is not None:
            for i in range(self._add_product_combo.count()):
                if self._add_product_combo.itemData(i) == current_id:
                    self._add_product_combo.setCurrentIndex(i)
                    break

    def set_shopping_list(self, shopping_list: ShoppingList) -> None:
        self._shopping_list = shopping_list
        self._table.blockSignals(True)
        self._table.setRowCount(0)

        for category, items in shopping_list.items_by_category().items():
            # --- Category header row ---
            header_row = self._table.rowCount()
            self._table.insertRow(header_row)
            self._table.setSpan(header_row, 0, 1, 4)
            header_item = QTableWidgetItem(f"  {category}")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)
            header_font = QFont()
            header_font.setBold(True)
            header_item.setFont(header_font)
            header_item.setBackground(QBrush(QColor("#d0d8e8")))
            header_item.setForeground(QBrush(QColor("#1a2a4a")))
            self._table.setItem(header_row, 0, header_item)

            for item in items:
                row = self._table.rowCount()
                self._table.insertRow(row)

                check_item = QTableWidgetItem()
                check_item.setCheckState(
                    Qt.CheckState.Checked if item.purchased else Qt.CheckState.Unchecked
                )
                self._table.setItem(row, 0, check_item)
                name_item = QTableWidgetItem(item.product_name)
                name_item.setData(Qt.ItemDataRole.UserRole, int(item.product_id))
                self._table.setItem(row, 1, name_item)
                qty_text = f"{item.quantity.amount:.2f} {to_display(item.quantity.unit)}"
                self._table.setItem(row, 2, QTableWidgetItem(qty_text))
                cost_text = f"{item.cost.amount:.2f}"
                self._table.setItem(row, 3, QTableWidgetItem(cost_text))

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

    def _on_add_combo_changed(self) -> None:
        product_id = self._add_product_combo.currentData()
        unit = ""
        if hasattr(self, "_products"):
            unit = next(
                (p.recipe_unit for p in self._products if p.id == product_id), ""
            )
        self._add_unit_label.setText(to_display(unit))

    def _on_add_product(self) -> None:
        if self._shopping_list is None:
            QMessageBox.information(self, "Добавление", "Сначала сформируйте список покупок.")
            return
        product_id = self._add_product_combo.currentData()
        if product_id is None:
            return
        # Check for duplicate
        for existing in self._shopping_list.items:
            if existing.product_id == product_id:
                name = self._add_product_combo.currentText()
                QMessageBox.information(
                    self, "Продукт уже в списке",
                    f"«{name}» уже есть в списке покупок, отредактируйте количество.",
                )
                return
        qty = self._add_qty_spin.value()
        self.add_product_requested.emit(int(product_id), qty)

    def _on_remove_product(self) -> None:
        if self._shopping_list is None:
            QMessageBox.information(self, "Удаление", "Список покупок пуст.")
            return
        product_id = self._selected_product_id()
        if product_id is None:
            QMessageBox.information(self, "Удаление", "Выберите продукт для удаления.")
            return
        name_item = self._table.item(self._table.currentRow(), 1)
        name = name_item.text() if name_item else ""
        reply = QMessageBox.question(
            self, "Подтверждение", f"Удалить «{name}» из списка покупок?"
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_product_requested.emit(product_id)

    def _on_cell_double_clicked(self, row: int, column: int) -> None:
        if column != 2 or self._shopping_list is None:
            return
        name_item = self._table.item(row, 1)
        if name_item is None:
            return
        product_id = name_item.data(Qt.ItemDataRole.UserRole)
        if product_id is None:
            return
        product_name = name_item.text()
        # Find current item to get unit and amount
        item = next(
            (i for i in self._shopping_list.items if int(i.product_id) == product_id),
            None,
        )
        if item is None:
            return
        new_qty, ok = QInputDialog.getDouble(
            self,
            "Изменить количество",
            f"Количество для «{product_name}» ({to_display(item.quantity.unit)}):",
            item.quantity.amount,
            0.01,
            99999.0,
            2,
        )
        if ok and new_qty != item.quantity.amount:
            self.quantity_edited.emit(product_id, new_qty)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        if not (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return
        self._update_summary()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _selected_product_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        name_item = self._table.item(row, 1)
        if name_item is None:
            return None
        return name_item.data(Qt.ItemDataRole.UserRole)

    def _update_summary(self) -> None:
        if self._shopping_list is None:
            return
        total = self._shopping_list.total_cost()
        data_items: list[QTableWidgetItem] = []
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item is not None and (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
                data_items.append(item)
        total_items = len(data_items)
        checked = sum(
            1 for it in data_items if it.checkState() == Qt.CheckState.Checked
        )
        self._total_label.setText(f"{total.amount:.2f} руб.")
        self._items_label.setText(f"Позиций: {total_items}")
        pct = int(checked / total_items * 100) if total_items > 0 else 0
        self._progress_bar.setValue(pct)
