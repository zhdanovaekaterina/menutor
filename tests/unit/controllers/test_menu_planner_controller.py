"""Unit tests for MenuPlannerController — menu CRUD, slot updates, shopping list generation."""

from decimal import Decimal
from unittest.mock import MagicMock, call

import pytest

from src.domain.entities.family_member import FamilyMember
from src.domain.entities.menu import MenuSlot, WeeklyMenu
from src.domain.entities.product import Product
from src.domain.entities.recipe import Recipe
from src.domain.entities.shopping_list import ShoppingList
from src.domain.value_objects.money import Money
from src.domain.value_objects.types import (
    FamilyMemberId,
    MenuId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)
from src.presentation.controllers.menu_planner_controller import MenuPlannerController


@pytest.fixture
def view() -> MagicMock:
    return MagicMock()


@pytest.fixture
def create_menu_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def save_menu_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def load_menu_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def delete_menu_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_menus_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def add_dish_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def remove_item_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def clear_menu_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_recipes_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_products_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_family_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def generate_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_menus() -> list[WeeklyMenu]:
    return [WeeklyMenu(id=MenuId(1), name="Неделя 1")]


@pytest.fixture
def sample_recipes() -> list[Recipe]:
    return [Recipe(id=RecipeId(1), name="Блины", servings=4, category_id=RecipeCategoryId(1))]


@pytest.fixture
def sample_products() -> list[Product]:
    return [
        Product(
            id=ProductId(1), name="Мука",
            recipe_unit="g", purchase_unit="kg",
            price_per_purchase_unit=Money(Decimal("80")),
            category_id=ProductCategoryId(1),
        ),
    ]


@pytest.fixture
def sample_members() -> list[FamilyMember]:
    return [FamilyMember(id=FamilyMemberId(1), name="Папа")]


@pytest.fixture
def on_shopping_list_generated() -> MagicMock:
    return MagicMock()


@pytest.fixture
def controller(
    view: MagicMock,
    create_menu_uc: MagicMock,
    save_menu_uc: MagicMock,
    load_menu_uc: MagicMock,
    delete_menu_uc: MagicMock,
    list_menus_uc: MagicMock,
    add_dish_uc: MagicMock,
    remove_item_uc: MagicMock,
    clear_menu_uc: MagicMock,
    list_recipes_uc: MagicMock,
    list_products_uc: MagicMock,
    list_family_uc: MagicMock,
    generate_uc: MagicMock,
    on_shopping_list_generated: MagicMock,
    sample_menus: list[WeeklyMenu],
    sample_recipes: list[Recipe],
    sample_products: list[Product],
    sample_members: list[FamilyMember],
) -> MenuPlannerController:
    list_menus_uc.execute.return_value = sample_menus
    list_recipes_uc.execute.return_value = sample_recipes
    list_products_uc.execute.return_value = sample_products
    list_family_uc.execute.return_value = sample_members
    return MenuPlannerController(
        view=view,
        create_menu_uc=create_menu_uc,
        save_menu_uc=save_menu_uc,
        load_menu_uc=load_menu_uc,
        delete_menu_uc=delete_menu_uc,
        list_menus_uc=list_menus_uc,
        add_dish_uc=add_dish_uc,
        remove_item_uc=remove_item_uc,
        clear_menu_uc=clear_menu_uc,
        list_recipes_uc=list_recipes_uc,
        list_products_uc=list_products_uc,
        list_family_uc=list_family_uc,
        generate_shopping_list_uc=generate_uc,
        on_shopping_list_generated=on_shopping_list_generated,
    )


class TestMenuPlannerControllerInit:
    def test_connects_signals(self, view: MagicMock, controller: MenuPlannerController) -> None:
        view.menu_selected.connect.assert_called_once()
        view.slot_updated.connect.assert_called_once()
        view.save_menu_requested.connect.assert_called_once()
        view.clear_menu_requested.connect.assert_called_once()
        view.generate_shopping_list_requested.connect.assert_called_once()
        view.delete_menu_requested.connect.assert_called_once()
        view.new_menu_requested.connect.assert_called_once()

    def test_sets_view_data_on_init(
        self,
        view: MagicMock,
        sample_menus: list[WeeklyMenu],
        sample_recipes: list[Recipe],
        sample_products: list[Product],
        sample_members: list[FamilyMember],
        controller: MenuPlannerController,
    ) -> None:
        view.set_menus.assert_called_once_with(sample_menus)
        view.set_recipes.assert_called_once_with(sample_recipes)
        view.set_products.assert_called_once_with(sample_products)
        view.set_family_members.assert_called_once_with(sample_members)


class TestMenuPlannerControllerMenuSelection:
    def test_load_menu_with_recipe_slots(
        self,
        load_menu_uc: MagicMock,
        view: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        menu = WeeklyMenu(
            id=MenuId(1), name="Неделя 1",
            slots=[
                MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(1), servings_override=2.0),
            ],
        )
        load_menu_uc.execute.return_value = menu
        controller._on_menu_selected(1)
        view.set_current_menu.assert_called_with(menu)
        view.add_grid_slot_item.assert_called_once_with(
            0, "Завтрак", "recipe", RecipeId(1), "Блины", servings=2.0,
        )

    def test_load_menu_with_product_slots(
        self,
        load_menu_uc: MagicMock,
        view: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        menu = WeeklyMenu(
            id=MenuId(1), name="Неделя 1",
            slots=[
                MenuSlot(day=1, meal_type="Обед", product_id=ProductId(1), quantity=200.0, unit="g"),
            ],
        )
        load_menu_uc.execute.return_value = menu
        controller._on_menu_selected(1)
        view.add_grid_slot_item.assert_called_once_with(
            1, "Обед", "product", ProductId(1), "Мука", quantity=200.0, unit="g",
        )

    def test_load_menu_error(
        self,
        load_menu_uc: MagicMock,
        view: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        load_menu_uc.execute.side_effect = ValueError("Меню не найдено")
        controller._on_menu_selected(99)
        view.show_error.assert_called_once_with("Меню не найдено")


class TestMenuPlannerControllerSlotUpdate:
    def test_slot_update_without_menu_shows_info(
        self, view: MagicMock, controller: MenuPlannerController,
    ) -> None:
        controller._on_slot_updated(0, "Завтрак", "recipe", 1, 2.0, "")
        view.show_info.assert_called_once_with("Сначала создайте или выберите меню.")

    def test_slot_update_adds_recipe(
        self,
        add_dish_uc: MagicMock,
        load_menu_uc: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        menu = WeeklyMenu(id=MenuId(1), name="W1")
        load_menu_uc.execute.return_value = menu
        controller._on_menu_selected(1)

        add_dish_uc.execute.return_value = menu
        controller._on_slot_updated(0, "Завтрак", "recipe", 1, 2.0, "")
        add_dish_uc.execute.assert_called_once()
        slot_arg = add_dish_uc.execute.call_args[0][1]
        assert slot_arg.recipe_id == RecipeId(1)
        assert slot_arg.servings_override == 2.0

    def test_slot_update_removes_on_zero_servings(
        self,
        remove_item_uc: MagicMock,
        load_menu_uc: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        menu = WeeklyMenu(id=MenuId(1), name="W1")
        load_menu_uc.execute.return_value = menu
        controller._on_menu_selected(1)

        remove_item_uc.execute.return_value = menu
        controller._on_slot_updated(0, "Завтрак", "recipe", 1, 0.0, "")
        remove_item_uc.execute.assert_called_once()


class TestMenuPlannerControllerNewMenu:
    def test_new_menu_creates_and_refreshes(
        self,
        create_menu_uc: MagicMock,
        list_menus_uc: MagicMock,
        view: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        new_menu = WeeklyMenu(id=MenuId(2), name="Неделя 2")
        create_menu_uc.execute.return_value = new_menu
        list_menus_uc.execute.reset_mock()
        controller._on_new_menu("Неделя 2")
        create_menu_uc.execute.assert_called_once_with("Неделя 2")
        view.set_current_menu.assert_called_with(new_menu)

    def test_new_menu_error(
        self,
        create_menu_uc: MagicMock,
        view: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        create_menu_uc.execute.side_effect = RuntimeError("DB full")
        controller._on_new_menu("X")
        view.show_error.assert_called_once_with("DB full")


class TestMenuPlannerControllerDeleteMenu:
    def test_delete_menu_clears_current(
        self,
        delete_menu_uc: MagicMock,
        list_menus_uc: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        list_menus_uc.execute.reset_mock()
        controller._on_delete_menu(1)
        delete_menu_uc.execute.assert_called_once_with(MenuId(1))
        list_menus_uc.execute.assert_called_once()


class TestMenuPlannerControllerClearMenu:
    def test_clear_without_menu_shows_info(
        self, view: MagicMock, controller: MenuPlannerController,
    ) -> None:
        controller._on_clear_menu()
        view.show_info.assert_called_once_with("Нет активного меню для очистки.")

    def test_clear_delegates_to_use_case(
        self,
        clear_menu_uc: MagicMock,
        load_menu_uc: MagicMock,
        view: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        menu = WeeklyMenu(id=MenuId(1), name="W1")
        load_menu_uc.execute.return_value = menu
        controller._on_menu_selected(1)

        cleared = WeeklyMenu(id=MenuId(1), name="W1", slots=[])
        clear_menu_uc.execute.return_value = cleared
        controller._on_clear_menu()
        clear_menu_uc.execute.assert_called_once_with(MenuId(1))
        view.set_current_menu.assert_called_with(cleared)


class TestMenuPlannerControllerGenerate:
    def test_generate_without_menu_shows_info(
        self, view: MagicMock, controller: MenuPlannerController,
    ) -> None:
        controller._on_generate()
        view.show_info.assert_called_once_with("Сначала выберите или сохраните меню.")

    def test_generate_calls_callback(
        self,
        generate_uc: MagicMock,
        load_menu_uc: MagicMock,
        on_shopping_list_generated: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        menu = WeeklyMenu(id=MenuId(1), name="W1")
        load_menu_uc.execute.return_value = menu
        controller._on_menu_selected(1)

        sl = ShoppingList()
        generate_uc.execute.return_value = sl
        controller._on_generate()
        generate_uc.execute.assert_called_once_with(MenuId(1))
        on_shopping_list_generated.assert_called_once_with(sl)

    def test_generate_error(
        self,
        generate_uc: MagicMock,
        load_menu_uc: MagicMock,
        view: MagicMock,
        controller: MenuPlannerController,
    ) -> None:
        menu = WeeklyMenu(id=MenuId(1), name="W1")
        load_menu_uc.execute.return_value = menu
        controller._on_menu_selected(1)

        generate_uc.execute.side_effect = ValueError("Пустое меню")
        controller._on_generate()
        view.show_error.assert_called_once_with("Пустое меню")
