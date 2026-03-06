from decimal import Decimal

from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.application.use_cases.manage_product import ProductData
from src.domain.entities.product import Product
from src.domain.value_objects.money import Money
from src.domain.value_objects.types import ProductCategoryId, ProductId
from src.presentation.models.product_table_model import ProductTableModel
from src.presentation.units import UNIT_DISPLAY_OPTIONS, to_code, to_display


class ProductListView(QWidget):
    """Экран «Продукты» (Screen 4): таблица продуктов + форма создания/редактирования."""

    create_product_requested = Signal(ProductData)
    edit_product_requested = Signal(object, ProductData)  # ProductId, ProductData
    delete_product_requested = Signal(object)  # ProductId

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_product: Product | None = None

        self._model = ProductTableModel()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Поиск по названию...")
        self._search_edit.textChanged.connect(self._model.filter)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.selectionModel().currentRowChanged.connect(self._on_row_selected)

        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self._search_edit)
        table_layout.addWidget(self._table)

        table_panel = QWidget()
        table_panel.setLayout(table_layout)

        # --- Form ---
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_container = QWidget()
        form_scroll.setWidget(form_container)
        form_layout = QVBoxLayout(form_container)

        self._name_edit = QLineEdit()
        self._category_combo = QComboBox()
        self._brand_edit = QLineEdit()
        self._supplier_edit = QLineEdit()

        self._recipe_unit_combo = QComboBox()
        self._recipe_unit_combo.addItems(UNIT_DISPLAY_OPTIONS)
        self._recipe_unit_combo.setEditable(True)

        self._purchase_unit_combo = QComboBox()
        self._purchase_unit_combo.addItems(UNIT_DISPLAY_OPTIONS)
        self._purchase_unit_combo.setEditable(True)

        self._price_spin = QDoubleSpinBox()
        self._price_spin.setMinimum(0.0)
        self._price_spin.setMaximum(999999.0)
        self._price_spin.setDecimals(2)
        self._price_spin.setSuffix(" руб.")

        self._conversion_spin = QDoubleSpinBox()
        self._conversion_spin.setMinimum(0.001)
        self._conversion_spin.setMaximum(99999.0)
        self._conversion_spin.setDecimals(3)
        self._conversion_spin.setValue(1.0)

        self._weight_spin = QDoubleSpinBox()
        self._weight_spin.setMinimum(0.0)
        self._weight_spin.setMaximum(99999.0)
        self._weight_spin.setDecimals(1)
        self._weight_spin.setSpecialValueText("—")  # 0 = not set

        self._weight_check = QCheckBox("Вес одной штуки (г)")
        self._weight_check.stateChanged.connect(
            lambda state: self._weight_spin.setEnabled(bool(state))
        )
        self._weight_spin.setEnabled(False)

        form = QFormLayout()
        form.addRow("Название:*", self._name_edit)
        form.addRow("Категория:", self._category_combo)
        form.addRow("Бренд:", self._brand_edit)
        form.addRow("Поставщик:", self._supplier_edit)
        form.addRow("Ед. в рецепте:", self._recipe_unit_combo)
        form.addRow("Ед. покупки:", self._purchase_unit_combo)
        form.addRow("Цена:", self._price_spin)
        form.addRow("Коэф. конвертации:", self._conversion_spin)
        form.addRow(self._weight_check, self._weight_spin)
        form_layout.addLayout(form)

        action_btns = QHBoxLayout()
        self._save_btn = QPushButton("Сохранить")
        self._delete_btn = QPushButton("Удалить")
        self._clear_btn = QPushButton("Очистить")
        self._save_btn.clicked.connect(self._on_save)
        self._delete_btn.clicked.connect(self._on_delete)
        self._clear_btn.clicked.connect(self._clear_form)
        action_btns.addWidget(self._save_btn)
        action_btns.addWidget(self._delete_btn)
        action_btns.addWidget(self._clear_btn)
        form_layout.addLayout(action_btns)
        form_layout.addStretch()

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(table_panel, 2)
        main_layout.addWidget(form_scroll, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_products(self, products: list[Product]) -> None:
        self._model.set_products(products)

    def set_categories(self, categories: list[tuple[int, str]]) -> None:
        current_id = self._category_combo.currentData()
        self._category_combo.clear()
        for cat_id, cat_name in categories:
            self._category_combo.addItem(cat_name, cat_id)
        if current_id is not None:
            for i in range(self._category_combo.count()):
                if self._category_combo.itemData(i) == current_id:
                    self._category_combo.setCurrentIndex(i)
                    break

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_row_selected(self, current: QModelIndex, _previous: QModelIndex) -> None:
        product = self._model.product_at(current.row())
        if product is None:
            return
        self._selected_product = product
        self._populate_form(product)

    def _on_save(self) -> None:
        data = self._collect_form_data()
        if data is None:
            return
        if self._selected_product is not None:
            self.edit_product_requested.emit(self._selected_product.id, data)
        else:
            self.create_product_requested.emit(data)

    def _on_delete(self) -> None:
        if self._selected_product is None:
            QMessageBox.information(self, "Удаление", "Выберите продукт для удаления.")
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить продукт «{self._selected_product.name}»?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_product_requested.emit(self._selected_product.id)
            self._selected_product = None
            self._clear_form()

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------

    def _populate_form(self, product: Product) -> None:
        self._name_edit.setText(product.name)
        for i in range(self._category_combo.count()):
            if self._category_combo.itemData(i) == product.category_id:
                self._category_combo.setCurrentIndex(i)
                break
        self._brand_edit.setText(product.brand)
        self._supplier_edit.setText(product.supplier)

        recipe_unit_display = to_display(product.recipe_unit)
        idx = self._recipe_unit_combo.findText(recipe_unit_display)
        self._recipe_unit_combo.setCurrentIndex(idx if idx >= 0 else 0)
        if idx < 0:
            self._recipe_unit_combo.setCurrentText(recipe_unit_display)

        purchase_unit_display = to_display(product.purchase_unit)
        idx = self._purchase_unit_combo.findText(purchase_unit_display)
        self._purchase_unit_combo.setCurrentIndex(idx if idx >= 0 else 0)
        if idx < 0:
            self._purchase_unit_combo.setCurrentText(purchase_unit_display)

        self._price_spin.setValue(float(product.price_per_purchase_unit.amount))
        self._conversion_spin.setValue(product.conversion_factor)

        if product.weight_per_piece_g is not None:
            self._weight_check.setChecked(True)
            self._weight_spin.setValue(product.weight_per_piece_g)
        else:
            self._weight_check.setChecked(False)
            self._weight_spin.setValue(0.0)

    def _clear_form(self) -> None:
        self._selected_product = None
        self._name_edit.clear()
        self._category_combo.setCurrentIndex(0)
        self._brand_edit.clear()
        self._supplier_edit.clear()
        self._recipe_unit_combo.setCurrentIndex(0)
        self._purchase_unit_combo.setCurrentIndex(0)
        self._price_spin.setValue(0.0)
        self._conversion_spin.setValue(1.0)
        self._weight_check.setChecked(False)
        self._weight_spin.setValue(0.0)

    def _collect_form_data(self) -> ProductData | None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название продукта.")
            return None
        category_id = self._category_combo.currentData()
        if category_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию продукта.")
            return None
        brand = self._brand_edit.text().strip()
        supplier = self._supplier_edit.text().strip()
        recipe_unit = to_code(self._recipe_unit_combo.currentText().strip()) or "g"
        purchase_unit = to_code(self._purchase_unit_combo.currentText().strip()) or "g"
        price = Money(Decimal(str(self._price_spin.value())))
        conversion_factor = self._conversion_spin.value()
        weight = (
            self._weight_spin.value()
            if self._weight_check.isChecked() and self._weight_spin.value() > 0
            else None
        )

        return ProductData(
            name=name,
            category_id=ProductCategoryId(category_id),
            brand=brand,
            supplier=supplier,
            recipe_unit=recipe_unit,
            purchase_unit=purchase_unit,
            price=price,
            conversion_factor=conversion_factor,
            weight_per_piece_g=weight,
        )
