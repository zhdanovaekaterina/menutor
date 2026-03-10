"""Tests for ProductTableModel and RecipeTableModel — display, filtering, item access."""

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.domain.entities.product import Product
from src.domain.entities.recipe import Recipe
from src.domain.value_objects.money import Money
from src.domain.value_objects.types import (
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)
from src.presentation.models.product_table_model import ProductTableModel
from src.presentation.models.recipe_table_model import RecipeTableModel


def _product(id: int = 1, name: str = "Мука", category_id: int = 1) -> Product:
    return Product(
        id=ProductId(id),
        name=name,
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80.50")),
        brand="Макфа",
        supplier="Магнит",
        conversion_factor=1000,
        category_id=ProductCategoryId(category_id),
    )


def _recipe(id: int = 1, name: str = "Блины", servings: int = 4, weight: int = 300) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name=name,
        servings=servings,
        category_id=RecipeCategoryId(1),
        weight=weight,
    )


# ---- ProductTableModel ----


class TestProductTableModel:
    def test_columns(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        assert model.columnCount() == 7

    def test_header_data(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        assert model.headerData(0, Qt.Orientation.Horizontal) == "Название"
        assert model.headerData(6, Qt.Orientation.Horizontal) == "Цена, руб."

    def test_header_vertical_returns_none(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        assert model.headerData(0, Qt.Orientation.Vertical) is None

    def test_empty_model_has_zero_rows(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        assert model.rowCount() == 0

    def test_set_products(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1), _product(2, name="Сахар")])
        assert model.rowCount() == 2

    def test_display_name(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 0)
        assert model.data(idx) == "Мука"

    def test_display_category_with_map(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_category_map({1: "Бакалея"})
        model.set_products([_product()])
        idx = model.index(0, 1)
        assert model.data(idx) == "Бакалея"

    def test_display_category_missing_in_map(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 1)
        assert model.data(idx) == ""

    def test_display_brand(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 2)
        assert model.data(idx) == "Макфа"

    def test_display_supplier(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 3)
        assert model.data(idx) == "Магнит"

    def test_display_recipe_unit_translated(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 4)
        assert model.data(idx) == "г"

    def test_display_purchase_unit_translated(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 5)
        assert model.data(idx) == "кг"

    def test_display_price(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 6)
        assert model.data(idx) == "80.50"

    def test_user_role_returns_id(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(42)])
        idx = model.index(0, 0)
        assert model.data(idx, Qt.ItemDataRole.UserRole) == 42

    def test_invalid_index_returns_none(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(5, 0)
        assert model.data(idx) is None

    def test_out_of_range_column_returns_none(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product()])
        idx = model.index(0, 99)
        assert model.data(idx) is None

    def test_product_at_valid(self, qapp: QApplication) -> None:
        p = _product(1)
        model = ProductTableModel()
        model.set_products([p])
        assert model.product_at(0) == p

    def test_product_at_out_of_range(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        assert model.product_at(0) is None
        assert model.product_at(-1) is None

    def test_filter_by_name(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1, "Мука"), _product(2, "Сахар"), _product(3, "Мука рисовая")])
        model.filter("мука")
        assert model.rowCount() == 2

    def test_filter_case_insensitive(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1, "Молоко")])
        model.filter("МОЛОКО")
        assert model.rowCount() == 1

    def test_filter_empty_restores_all(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1), _product(2, "Сахар")])
        model.filter("мука")
        assert model.rowCount() == 1
        model.filter("")
        assert model.rowCount() == 2

    def test_filter_no_match(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1)])
        model.filter("xyz")
        assert model.rowCount() == 0

    def test_set_items_resets_filter(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1), _product(2, "Сахар")])
        model.filter("сахар")
        assert model.rowCount() == 1
        model.set_products([_product(1), _product(2, "Сахар"), _product(3, "Соль")])
        assert model.rowCount() == 3


# ---- RecipeTableModel ----


class TestRecipeTableModel:
    def test_columns(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        assert model.columnCount() == 4

    def test_header_data(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        assert model.headerData(0, Qt.Orientation.Horizontal) == "Название"
        assert model.headerData(2, Qt.Orientation.Horizontal) == "Порций"
        assert model.headerData(3, Qt.Orientation.Horizontal) == "Вес, г"

    def test_empty_model(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        assert model.rowCount() == 0

    def test_set_recipes(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(1), _recipe(2, "Каша")])
        assert model.rowCount() == 2

    def test_display_name(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe()])
        assert model.data(model.index(0, 0)) == "Блины"

    def test_display_category(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_category_map({1: "Завтраки"})
        model.set_recipes([_recipe()])
        assert model.data(model.index(0, 1)) == "Завтраки"

    def test_display_servings(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(servings=6)])
        assert model.data(model.index(0, 2)) == "6"

    def test_display_weight(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(weight=300)])
        assert model.data(model.index(0, 3)) == "300"

    def test_display_weight_zero_returns_empty(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(weight=0)])
        assert model.data(model.index(0, 3)) == ""

    def test_user_role_returns_id(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(id=7)])
        assert model.data(model.index(0, 0), Qt.ItemDataRole.UserRole) == 7

    def test_recipe_at_valid(self, qapp: QApplication) -> None:
        r = _recipe()
        model = RecipeTableModel()
        model.set_recipes([r])
        assert model.recipe_at(0) == r

    def test_recipe_at_out_of_range(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        assert model.recipe_at(0) is None

    def test_filter_by_name(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(1, "Блины"), _recipe(2, "Каша"), _recipe(3, "Блинчики")])
        model.filter("блин")
        assert model.rowCount() == 2

    def test_filter_empty_restores_all(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(1), _recipe(2, "Каша")])
        model.filter("каша")
        assert model.rowCount() == 1
        model.filter("")
        assert model.rowCount() == 2

    def test_decoration_role_returns_none(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe()])
        assert model.data(model.index(0, 0), Qt.ItemDataRole.DecorationRole) is None
