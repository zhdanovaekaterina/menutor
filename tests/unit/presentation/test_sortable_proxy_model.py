"""Tests for SortableProxyModel — numeric and alphabetic sorting."""

from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import (
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)
from backend.presentation.models.product_table_model import ProductTableModel
from backend.presentation.models.recipe_table_model import RecipeTableModel
from backend.presentation.models.sortable_proxy_model import SortableProxyModel


def _product(id: int, name: str, price: str = "10.00") -> Product:
    return Product(
        id=ProductId(id),
        name=name,
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal(price)),
        conversion_factor=1000,
        category_id=ProductCategoryId(1),
    )


def _recipe(id: int, name: str, servings: int = 4, weight: int = 0) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name=name,
        servings=servings,
        category_id=RecipeCategoryId(1),
        weight=weight,
    )


class TestSortableProxyModelProducts:
    def test_sort_by_name_ascending(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1, "Сахар"), _product(2, "Мука"), _product(3, "Соль")])
        proxy = SortableProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(0, Qt.SortOrder.AscendingOrder)
        assert proxy.data(proxy.index(0, 0)) == "Мука"
        assert proxy.data(proxy.index(1, 0)) == "Сахар"
        assert proxy.data(proxy.index(2, 0)) == "Соль"

    def test_sort_by_name_descending(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([_product(1, "Мука"), _product(2, "Сахар")])
        proxy = SortableProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(0, Qt.SortOrder.DescendingOrder)
        assert proxy.data(proxy.index(0, 0)) == "Сахар"

    def test_sort_by_price_numeric(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        model.set_products([
            _product(1, "А", price="100.00"),
            _product(2, "Б", price="9.00"),
            _product(3, "В", price="50.00"),
        ])
        proxy = SortableProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(6, Qt.SortOrder.AscendingOrder)
        assert proxy.data(proxy.index(0, 6)) == "9.00"
        assert proxy.data(proxy.index(1, 6)) == "50.00"
        assert proxy.data(proxy.index(2, 6)) == "100.00"

    def test_source_model_unchanged_after_sort(self, qapp: QApplication) -> None:
        model = ProductTableModel()
        products = [_product(1, "Сахар"), _product(2, "Мука")]
        model.set_products(products)
        proxy = SortableProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(0, Qt.SortOrder.AscendingOrder)
        # Source model row order is unchanged
        assert model.product_at(0).name == "Сахар"  # type: ignore[union-attr]
        assert model.product_at(1).name == "Мука"  # type: ignore[union-attr]


class TestSortableProxyModelRecipes:
    def test_sort_by_name_ascending(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([_recipe(1, "Суп"), _recipe(2, "Каша"), _recipe(3, "Блины")])
        proxy = SortableProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(0, Qt.SortOrder.AscendingOrder)
        assert proxy.data(proxy.index(0, 0)) == "Блины"
        assert proxy.data(proxy.index(1, 0)) == "Каша"
        assert proxy.data(proxy.index(2, 0)) == "Суп"

    def test_sort_by_servings_numeric(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([
            _recipe(1, "А", servings=10),
            _recipe(2, "Б", servings=2),
            _recipe(3, "В", servings=6),
        ])
        proxy = SortableProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(2, Qt.SortOrder.AscendingOrder)
        assert proxy.data(proxy.index(0, 2)) == "2"
        assert proxy.data(proxy.index(1, 2)) == "6"
        assert proxy.data(proxy.index(2, 2)) == "10"

    def test_sort_by_weight_numeric(self, qapp: QApplication) -> None:
        model = RecipeTableModel()
        model.set_recipes([
            _recipe(1, "А", weight=500),
            _recipe(2, "Б", weight=100),
            _recipe(3, "В", weight=0),
        ])
        proxy = SortableProxyModel()
        proxy.setSourceModel(model)
        proxy.sort(3, Qt.SortOrder.AscendingOrder)
        # weight=0 displays as "" — sorts before numbers
        assert proxy.data(proxy.index(1, 3)) == "100"
        assert proxy.data(proxy.index(2, 3)) == "500"
