from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from backend.application.use_cases.manage_family import FamilyMemberData
from backend.domain.entities.family_member import FamilyMember
from backend.domain.value_objects.category import Category
from backend.presentation.widgets.about_panel import AboutPanel
from backend.presentation.widgets.category_panel import CategoryPanel
from backend.presentation.widgets.family_panel import FamilyPanel


class SettingsView(QWidget):
    """Экран «Настройки» (Screen 5)."""

    # Family member signals
    create_member_requested = Signal(FamilyMemberData)
    edit_member_requested = Signal(object, FamilyMemberData)
    delete_member_requested = Signal(object)

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
        self._nav.addItem("О программе")
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        self._nav.setMaximumWidth(200)

        # Right: stacked content — public so the controller can wire signals directly
        self.family_panel = FamilyPanel()
        self.family_panel.create_member_requested.connect(self.create_member_requested)
        self.family_panel.edit_member_requested.connect(self.edit_member_requested)
        self.family_panel.delete_member_requested.connect(self.delete_member_requested)

        self.product_cat_panel = CategoryPanel("Категории продуктов")
        self.product_cat_panel.create_requested.connect(
            self.create_product_category_requested
        )
        self.product_cat_panel.edit_requested.connect(
            self.edit_product_category_requested
        )
        self.product_cat_panel.delete_requested.connect(
            self.delete_product_category_requested
        )

        self.recipe_cat_panel = CategoryPanel("Категории рецептов")
        self.recipe_cat_panel.create_requested.connect(
            self.create_recipe_category_requested
        )
        self.recipe_cat_panel.edit_requested.connect(
            self.edit_recipe_category_requested
        )
        self.recipe_cat_panel.delete_requested.connect(
            self.delete_recipe_category_requested
        )

        self.about_panel = AboutPanel()

        self._stack = QStackedWidget()
        self._stack.addWidget(self.family_panel)
        self._stack.addWidget(self.product_cat_panel)
        self._stack.addWidget(self.recipe_cat_panel)
        self._stack.addWidget(self.about_panel)

        layout = QHBoxLayout(self)
        layout.addWidget(self._nav)
        layout.addWidget(self._stack, 1)

        self._nav.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_family_members(self, members: list[FamilyMember]) -> None:
        self.family_panel.set_members(members)

    def set_product_categories(self, categories: list[Category]) -> None:
        self.product_cat_panel.set_categories(categories)

    def set_recipe_categories(self, categories: list[Category]) -> None:
        self.recipe_cat_panel.set_categories(categories)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_nav_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
