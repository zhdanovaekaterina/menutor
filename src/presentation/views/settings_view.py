from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.application.use_cases.manage_family import FamilyMemberData
from src.domain.entities.family_member import FamilyMember
from src.domain.value_objects.category import Category
from src.domain.value_objects.types import FamilyMemberId


class _CategoryPanel(QWidget):
    """Универсальная панель управления категориями (продуктов или рецептов)."""

    create_requested = Signal(str)           # name
    edit_requested = Signal(int, str)        # category_id, name
    delete_requested = Signal(int)           # category_id

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
        self._clear_btn = QPushButton("Очистить")
        self._save_btn.clicked.connect(self._on_save)
        self._delete_btn.clicked.connect(self._on_delete)
        self._clear_btn.clicked.connect(self._clear_form)
        btns.addWidget(self._save_btn)
        btns.addWidget(self._delete_btn)
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
            cat_id, name, _active = self._categories[row]
            self._selected_id = cat_id
            self._name_edit.setText(name)

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
        selected_name = self._name_edit.text().strip()
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Скрыть категорию «{selected_name}»?\n"
            "Категория станет неактивной, но существующие записи сохранятся.",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self._selected_id)
            self._clear_form()

    def _clear_form(self) -> None:
        self._selected_id = None
        self._name_edit.clear()


class _FamilyPanel(QWidget):
    """Панель управления членами семьи."""

    create_member_requested = Signal(FamilyMemberData)
    edit_member_requested = Signal(object, FamilyMemberData)   # FamilyMemberId, data
    delete_member_requested = Signal(object)                    # FamilyMemberId

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_member: FamilyMember | None = None
        self._members: list[FamilyMember] = []

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["Имя", "Коэф. порции", "Ограничения", "Комментарий"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.selectionModel().currentRowChanged.connect(self._on_row_selected)

        # Form
        self._name_edit = QLineEdit()
        self._multiplier_spin = QDoubleSpinBox()
        self._multiplier_spin.setMinimum(0.1)
        self._multiplier_spin.setMaximum(5.0)
        self._multiplier_spin.setDecimals(1)
        self._multiplier_spin.setSingleStep(0.1)
        self._multiplier_spin.setValue(1.0)
        self._restrictions_edit = QLineEdit()
        self._comment_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("Имя:*", self._name_edit)
        form.addRow("Коэф. порции:", self._multiplier_spin)
        form.addRow("Ограничения:", self._restrictions_edit)
        form.addRow("Комментарий:", self._comment_edit)

        btns = QHBoxLayout()
        self._save_btn = QPushButton("Сохранить")
        self._delete_btn = QPushButton("Удалить")
        self._clear_btn = QPushButton("Очистить")
        self._save_btn.clicked.connect(self._on_save)
        self._delete_btn.clicked.connect(self._on_delete)
        self._clear_btn.clicked.connect(self._clear_form)
        btns.addWidget(self._save_btn)
        btns.addWidget(self._delete_btn)
        btns.addWidget(self._clear_btn)

        form_box = QGroupBox("Добавить / редактировать")
        form_layout = QVBoxLayout(form_box)
        form_layout.addLayout(form)
        form_layout.addLayout(btns)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        layout.addWidget(form_box)

    def set_members(self, members: list[FamilyMember]) -> None:
        self._members = members
        self._table.setRowCount(0)
        for m in members:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(m.name))
            self._table.setItem(row, 1, QTableWidgetItem(str(m.portion_multiplier)))
            self._table.setItem(row, 2, QTableWidgetItem(m.dietary_restrictions))
            self._table.setItem(row, 3, QTableWidgetItem(m.comment))

    def _on_row_selected(self, current, _previous) -> None:
        row = current.row()
        if 0 <= row < len(self._members):
            self._selected_member = self._members[row]
            m = self._selected_member
            self._name_edit.setText(m.name)
            self._multiplier_spin.setValue(m.portion_multiplier)
            self._restrictions_edit.setText(m.dietary_restrictions)
            self._comment_edit.setText(m.comment)

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя члена семьи.")
            return
        data = FamilyMemberData(
            name=name,
            portion_multiplier=self._multiplier_spin.value(),
            dietary_restrictions=self._restrictions_edit.text().strip(),
            comment=self._comment_edit.text().strip(),
        )
        if self._selected_member is not None:
            self.edit_member_requested.emit(self._selected_member.id, data)
        else:
            self.create_member_requested.emit(data)

    def _on_delete(self) -> None:
        if self._selected_member is None:
            QMessageBox.information(self, "Удаление", "Выберите члена семьи для удаления.")
            return
        reply = QMessageBox.question(
            self, "Подтверждение", f"Удалить «{self._selected_member.name}»?"
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_member_requested.emit(self._selected_member.id)
            self._selected_member = None
            self._clear_form()

    def _clear_form(self) -> None:
        self._selected_member = None
        self._name_edit.clear()
        self._multiplier_spin.setValue(1.0)
        self._restrictions_edit.clear()
        self._comment_edit.clear()


class _ImportExportPanel(QWidget):
    """Панель импорта/экспорта."""

    export_text_requested = Signal()
    export_csv_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Экспорт последнего сформированного списка покупок:"))

        export_text_btn = QPushButton("Экспорт в текст (для мессенджера)")
        export_csv_btn = QPushButton("Экспорт в CSV")
        export_text_btn.clicked.connect(self.export_text_requested)
        export_csv_btn.clicked.connect(self._on_export_csv)
        layout.addWidget(export_text_btn)
        layout.addWidget(export_csv_btn)
        layout.addStretch()

    def _on_export_csv(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить список покупок", "", "CSV файлы (*.csv)"
        )
        if filepath:
            self.export_csv_requested.emit(filepath)


class SettingsView(QWidget):
    """Экран «Настройки» (Screen 5)."""

    # Family member signals
    create_member_requested = Signal(FamilyMemberData)
    edit_member_requested = Signal(object, FamilyMemberData)
    delete_member_requested = Signal(object)

    # Export signals (from import/export panel)
    export_text_requested = Signal()
    export_csv_requested = Signal(str)

    # Product category signals
    create_product_category_requested = Signal(str)
    edit_product_category_requested = Signal(int, str)
    delete_product_category_requested = Signal(int)

    # Recipe category signals
    create_recipe_category_requested = Signal(str)
    edit_recipe_category_requested = Signal(int, str)
    delete_recipe_category_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Left secondary nav
        self._nav = QListWidget()
        self._nav.addItem("Члены семьи")
        self._nav.addItem("Категории продуктов")
        self._nav.addItem("Категории рецептов")
        self._nav.addItem("Импорт / Экспорт")
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        self._nav.setMaximumWidth(200)

        # Right: stacked content
        self._family_panel = _FamilyPanel()
        self._family_panel.create_member_requested.connect(self.create_member_requested)
        self._family_panel.edit_member_requested.connect(self.edit_member_requested)
        self._family_panel.delete_member_requested.connect(self.delete_member_requested)

        self._product_cat_panel = _CategoryPanel("Категории продуктов")
        self._product_cat_panel.create_requested.connect(
            self.create_product_category_requested
        )
        self._product_cat_panel.edit_requested.connect(
            self.edit_product_category_requested
        )
        self._product_cat_panel.delete_requested.connect(
            self.delete_product_category_requested
        )

        self._recipe_cat_panel = _CategoryPanel("Категории рецептов")
        self._recipe_cat_panel.create_requested.connect(
            self.create_recipe_category_requested
        )
        self._recipe_cat_panel.edit_requested.connect(
            self.edit_recipe_category_requested
        )
        self._recipe_cat_panel.delete_requested.connect(
            self.delete_recipe_category_requested
        )

        self._ie_panel = _ImportExportPanel()
        self._ie_panel.export_text_requested.connect(self.export_text_requested)
        self._ie_panel.export_csv_requested.connect(self.export_csv_requested)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._family_panel)
        self._stack.addWidget(self._product_cat_panel)
        self._stack.addWidget(self._recipe_cat_panel)
        self._stack.addWidget(self._ie_panel)

        layout = QHBoxLayout(self)
        layout.addWidget(self._nav)
        layout.addWidget(self._stack, 1)

        self._nav.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_family_members(self, members: list[FamilyMember]) -> None:
        self._family_panel.set_members(members)

    def set_product_categories(
        self, categories: list[Category],
    ) -> None:
        self._product_cat_panel.set_categories(categories)

    def set_recipe_categories(
        self, categories: list[Category],
    ) -> None:
        self._recipe_cat_panel.set_categories(categories)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_nav_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
