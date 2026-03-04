from typing import Callable, cast

from src.application.use_cases.generate_shopping_list import GenerateShoppingList
from src.application.use_cases.manage_family import ListFamilyMembers
from src.application.use_cases.manage_product import ListProducts
from src.application.use_cases.manage_recipe import ListRecipes
from src.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
    RemoveDishFromSlot,
    SaveMenu,
)
from src.domain.entities.menu import MenuSlot, WeeklyMenu
from src.domain.entities.shopping_list import ShoppingList
from src.domain.value_objects.types import MenuId, RecipeId
from src.presentation.views.menu_planner_view import MenuPlannerView


class MenuPlannerController:
    """Соединяет MenuPlannerView с use cases и обрабатывает состояние текущего меню."""

    def __init__(
        self,
        view: MenuPlannerView,
        create_menu_uc: CreateMenu,
        save_menu_uc: SaveMenu,
        load_menu_uc: LoadMenu,
        delete_menu_uc: DeleteMenu,
        list_menus_uc: ListMenus,
        add_dish_uc: AddDishToSlot,
        remove_dish_uc: RemoveDishFromSlot,
        clear_menu_uc: ClearMenu,
        list_recipes_uc: ListRecipes,
        list_products_uc: ListProducts,
        list_family_uc: ListFamilyMembers,
        generate_shopping_list_uc: GenerateShoppingList,
        on_shopping_list_generated: Callable[[ShoppingList], None] | None = None,
    ) -> None:
        self._view = view
        self._create_menu_uc = create_menu_uc
        self._save_menu_uc = save_menu_uc
        self._load_menu_uc = load_menu_uc
        self._delete_menu_uc = delete_menu_uc
        self._list_menus_uc = list_menus_uc
        self._add_dish_uc = add_dish_uc
        self._remove_dish_uc = remove_dish_uc
        self._clear_menu_uc = clear_menu_uc
        self._list_recipes_uc = list_recipes_uc
        self._list_products_uc = list_products_uc
        self._list_family_uc = list_family_uc
        self._generate_uc = generate_shopping_list_uc
        self._on_shopping_list_generated = on_shopping_list_generated

        self._current_menu: WeeklyMenu | None = None
        self._recipe_map: dict[object, str] = {}  # recipe_id -> name

        view.menu_selected.connect(self._on_menu_selected)
        view.slot_updated.connect(self._on_slot_updated)
        view.save_menu_requested.connect(self._on_save_menu)
        view.clear_menu_requested.connect(self._on_clear_menu)
        view.generate_shopping_list_requested.connect(self._on_generate)
        view.delete_menu_requested.connect(self._on_delete_menu)
        view.new_menu_requested.connect(self._on_new_menu)

        self._refresh()

    def refresh(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        try:
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)

            recipes = self._list_recipes_uc.execute()
            self._recipe_map = {r.id: r.name for r in recipes}
            self._view.set_recipes(recipes)

            products = self._list_products_uc.execute()
            self._view.set_products(products)

            members = self._list_family_uc.execute()
            self._view.set_family_members(members)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_menu_selected(self, menu_id: object) -> None:
        try:
            menu = self._load_menu_uc.execute(MenuId(cast(int, menu_id)))
            self._current_menu = menu
            self._view.set_current_menu(menu)
            if menu:
                for slot in menu.slots:
                    name = self._recipe_map.get(slot.recipe_id, f"#{slot.recipe_id}")
                    servings = slot.servings_override if slot.servings_override is not None else 1.0
                    self._view.set_grid_slot(slot.day, slot.meal_type, slot.recipe_id, name, servings)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_slot_updated(
        self, day: int, meal_type: str, recipe_id: object, servings: float
    ) -> None:
        if self._current_menu is None:
            self._view.show_info("Сначала создайте или выберите меню.")
            return
        try:
            if recipe_id is None:
                self._current_menu = self._remove_dish_uc.execute(
                    self._current_menu.id, day, meal_type
                )
            else:
                slot = MenuSlot(
                    day=day,
                    meal_type=meal_type,
                    recipe_id=RecipeId(cast(int, recipe_id)),
                    servings_override=servings if servings > 0 else None,
                )
                self._current_menu = self._add_dish_uc.execute(
                    self._current_menu.id, slot
                )
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_save_menu(self, name: str) -> None:
        try:
            if self._current_menu is None:
                if not name:
                    return
                self._current_menu = self._create_menu_uc.execute(name)
                # Re-add all current grid slots
                for day, meal_type, recipe_id, servings in self._view.get_grid_slots():
                    slot = MenuSlot(
                        day=day,
                        meal_type=meal_type,
                        recipe_id=RecipeId(cast(int, recipe_id)),
                        servings_override=servings if servings > 0 else None,
                    )
                    self._current_menu = self._add_dish_uc.execute(
                        self._current_menu.id, slot
                    )
            else:
                self._current_menu = self._save_menu_uc.execute(self._current_menu)
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_clear_menu(self) -> None:
        if self._current_menu is None:
            self._view.show_info("Нет активного меню для очистки.")
            return
        try:
            self._current_menu = self._clear_menu_uc.execute(self._current_menu.id)
            self._view.set_current_menu(self._current_menu)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_delete_menu(self, menu_id: object) -> None:
        try:
            self._delete_menu_uc.execute(MenuId(cast(int, menu_id)))
            self._current_menu = None
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_new_menu(self, name: str) -> None:
        try:
            menu = self._create_menu_uc.execute(name)
            self._current_menu = menu
            self._view.set_current_menu(menu)
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_generate(self) -> None:
        if self._current_menu is None:
            self._view.show_info("Сначала выберите или сохраните меню.")
            return
        try:
            shopping_list = self._generate_uc.execute(self._current_menu.id)
            if self._on_shopping_list_generated:
                self._on_shopping_list_generated(shopping_list)
        except Exception as exc:
            self._view.show_error(str(exc))
