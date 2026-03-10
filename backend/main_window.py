from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow, QTabWidget

from backend.presentation.controllers.menu_planner_controller import MenuPlannerController
from backend.presentation.controllers.product_controller import ProductController
from backend.presentation.controllers.recipe_controller import RecipeController
from backend.presentation.controllers.settings_controller import SettingsController
from backend.presentation.controllers.shopping_list_controller import ShoppingListController
from backend.presentation.views.menu_planner_view import MenuPlannerView
from backend.presentation.views.product_list_view import ProductListView
from backend.presentation.views.recipe_list_view import RecipeListView
from backend.presentation.views.settings_view import SettingsView
from backend.presentation.views.shopping_list_view import ShoppingListView

if TYPE_CHECKING:
    from backend.composition_root import ApplicationContainer


class MainWindow(QMainWindow):
    """Главное окно приложения. Содержит 5 вкладок."""

    def __init__(self, container: ApplicationContainer) -> None:
        super().__init__()
        self.setWindowTitle("Menutor")
        self.showMaximized()

        # --- Views ---
        self._menu_view = MenuPlannerView()
        self._shopping_view = ShoppingListView()
        self._recipe_view = RecipeListView()
        self._product_view = ProductListView()
        self._settings_view = SettingsView()

        # --- Controllers ---
        self._product_ctrl = ProductController(
            view=self._product_view,
            create_uc=container.create_product,
            edit_uc=container.edit_product,
            delete_uc=container.delete_product,
            list_uc=container.list_products,
            list_categories_uc=container.list_product_categories,
        )

        self._recipe_ctrl = RecipeController(
            view=self._recipe_view,
            create_uc=container.create_recipe,
            edit_uc=container.edit_recipe,
            delete_uc=container.delete_recipe,
            list_uc=container.list_recipes,
            list_products_uc=container.list_products,
            list_categories_uc=container.list_recipe_categories,
        )

        self._shopping_ctrl = ShoppingListController(
            view=self._shopping_view,
            export_text_uc=container.export_shopping_list_as_text,
            export_csv_uc=container.export_shopping_list_as_csv,
            list_products_uc=container.list_products,
            list_product_categories_uc=container.list_product_categories,
        )

        self._settings_ctrl = SettingsController(
            view=self._settings_view,
            create_member_uc=container.create_family_member,
            edit_member_uc=container.edit_family_member,
            delete_member_uc=container.delete_family_member,
            list_members_uc=container.list_family_members,
            list_product_categories_uc=container.list_all_product_categories,
            create_product_category_uc=container.create_product_category,
            edit_product_category_uc=container.edit_product_category,
            delete_product_category_uc=container.delete_product_category,
            hard_delete_product_category_uc=container.hard_delete_product_category,
            activate_product_category_uc=container.activate_product_category,
            check_product_category_used_uc=container.check_product_category_used,
            list_recipe_categories_uc=container.list_all_recipe_categories,
            create_recipe_category_uc=container.create_recipe_category,
            edit_recipe_category_uc=container.edit_recipe_category,
            delete_recipe_category_uc=container.delete_recipe_category,
            hard_delete_recipe_category_uc=container.hard_delete_recipe_category,
            activate_recipe_category_uc=container.activate_recipe_category,
            check_recipe_category_used_uc=container.check_recipe_category_used,
        )

        self._menu_ctrl = MenuPlannerController(
            view=self._menu_view,
            create_menu_uc=container.create_menu,
            save_menu_uc=container.save_menu,
            load_menu_uc=container.load_menu,
            delete_menu_uc=container.delete_menu,
            list_menus_uc=container.list_menus,
            add_dish_uc=container.add_dish_to_slot,
            remove_item_uc=container.remove_item_from_slot,
            clear_menu_uc=container.clear_menu,
            list_recipes_uc=container.list_recipes,
            list_products_uc=container.list_products,
            list_family_uc=container.list_family_members,
            generate_shopping_list_uc=container.generate_shopping_list,
            on_shopping_list_generated=self._on_shopping_list_generated,
        )

        # --- Cross-controller signals: update menu grid when data changes ---
        self._recipe_ctrl.data_changed.connect(self._menu_ctrl.refresh_names)
        self._product_ctrl.data_changed.connect(self._menu_ctrl.refresh_names)

        # --- Tab widget ---
        tabs = QTabWidget()
        tabs.addTab(self._menu_view, "Планировщик")
        tabs.addTab(self._shopping_view, "Список покупок")
        tabs.addTab(self._recipe_view, "Рецепты")
        tabs.addTab(self._product_view, "Продукты")
        tabs.addTab(self._settings_view, "Настройки")

        # Refresh recipe/product views when switching tabs (data may have changed)
        tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(tabs)
        self._tabs = tabs

    def _on_shopping_list_generated(self, shopping_list) -> None:
        self._shopping_ctrl.set_shopping_list(shopping_list)
        # Switch to shopping list tab
        self._tabs.setCurrentIndex(1)

    def _on_tab_changed(self, index: int) -> None:
        # index 0 = Planner, 1 = Shopping list, 2 = Recipes, 3 = Products, 4 = Settings
        if index == 1:
            self._shopping_ctrl.refresh()
        elif index == 0:
            self._menu_ctrl.refresh()
        elif index == 2:
            self._recipe_ctrl.refresh()
        elif index == 3:
            self._product_ctrl.refresh()
        elif index == 4:
            self._settings_ctrl.refresh()
