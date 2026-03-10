from decimal import Decimal

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from backend.application.use_cases.manage_recipe import RecipeData
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId
from backend.presentation.models.recipe_table_model import RecipeTableModel
from backend.presentation.models.sortable_proxy_model import SortableProxyModel
from backend.presentation.units import to_code, to_display

_QWIDGETSIZE_MAX = 16777215


class _CollapsibleSection(QWidget):
    """Titled section widget that can be collapsed/expanded with a toggle button."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title

        self._toggle_btn = QPushButton(f"▼  {title}")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setStyleSheet(
            "QPushButton { text-align: left; font-weight: bold;"
            " background: #d0d8e8; border: none; padding: 4px 8px; }"
            "QPushButton:hover { background: #b8c8e0; }"
        )
        self._toggle_btn.clicked.connect(self._on_toggle)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 4, 0, 0)
        self._content_layout.setSpacing(4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toggle_btn)
        layout.addWidget(self._content, 1)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def _on_toggle(self, checked: bool) -> None:
        self._content.setVisible(not checked)
        arrow = "▶" if checked else "▼"
        self._toggle_btn.setText(f"{arrow}  {self._title}")
        if checked:
            self.setMaximumHeight(self._toggle_btn.sizeHint().height())
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        else:
            self.setMaximumHeight(_QWIDGETSIZE_MAX)
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
            )


class RecipeListView(QWidget):
    """Экран «Рецепты» (Screen 3): таблица рецептов + форма создания/редактирования."""

    create_recipe_requested = Signal(RecipeData)
    edit_recipe_requested = Signal(object, RecipeData)  # RecipeId, RecipeData
    delete_recipe_requested = Signal(object)  # RecipeId

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_recipe: Recipe | None = None
        self._products: list[Product] = []
        self._model = RecipeTableModel()
        self._proxy = SortableProxyModel()
        self._proxy.setSourceModel(self._model)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Поиск по названию...")
        self._search_edit.textChanged.connect(self._model.filter)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.selectionModel().currentRowChanged.connect(
            self._on_row_selected
        )

        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self._search_edit)
        table_layout.addWidget(self._table)

        table_panel = QWidget()
        table_panel.setLayout(table_layout)

        # --- Form (no scroll area — sections stretch to fill height) ---
        form_panel = QWidget()
        form_layout = QVBoxLayout(form_panel)

        self._name_edit = QLineEdit()
        self._category_combo = QComboBox()
        self._servings_spin = QSpinBox()
        self._servings_spin.setMinimum(1)
        self._servings_spin.setMaximum(100)
        self._servings_spin.setValue(4)

        self._weight_spin = QSpinBox()
        self._weight_spin.setMinimum(0)
        self._weight_spin.setMaximum(99999)
        self._weight_spin.setValue(0)
        self._weight_spin.setSuffix(" г")

        meta_form = QFormLayout()
        meta_form.addRow("Название:", self._name_edit)
        meta_form.addRow("Категория:", self._category_combo)
        meta_form.addRow("Порций:", self._servings_spin)
        meta_form.addRow("Вес:", self._weight_spin)
        form_layout.addLayout(meta_form)

        # --- Ingredients collapsible section ---
        ing_section = _CollapsibleSection("Ингредиенты")
        ing_layout = ing_section.content_layout

        self._ingredients_table = QTableWidget(0, 3)
        self._ingredients_table.setHorizontalHeaderLabels(["Продукт", "Кол-во", "Ед."])
        self._ingredients_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        ing_layout.addWidget(self._ingredients_table, 1)

        ing_btns = QHBoxLayout()
        self._add_ing_btn = QPushButton("+ Добавить")
        self._remove_ing_btn = QPushButton("− Удалить")
        self._add_ing_btn.clicked.connect(self._add_ingredient_row)
        self._remove_ing_btn.clicked.connect(self._remove_ingredient_row)
        ing_btns.addWidget(self._add_ing_btn)
        ing_btns.addWidget(self._remove_ing_btn)
        ing_layout.addLayout(ing_btns)

        form_layout.addWidget(ing_section, 1)

        # --- Cooking steps collapsible section ---
        steps_section = _CollapsibleSection("Шаги приготовления")
        steps_layout = steps_section.content_layout

        self._steps_list = QListWidget()
        steps_layout.addWidget(self._steps_list, 1)

        self._step_input = QLineEdit()
        self._step_input.setPlaceholderText("Описание шага...")
        steps_layout.addWidget(self._step_input)

        step_btns = QHBoxLayout()
        self._add_step_btn = QPushButton("+ Добавить шаг")
        self._remove_step_btn = QPushButton("− Удалить шаг")
        self._add_step_btn.clicked.connect(self._add_step)
        self._remove_step_btn.clicked.connect(self._remove_step)
        step_btns.addWidget(self._add_step_btn)
        step_btns.addWidget(self._remove_step_btn)
        steps_layout.addLayout(step_btns)

        form_layout.addWidget(steps_section, 1)

        # Action buttons
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

        # --- Main layout: 2/3 table + 1/3 form ---
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(table_panel, 2)
        main_layout.addWidget(form_panel, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_category_map(self, category_map: dict[int, str]) -> None:
        self._model.set_category_map(category_map)

    def set_recipes(self, recipes: list[Recipe]) -> None:
        self._model.set_recipes(recipes)

    def set_categories(self, categories: list[ActiveCategory]) -> None:
        current_id = self._category_combo.currentData()
        self._category_combo.clear()
        for cat_id, cat_name in categories:
            self._category_combo.addItem(cat_name, cat_id)
        if current_id is not None:
            for i in range(self._category_combo.count()):
                if self._category_combo.itemData(i) == current_id:
                    self._category_combo.setCurrentIndex(i)
                    break

    def set_products(self, products: list[Product]) -> None:
        self._products = products
        # Refresh product combos in ingredient table
        for row in range(self._ingredients_table.rowCount()):
            combo = self._ingredients_table.cellWidget(row, 0)
            if isinstance(combo, QComboBox):
                self._populate_product_combo(combo)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_row_selected(self, current: QModelIndex, _previous: QModelIndex) -> None:
        source_row = self._proxy.mapToSource(current).row()
        recipe = self._model.recipe_at(source_row)
        if recipe is None:
            return
        self._selected_recipe = recipe
        self._populate_form(recipe)

    def _on_save(self) -> None:
        data = self._collect_form_data()
        if data is None:
            return
        if self._selected_recipe is not None:
            self.edit_recipe_requested.emit(self._selected_recipe.id, data)
        else:
            self.create_recipe_requested.emit(data)

    def _on_delete(self) -> None:
        if self._selected_recipe is None:
            QMessageBox.information(self, "Удаление", "Выберите рецепт для удаления.")
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить рецепт «{self._selected_recipe.name}»?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_recipe_requested.emit(self._selected_recipe.id)
            self._selected_recipe = None
            self._clear_form()

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------

    def _populate_form(self, recipe: Recipe) -> None:
        self._name_edit.setText(recipe.name)
        for i in range(self._category_combo.count()):
            if self._category_combo.itemData(i) == recipe.category_id:
                self._category_combo.setCurrentIndex(i)
                break
        self._servings_spin.setValue(recipe.servings)
        self._weight_spin.setValue(recipe.weight)

        # Ingredients
        self._ingredients_table.setRowCount(0)
        for ing in recipe.ingredients:
            self._add_ingredient_row()
            row = self._ingredients_table.rowCount() - 1
            combo: QComboBox = self._ingredients_table.cellWidget(row, 0)  # type: ignore[assignment]
            for i in range(combo.count()):
                if combo.itemData(i) == ing.product_id:
                    combo.setCurrentIndex(i)  # triggers unit label update via signal
                    break
            spin: QDoubleSpinBox = self._ingredients_table.cellWidget(row, 1)  # type: ignore[assignment]
            spin.setValue(ing.quantity.amount)

        # Steps
        self._steps_list.clear()
        for step in sorted(recipe.steps, key=lambda s: s.order):
            self._steps_list.addItem(step.description)

    def _clear_form(self) -> None:
        self._selected_recipe = None
        self._name_edit.clear()
        self._category_combo.setCurrentIndex(0)
        self._servings_spin.setValue(4)
        self._weight_spin.setValue(0)
        self._ingredients_table.setRowCount(0)
        self._steps_list.clear()
        self._step_input.clear()

    def _collect_form_data(self) -> RecipeData | None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название рецепта.")
            return None
        category_id = self._category_combo.currentData()
        if category_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию рецепта.")
            return None
        servings = self._servings_spin.value()
        weight = self._weight_spin.value()

        ingredients: list[RecipeIngredient] = []
        for row in range(self._ingredients_table.rowCount()):
            combo: QComboBox = self._ingredients_table.cellWidget(row, 0)  # type: ignore[assignment]
            spin: QDoubleSpinBox = self._ingredients_table.cellWidget(row, 1)  # type: ignore[assignment]
            unit_label: QLabel = self._ingredients_table.cellWidget(row, 2)  # type: ignore[assignment]
            product_id = combo.currentData()
            if product_id is None:
                continue
            ingredients.append(
                RecipeIngredient(
                    product_id=ProductId(int(product_id)),
                    quantity=Quantity(spin.value(), to_code(unit_label.text())),
                )
            )

        steps: list[CookingStep] = []
        for i in range(self._steps_list.count()):
            item = self._steps_list.item(i)
            if item:
                steps.append(CookingStep(order=i + 1, description=item.text()))

        return RecipeData(
            name=name,
            category_id=RecipeCategoryId(category_id),
            servings=servings,
            ingredients=ingredients,
            steps=steps,
            weight=weight,
        )

    def _add_ingredient_row(self) -> None:
        row = self._ingredients_table.rowCount()
        self._ingredients_table.insertRow(row)

        product_combo = QComboBox()
        self._populate_product_combo(product_combo)
        self._ingredients_table.setCellWidget(row, 0, product_combo)

        amount_spin = QDoubleSpinBox()
        amount_spin.setMinimum(0.01)
        amount_spin.setMaximum(9999.0)
        amount_spin.setDecimals(2)
        amount_spin.setValue(100.0)
        self._ingredients_table.setCellWidget(row, 1, amount_spin)

        unit_label = QLabel()
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh_unit_label(product_combo, unit_label)
        product_combo.currentIndexChanged.connect(
            lambda _: self._refresh_unit_label(product_combo, unit_label)
        )
        self._ingredients_table.setCellWidget(row, 2, unit_label)

    def _remove_ingredient_row(self) -> None:
        row = self._ingredients_table.currentRow()
        if row >= 0:
            self._ingredients_table.removeRow(row)

    def _refresh_unit_label(self, combo: QComboBox, label: QLabel) -> None:
        product_id = combo.currentData()
        unit = next((p.recipe_unit for p in self._products if p.id == product_id), "")
        label.setText(to_display(unit))

    def _populate_product_combo(self, combo: QComboBox) -> None:
        current_id = combo.currentData()
        combo.clear()
        for product in self._products:
            combo.addItem(product.name, product.id)
        if current_id is not None:
            for i in range(combo.count()):
                if combo.itemData(i) == current_id:
                    combo.setCurrentIndex(i)
                    break

    def _add_step(self) -> None:
        text = self._step_input.text().strip()
        if text:
            self._steps_list.addItem(text)
            self._step_input.clear()

    def _remove_step(self) -> None:
        row = self._steps_list.currentRow()
        if row >= 0:
            self._steps_list.takeItem(row)
