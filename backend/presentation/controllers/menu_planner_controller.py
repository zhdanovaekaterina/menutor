import logging
from typing import Callable, cast

from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.application.use_cases.manage_family import ListFamilyMembers
from backend.application.use_cases.manage_product import ListProducts
from backend.application.use_cases.manage_recipe import ListRecipes
from backend.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
    RemoveItemFromSlot,
    SaveMenu,
)
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.shopping_list import ShoppingList
from backend.domain.exceptions import AppError
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId
from backend.presentation.views.menu_planner_view import MenuPlannerView

logger = logging.getLogger(__name__)


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
        remove_item_uc: RemoveItemFromSlot,
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
        self._remove_item_uc = remove_item_uc
        self._clear_menu_uc = clear_menu_uc
        self._list_recipes_uc = list_recipes_uc
        self._list_products_uc = list_products_uc
        self._list_family_uc = list_family_uc
        self._generate_uc = generate_shopping_list_uc
        self._on_shopping_list_generated = on_shopping_list_generated

        self._current_menu: WeeklyMenu | None = None
        self._recipe_map: dict[object, str] = {}  # recipe_id -> name
        self._product_map: dict[object, str] = {}  # product_id -> name

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

    def refresh_names(self) -> None:
        """Обновить имена рецептов/продуктов в сетке без перезагрузки меню."""
        try:
            recipes = self._list_recipes_uc.execute()
            new_recipe_map = {r.id: r.name for r in recipes}
            for rid, new_name in new_recipe_map.items():
                if self._recipe_map.get(rid) != new_name:
                    self._view.update_item_name("recipe", rid, new_name)
            self._recipe_map = new_recipe_map
            self._view.set_recipes(recipes)

            products = self._list_products_uc.execute()
            new_product_map = {p.id: p.name for p in products}
            for pid, new_name in new_product_map.items():
                if self._product_map.get(pid) != new_name:
                    self._view.update_item_name("product", pid, new_name)
            self._product_map = new_product_map
            self._view.set_products(products)
        except AppError as exc:
            logger.warning("Ошибка при обновлении имён: %s", exc)

    def _refresh(self) -> None:
        try:
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)

            recipes = self._list_recipes_uc.execute()
            self._recipe_map = {r.id: r.name for r in recipes}
            self._view.set_recipes(recipes)

            products = self._list_products_uc.execute()
            self._product_map = {p.id: p.name for p in products}
            self._view.set_products(products)

            members = self._list_family_uc.execute()
            self._view.set_family_members(members)
        except AppError as exc:
            logger.warning("Ошибка при загрузке данных меню: %s", exc)
            self._view.show_error(str(exc))

    def _on_menu_selected(self, menu_id: object) -> None:
        try:
            menu = self._load_menu_uc.execute(MenuId(cast(int, menu_id)))
            self._current_menu = menu
            self._view.set_current_menu(menu)
            if menu:
                for slot in menu.slots:
                    if slot.recipe_id is not None:
                        name = self._recipe_map.get(slot.recipe_id, f"#{slot.recipe_id}")
                        servings = slot.servings_override if slot.servings_override is not None else 1.0
                        self._view.add_grid_slot_item(
                            slot.day, slot.meal_type, "recipe", slot.recipe_id, name,
                            servings=servings,
                        )
                    elif slot.product_id is not None:
                        name = self._product_map.get(slot.product_id, f"#{slot.product_id}")
                        self._view.add_grid_slot_item(
                            slot.day, slot.meal_type, "product", slot.product_id, name,
                            quantity=slot.quantity or 0.0,
                            unit=slot.unit or "",
                        )
        except AppError as exc:
            logger.warning("Ошибка при загрузке меню %s: %s", menu_id, exc)
            self._view.show_error(str(exc))

    def _on_slot_updated(
        self, day: int, meal_type: str, item_type: str, item_id: int,
        servings_or_qty: float, unit: str,
    ) -> None:
        if self._current_menu is None:
            self._view.show_info("Сначала создайте или выберите меню.")
            return
        try:
            if servings_or_qty == 0.0:
                # Removal
                self._current_menu = self._remove_item_uc.execute(
                    self._current_menu.id, day, meal_type,
                    recipe_id=RecipeId(item_id) if item_type == "recipe" else None,
                    product_id=ProductId(item_id) if item_type == "product" else None,
                )
            else:
                if item_type == "recipe":
                    slot = MenuSlot(
                        day=day,
                        meal_type=meal_type,
                        recipe_id=RecipeId(item_id),
                        servings_override=servings_or_qty if servings_or_qty > 0 else None,
                    )
                else:
                    slot = MenuSlot(
                        day=day,
                        meal_type=meal_type,
                        product_id=ProductId(item_id),
                        quantity=servings_or_qty,
                        unit=unit,
                    )
                self._current_menu = self._add_dish_uc.execute(
                    self._current_menu.id, slot
                )
        except AppError as exc:
            logger.warning("Ошибка при обновлении слота: %s", exc)
            self._view.show_error(str(exc))

    def _on_save_menu(self, name: str) -> None:
        try:
            if self._current_menu is None:
                if not name:
                    return
                self._current_menu = self._create_menu_uc.execute(name)
                # Re-add all current grid slots
                for slot_data in self._view.get_grid_slots():
                    if slot_data["type"] == "recipe":
                        slot = MenuSlot(
                            day=slot_data["day"],
                            meal_type=slot_data["meal_type"],
                            recipe_id=RecipeId(cast(int, slot_data["id"])),
                            servings_override=slot_data["servings"] if slot_data["servings"] > 0 else None,
                        )
                    else:
                        slot = MenuSlot(
                            day=slot_data["day"],
                            meal_type=slot_data["meal_type"],
                            product_id=ProductId(cast(int, slot_data["id"])),
                            quantity=slot_data["quantity"],
                            unit=slot_data["unit"],
                        )
                    self._current_menu = self._add_dish_uc.execute(
                        self._current_menu.id, slot
                    )
            else:
                self._current_menu = self._save_menu_uc.execute(self._current_menu)
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)
        except AppError as exc:
            logger.warning("Ошибка при сохранении меню: %s", exc)
            self._view.show_error(str(exc))

    def _on_clear_menu(self) -> None:
        if self._current_menu is None:
            self._view.show_info("Нет активного меню для очистки.")
            return
        try:
            self._current_menu = self._clear_menu_uc.execute(self._current_menu.id)
            self._view.set_current_menu(self._current_menu)
        except AppError as exc:
            logger.warning("Ошибка при очистке меню: %s", exc)
            self._view.show_error(str(exc))

    def _on_delete_menu(self, menu_id: object) -> None:
        try:
            self._delete_menu_uc.execute(MenuId(cast(int, menu_id)))
            self._current_menu = None
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)
        except AppError as exc:
            logger.warning("Ошибка при удалении меню %s: %s", menu_id, exc)
            self._view.show_error(str(exc))

    def _on_new_menu(self, name: str) -> None:
        try:
            menu = self._create_menu_uc.execute(name)
            self._current_menu = menu
            self._view.set_current_menu(menu)
            menus = self._list_menus_uc.execute()
            self._view.set_menus(menus)
        except AppError as exc:
            logger.warning("Ошибка при создании меню: %s", exc)
            self._view.show_error(str(exc))

    def _on_generate(self) -> None:
        if self._current_menu is None:
            self._view.show_info("Сначала выберите или сохраните меню.")
            return
        try:
            shopping_list = self._generate_uc.execute(self._current_menu.id)
            if self._on_shopping_list_generated:
                self._on_shopping_list_generated(shopping_list)
        except AppError as exc:
            logger.warning("Ошибка при генерации списка покупок: %s", exc)
            self._view.show_error(str(exc))
