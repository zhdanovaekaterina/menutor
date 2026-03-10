from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.domain.entities.family_member import FamilyMember
from src.domain.entities.menu import WeeklyMenu
from src.domain.entities.product import Product
from src.domain.entities.recipe import Recipe
from src.presentation.widgets.drag_drop_grid import DragDropGrid
from src.presentation.widgets.searchable_list import SearchableList


class MenuPlannerView(QWidget):
    """Экран «Планировщик» (Screen 1)."""

    menu_selected = Signal(object)           # MenuId
    # day, meal_type, item_type, item_id, servings_or_qty, unit
    slot_updated = Signal(int, str, str, int, float, str)
    save_menu_requested = Signal(str)        # menu name
    clear_menu_requested = Signal()
    generate_shopping_list_requested = Signal()
    delete_menu_requested = Signal(object)   # MenuId
    new_menu_requested = Signal(str)         # menu name

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # --- Left: saved menus list ---
        self._menus_list = SearchableList()
        self._menus_list.item_selected.connect(self.menu_selected)

        new_menu_btn = QPushButton("+ Новое меню")
        new_menu_btn.clicked.connect(self._on_new_menu)
        del_menu_btn = QPushButton("Удалить меню")
        del_menu_btn.clicked.connect(self._on_delete_menu)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Сохранённые меню"))
        left_layout.addWidget(self._menus_list)
        left_layout.addWidget(new_menu_btn)
        left_layout.addWidget(del_menu_btn)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(180)

        # --- Center: drag-drop grid ---
        self._grid = DragDropGrid()
        self._grid.slot_changed.connect(self.slot_updated)

        # --- Right top: family info ---
        self._family_label = QLabel("Члены семьи:\n—")
        self._family_label.setWordWrap(True)

        family_box = QGroupBox("Семья")
        family_box_layout = QVBoxLayout(family_box)
        family_box_layout.addWidget(self._family_label)

        # --- Right bottom: Dishes / Ingredients tabs ---
        self._recipe_source = SearchableList(
            drag_enabled=True, mime_type="application/x-menutor-recipe-id"
        )
        self._product_source = SearchableList(
            drag_enabled=True, mime_type="application/x-menutor-product-id"
        )

        source_tabs = QTabWidget()
        source_tabs.addTab(self._recipe_source, "Блюда")
        source_tabs.addTab(self._product_source, "Ингредиенты")

        right_layout = QVBoxLayout()
        right_layout.addWidget(family_box)
        right_layout.addWidget(source_tabs, 1)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)
        right_panel.setMaximumWidth(200)

        # --- Bottom action bar ---
        self._save_btn = QPushButton("Сохранить меню")
        self._clear_btn = QPushButton("Очистить")
        self._generate_btn = QPushButton("Сформировать список покупок")
        self._save_btn.clicked.connect(self._on_save)
        self._clear_btn.clicked.connect(self.clear_menu_requested)
        self._generate_btn.clicked.connect(self.generate_shopping_list_requested)

        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(self._save_btn)
        bottom_bar.addWidget(self._clear_btn)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self._generate_btn)

        # --- Assemble ---
        center_layout = QVBoxLayout()
        center_layout.addWidget(self._grid, 1)
        center_layout.addLayout(bottom_bar)

        center_panel = QWidget()
        center_panel.setLayout(center_layout)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel, 4)
        main_layout.addWidget(right_panel)

        self._current_menu_id: object = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_menus(self, menus: list[WeeklyMenu]) -> None:
        self._menus_list.set_items([(m.id, m.name) for m in menus])

    def set_current_menu(self, menu: WeeklyMenu | None) -> None:
        self._current_menu_id = menu.id if menu else None
        self._grid.clear_all()
        if menu is None:
            return
        # Grid requires item names — those must be injected via add_grid_slot_item
        # The controller will call add_grid_slot_item per slot after loading.

    def add_grid_slot_item(
        self,
        day: int,
        meal_type: str,
        item_type: str,
        item_id: int,
        name: str,
        servings: float = 1.0,
        quantity: float = 0.0,
        unit: str = "",
    ) -> None:
        self._grid.add_slot_item(day, meal_type, item_type, item_id, name, servings, quantity, unit)

    def clear_grid_slot_item(self, day: int, meal_type: str, item_type: str, item_id: int) -> None:
        self._grid.clear_slot_item(day, meal_type, item_type, item_id)

    def update_item_name(self, item_type: str, item_id: int, new_name: str) -> None:
        self._grid.update_item_name(item_type, item_id, new_name)

    def set_recipes(self, recipes: list[Recipe]) -> None:
        self._recipe_source.set_items([(r.id, r.name) for r in recipes])

    def set_products(self, products: list[Product]) -> None:
        self._product_source.set_items([(p.id, p.name) for p in products])
        self._grid.set_product_units({p.id: p.recipe_unit for p in products})

    def set_family_members(self, members: list[FamilyMember]) -> None:
        if not members:
            self._family_label.setText("Члены семьи:\n—")
            return
        total = sum(m.portion_multiplier for m in members)
        self._grid.set_default_recipe_servings(total)
        lines = "\n".join(
            f"• {m.name} (×{m.portion_multiplier:.1f})" for m in members
        )
        self._family_label.setText(f"Члены семьи:\n{lines}")

    def get_current_menu_id(self) -> object:
        return self._current_menu_id

    def get_grid_slots(self) -> list[dict]:
        return self._grid.get_slots()

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Ошибка", message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, "Информация", message)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_save(self) -> None:
        if self._current_menu_id is None:
            name, ok = QInputDialog.getText(self, "Сохранить меню", "Название меню:")
            if ok and name.strip():
                self.save_menu_requested.emit(name.strip())
        else:
            self.save_menu_requested.emit("")

    def _on_new_menu(self) -> None:
        name, ok = QInputDialog.getText(self, "Новое меню", "Название нового меню:")
        if ok and name.strip():
            self.new_menu_requested.emit(name.strip())

    def _on_delete_menu(self) -> None:
        if self._current_menu_id is None:
            QMessageBox.information(self, "Удаление", "Выберите меню для удаления.")
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранное меню?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_menu_requested.emit(self._current_menu_id)
            self._current_menu_id = None
            self._grid.clear_all()
